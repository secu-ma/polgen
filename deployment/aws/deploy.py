#!/usr/bin/python3
import argparse
import io
import json
import os
import secrets
import subprocess
import sys
import zipfile

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))


def remove_version_from_function_arn(function_arn):
    return ":".join(function_arn.split(":")[:-1])


def main(session, session_us_east_1, cognito_region, user_pool_id, user_pool_app_id, user_pool_app_secret, user_pool_domain, cloudfront_distribution_id, function_prefix="wiki-"):
    # Lambda@Edge always lives in us-east-1
    lambda_client = session_us_east_1.client('lambda')
    cloudfront_client = session.client('cloudfront')

    # Build the lambda-edge project
    subprocess.run(["npm", "run", "build"], cwd=os.path.join(CURRENT_DIR, 'lambda-edge'), check=True, capture_output=True)

    # Get the current cloudfront config
    result = cloudfront_client.get_distribution_config(
        Id=cloudfront_distribution_id,
    )
    distribution_config = result['DistributionConfig']
    etag = result.pop('ETag')


    # Create the deployment packages for each lambda function
    nonce_signing_secret = secrets.token_urlsafe(64)
    lambda_src_path = os.path.join(CURRENT_DIR, 'lambda-edge', 'src')
    for root, dirs, files in os.walk(lambda_src_path):
        if 'bundle.js' in files:
            relpath = os.path.relpath(root, lambda_src_path)
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
            print("Deploying to lambda...")
            zip_buffer.seek(0)
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
            print("Current config", distribution_config)
            import pprint
            # pprint.pprint(distribution_config)
            cache_behaviors = distribution_config.get('CacheBehaviors', {}).get('Items', [])
            default_cache_behavior = distribution_config['DefaultCacheBehavior']
            pprint.pprint(default_cache_behavior)
            pprint.pprint(cache_behaviors)
            for cache_behavior in cache_behaviors + [default_cache_behavior]:
                for association in cache_behavior["LambdaFunctionAssociations"]["Items"]:
                    if remove_version_from_function_arn(association["LambdaFunctionARN"]) == remove_version_from_function_arn(arn):
                        association["LambdaFunctionARN"] = arn

    print("Deploying to cloudfront...")
    cloudfront_client.update_distribution(
        Id=cloudfront_distribution_id,
        DistributionConfig=distribution_config,
        IfMatch=etag,
    )
    print("Cloudfront distribution updated", cloudfront_distribution_id)
    waiter = cloudfront_client.get_waiter('distribution_deployed')
    waiter.wait(Id=cloudfront_distribution_id)
    print("Cloudfront update done")


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
    parser.add_argument("--function-prefix", default="wiki-")
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
        function_prefix=args.function_prefix
    )
