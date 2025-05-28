#!/usr/bin/python3
import argparse
import datetime
import io
import json
import mimetypes
import os
import secrets
import subprocess
import sys
import zipfile

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def remove_version_from_function_arn(function_arn):
    return ":".join(function_arn.split(":")[:-1])


def get_cloudfront_config(session, cloudfront_distribution_id):
    cloudfront_client = session.client('cloudfront')

    # Get the current cloudfront config
    result = cloudfront_client.get_distribution_config(
        Id=cloudfront_distribution_id,
    )
    distribution_config = result['DistributionConfig']
    etag = result.pop('ETag')
    return distribution_config, etag


def deploy_edge_lambdas(session_us_east_1, cognito_region, user_pool_id, user_pool_app_id, user_pool_app_secret, user_pool_domain, distribution_config, function_prefix="wiki-", lambda_edge_artifact_dir=""):
    # Lambda@Edge always lives in us-east-1
    lambda_client = session_us_east_1.client('lambda')

    if not lambda_edge_artifact_dir:
        # Build the lambda-edge project
        subprocess.run(["npm", "run", "build"], cwd=os.path.join(CURRENT_DIR, 'lambda-edge'), check=True, capture_output=True)
        lambda_edge_artifact_dir = os.path.join(CURRENT_DIR, 'lambda-edge', 'src')

    # Deploy each lambda function (there is currently only one, but multiple is supported)
    nonce_signing_secret = secrets.token_urlsafe(64)
    for root, dirs, files in os.walk(lambda_edge_artifact_dir):
        if 'bundle.js' not in files:
            continue

        relpath = os.path.relpath(root, lambda_edge_artifact_dir)
        bundle_relpath = os.path.join(relpath, 'bundle.js')
        print("Creating deployment package for: ", bundle_relpath)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
            zip_file.write(os.path.join(root, 'bundle.js'), 'bundle.js')
            zip_file.writestr("config.json", json.dumps({
                "region": cognito_region,
                "userPoolId": user_pool_id,
                "userPoolAppId": user_pool_app_id,
                "userPoolAppSecret": user_pool_app_secret,
                "userPoolDomain": user_pool_domain,
                "httpOnly": True,
                "sameSite": "Lax",
                "csrfProtection": {
                    "nonceSigningSecret": nonce_signing_secret,
                },
                "logLevel": "debug",
            }))
        zip_buffer.seek(0)

        print("Deploying to lambda...")
        result = lambda_client.update_function_code(
            FunctionName=f"{function_prefix}{relpath.split('/')[-1]}",
            ZipFile=zip_buffer.read(),
            Publish=True,
        )
        new_version = result["Version"]
        arn = result["FunctionArn"]
        print("New lambda version deployed:", new_version, arn)

        print("Waiting until lambda is active...")
        waiter = lambda_client.get_waiter("function_active_v2")
        waiter.wait(FunctionName=arn)
        print("Function is now active")

        # Updating cloudfront distribution config with updated lambda arn
        cache_behaviors = distribution_config.get('CacheBehaviors', {}).get('Items', [])
        default_cache_behavior = distribution_config['DefaultCacheBehavior']
        for cache_behavior in cache_behaviors + [default_cache_behavior]:
            for association in cache_behavior["LambdaFunctionAssociations"]["Items"]:
                if remove_version_from_function_arn(association["LambdaFunctionARN"]) == remove_version_from_function_arn(arn):
                    association["LambdaFunctionARN"] = arn

    return distribution_config


def get_current_wiki_version(distribution_config):
    origins = distribution_config["Origins"]
    origin_path = origins["Items"][0]["OriginPath"]
    if origin_path.startswith("/"):
        origin_path = origin_path[1:]
    return origin_path


def deploy_s3_wiki(session, s3_bucket, distribution_config, build_path='../../wiki/dist', wiki_artifact_dir=""):
    version_old = get_current_wiki_version(distribution_config)
    version_new = datetime.datetime.now().replace(microsecond=0).isoformat()
    print("Current wiki version:", version_old)

    if not wiki_artifact_dir:
        build_path_abs = os.path.abspath(os.path.join(CURRENT_DIR, build_path))
        # Build Astro wiki
        subprocess.run(["npm", "run", "build"], cwd=os.path.join(build_path_abs, ".."))
        wiki_artifact_dir = build_path_abs

    # Upload build to S3 bucket as new version
    s3 = session.client('s3')
    print(f'Start S3 upload of version {version_new} to {s3_bucket}')
    for root, dirs, files in os.walk(wiki_artifact_dir):
        for filename in files:
            local_path = os.path.join(root, filename)
            relative_path = os.path.relpath(local_path, wiki_artifact_dir)
            s3_path = os.path.join(version_new, relative_path)
            mimetype = mimetypes.guess_type(local_path)[0]
            extra_args = {}
            if mimetype:
                extra_args['ContentType'] = mimetype
            print(f'Uploading {local_path} to {s3_path} with content-type {mimetype}')
            s3.upload_file(
                local_path,
                s3_bucket,
                s3_path,
                ExtraArgs=extra_args
            )

    # Serve new version on cloudfront
    new_path = version_new if version_new.startswith("/") else f"/{version_new}"
    distribution_config["Origins"]["Items"][0]["OriginPath"] = new_path
    return distribution_config


def update_cloudfront(session, cloudfront_distribution_id, distribution_config, etag, wait=True, invalidate=True):
    cloudfront_client = session.client('cloudfront')

    print("Deploying to cloudfront...")
    cloudfront_client.update_distribution(
        Id=cloudfront_distribution_id,
        DistributionConfig=distribution_config,
        IfMatch=etag,
    )
    print("Cloudfront distribution config pushed", cloudfront_distribution_id)
    if wait:
        print("Waiting for cloudfront deployment to finish")
        waiter = cloudfront_client.get_waiter('distribution_deployed')
        waiter.wait(Id=cloudfront_distribution_id)
        print("Cloudfront update done")
    if invalidate:
        print("Invalidating cloudfront distribution cache")
        result = cloudfront_client.create_invalidation(
            DistributionId=cloudfront_distribution_id,
            InvalidationBatch={
                'Paths': {
                    'Quantity': 1,
                    'Items': [
                        "/*"
                    ]
                },
                'CallerReference': datetime.datetime.now().isoformat(),
            }
        )
        waiter = cloudfront_client.get_waiter('invalidation_completed')
        waiter.wait(DistributionId=cloudfront_distribution_id, Id=result['Invalidation']['Id'])
        print("Cloudfront invalidation done")


def main(session, session_us_east_1, cognito_region, user_pool_id, user_pool_app_id, user_pool_app_secret, user_pool_domain, cloudfront_distribution_id, wiki_bucket, function_prefix="wiki-", lambda_edge_artifact_dir="", wiki_artifact_dir=""):
    distribution_config, etag = get_cloudfront_config(session=session, cloudfront_distribution_id=cloudfront_distribution_id)
    distribution_config = deploy_edge_lambdas(
        session_us_east_1=session_us_east_1,
        cognito_region=cognito_region,
        user_pool_id=user_pool_id,
        user_pool_app_id=user_pool_app_id,
        user_pool_app_secret=user_pool_app_secret,
        user_pool_domain=user_pool_domain,
        distribution_config=distribution_config,
        function_prefix=function_prefix,
        lambda_edge_artifact_dir=lambda_edge_artifact_dir,
    )
    distribution_config = deploy_s3_wiki(
        session=session,
        s3_bucket=wiki_bucket,
        distribution_config=distribution_config,
        wiki_artifact_dir=wiki_artifact_dir,
    )
    update_cloudfront(
        session=session,
        cloudfront_distribution_id=cloudfront_distribution_id,
        distribution_config=distribution_config,
        etag=etag,
        wait=True,
        invalidate=False,
    )

if __name__ == "__main__":
    try:
        import boto3
    except ImportError:
        print("Boto3 is required to run this script.", file=sys.stderr)
        sys.exit(1)

    parser = argparse.ArgumentParser()
    parser.add_argument("--cognito-region", required=True)
    parser.add_argument("--user-pool-id", required=True)
    parser.add_argument("--user-pool-domain", required=True)
    parser.add_argument("--user-pool-app-id", required=True)
    parser.add_argument("--user-pool-app-secret", required=True)
    parser.add_argument("--cloudfront-distribution-id", required=True)
    parser.add_argument("--wiki-bucket", required=True)
    parser.add_argument("--function-prefix", default="wiki-")
    parser.add_argument("--wiki-artifact-dir", default="", required=False)
    parser.add_argument("--lambda-edge-artifact-dir", default="", required=False)
    args = parser.parse_args()

    session = boto3.session.Session()
    session_us_east_1 = boto3.session.Session(region_name="us-east-1")
    main(
        session,
        session_us_east_1,
        cognito_region=args.cognito_region,
        user_pool_id=args.user_pool_id,
        user_pool_domain=args.user_pool_domain,
        user_pool_app_id=args.user_pool_app_id,
        user_pool_app_secret=args.user_pool_app_secret,
        cloudfront_distribution_id=args.cloudfront_distribution_id,
        wiki_bucket=args.wiki_bucket,
        function_prefix=args.function_prefix,
        lambda_edge_artifact_dir=args.lambda_edge_artifact_dir,
        wiki_artifact_dir=args.wiki_artifact_dir,
    )
