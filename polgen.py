#!/usr/bin/python3

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import argparse
import contextlib
import hashlib
import json
import logging
import platform
import re
import subprocess
import sys
import tempfile
import time
from typing import Any

try:
    import boto3
    import botocore
except ImportError:
    boto3 = None

logger = logging.getLogger(__name__)


CLOUDFORMATION_INIT_TEMPLATE = """{
  "AWSTemplateFormatVersion": "2010-09-09",
  "Description": "PolGen Wiki Genesis resources: S3 state bucket and user with necessary deployment permissions",
  "Resources": {
    "S3Bucket": {
      "Type": "AWS::S3::Bucket",
      "Properties": {
        "BucketName": {
          "Fn::Sub": "state-%(postfix)s"
        },
        "VersioningConfiguration": {
          "Status": "Enabled"
        },
        "LifecycleConfiguration": {
          "Rules": [
            {
              "Id": "DeleteOldVersions",
              "Status": "Enabled",
              "NoncurrentVersionExpiration": {
                "NoncurrentDays": 90
              }
            }
          ]
        }
      }
    },
    "IAMUser": {
      "Type": "AWS::IAM::User",
      "Properties": {
        "Path": "/",
        "ManagedPolicyArns": [
          "arn:aws:iam::aws:policy/AmazonS3FullAccess",
          "arn:aws:iam::aws:policy/AmazonCognitoPowerUser",
          "arn:aws:iam::aws:policy/CloudFrontFullAccess",
          "arn:aws:iam::aws:policy/AWSLambda_FullAccess",
          "arn:aws:iam::aws:policy/IAMFullAccess"
        ]
      }
    },
    "IAMAccessKey": {
      "Type": "AWS::IAM::AccessKey",
      "Properties": {
        "Status": "Active",
        "UserName": {
          "Ref": "IAMUser"
        }
      }
    }
  },
  "Outputs": {
    "BucketName": {
      "Description": "Name of the created S3 bucket",
      "Value": {
        "Ref": "S3Bucket"
      }
    },
    "AccessKeyID": {
      "Description": "Access Key ID for the created IAM user",
      "Value": {
        "Ref": "IAMAccessKey"
      }
    },
    "SecretAccessKey": {
      "Description": "Secret Access Key for the created IAM user",
      "Value": {
        "Fn::GetAtt": ["IAMAccessKey", "SecretAccessKey"]
      }
    }
  }
}
"""


def os_cmd(cmd: str) -> str:
    if platform.system() == "Windows":
        return f"{cmd}.exe"
    return cmd


def request_confirmation(message: str) -> bool:
    result = input(message + " (y/N) ").strip().lower()
    return result == "yes" or result == "y"


def get_git_repo_name():
    try:
        result = subprocess.run(
            [os_cmd("git"), "remote", "get-url", "origin"],
            check=True,
            capture_output=True,
            text=True,
        )
    except subprocess.CalledProcessError:
        logger.debug("Unable to get git repo name", exc_info=True)
        return ""
    repo_url = result.stdout.strip()
    logger.debug("git repo url: %s", repo_url)
    if ":" in repo_url:
        repo_name = repo_url.split(":")[-1][:-4]
        logger.debug("ssh repo name: %s", repo_name)
    else:
        repo_name = "/".join(repo_url.rsplit("/", 2)[1:])[:-4]
        logger.debug("https repo name: %s", repo_name)
    return repo_name


def get_postfix(unique_seed: str) -> str:
    return hashlib.sha256(unique_seed.encode("utf-8")).hexdigest()[:16]


def is_boto3_available() -> bool:
    return boto3 is not None


def is_aws_cli_available() -> bool:
    try:
        result = subprocess.run(
            [os_cmd("aws"), "--version"], check=True, capture_output=True, text=True
        )
    except subprocess.CalledProcessError:
        return False
    return result.stdout.strip().startswith("aws-cli")


def is_aws_interface_available() -> bool:
    return is_boto3_available() or is_aws_cli_available()


def cli_encode_arg_value(value: Any) -> str:
    if isinstance(value, str):
        return value
    try:
        return ",".join([v for v in value])
    except TypeError:
        return str(value)


@contextlib.contextmanager
def process_special_aws_kwargs(kwargs):
    args = []

    template_body = kwargs.pop("TemplateBody", None)
    template_body_file = None
    if template_body:
        template_body_file = tempfile.NamedTemporaryFile(delete=False)
        # The template body must be passed through a file
        template_body_file.write(template_body.encode("utf-8"))
        template_body_file.flush()
        args.append(f"--template-body=file://{template_body_file.name}")
    try:
        yield args
    finally:
        if template_body_file:
            template_body_file.close()


class AWSCommandError(Exception):
    def __init__(self, message: str, code: str = "", detail: str = ""):
        super().__init__(message)
        self.code = code
        self.detail = detail


def aws_command(service: str, cmd: str, kwargs: dict[str, Any]) -> dict[str, Any]:
    if is_boto3_available():
        client = boto3.client(service)
        try:
            return getattr(client, cmd)(**kwargs)
        except botocore.exceptions.ClientError as e:
            message = f"An error occurred ({e.response['Error']['Code']}) when calling the {e.operation_name} operation: {e.response['Error']['Message']}"
            raise AWSCommandError(
                message, e.response["Error"]["Code"], e.response["Error"]["Message"]
            ) from e
    else:
        pattern = re.compile(r"(?<!^)(?=[A-Z])")

        with process_special_aws_kwargs(kwargs) as args:
            args += [
                f"--{pattern.sub("-", arg).lower()}={cli_encode_arg_value(value)}"
                for arg, value in kwargs.items()
            ]
            cmd = cmd.replace("_", "-")
            try:
                result = subprocess.run(
                    [os_cmd("aws"), service, cmd, *args, "--output=json"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
            except subprocess.CalledProcessError as e:
                error_message = e.stderr.strip()
                if e.returncode == 254 and error_message.startswith(
                    "An error occurred"
                ):
                    error_match = re.match(
                        r"^An error occurred \((.+)\) when calling the \w+ operation: (.*)$",
                        error_message,
                    )
                    if error_match:
                        raise AWSCommandError(
                            error_message, error_match.group(1), error_match.group(2)
                        ) from e
                raise
        return json.loads(result.stdout.strip())


def get_aws_account_id() -> str:
    result = aws_command("sts", "get_caller_identity", {})
    return result["Account"]


def get_bootstrap_stack_name(postfix: str) -> str:
    return f"PolGenBootstrap{postfix}"


def get_bootstrap_stack(postfix: str):
    kwargs = {
        "StackName": get_bootstrap_stack_name(postfix),
    }
    try:
        result = aws_command("cloudformation", "describe_stacks", kwargs)
    except AWSCommandError as e:
        if e.code == "ValidationError":
            return None  # A ValidationError means no stack exists with that name
        raise

    stacks = result.get("Stacks", [])
    if stacks:
        return stacks[0]
    return None


def create_bootstrap_stack(postfix: str, wait_until_created=True):
    kwargs = {
        "StackName": get_bootstrap_stack_name(postfix),
        "TemplateBody": CLOUDFORMATION_INIT_TEMPLATE
        % {
            "postfix": postfix,
        },
        "Capabilities": ["CAPABILITY_IAM"],
    }
    result = aws_command("cloudformation", "create_stack", kwargs)
    if wait_until_created:
        if is_boto3_available():
            waiter = boto3.client("cloudformation").get_waiter("stack_create_complete")
            waiter.wait(StackName=result["StackId"])
        else:
            for i in range(120):
                time.sleep(30)
                logger.debug("Check stack creation")
                stack = get_bootstrap_stack(postfix)
                if stack["StackStatus"] == "CREATE_COMPLETE":
                    break
                if stack["StackStatus"] != "CREATE_IN_PROGRESS":
                    raise Exception(
                        f"Stack {stack['StackId']} creation failed in state {stack['StackStatus']}"
                    )


def update_bootstrap_stack(
    postfix: str, stack: dict[str, Any], wait_until_updated=True
):
    kwargs = {
        "StackName": stack["StackId"],
        "TemplateBody": CLOUDFORMATION_INIT_TEMPLATE
        % {
            "postfix": postfix,
        },
        "Capabilities": ["CAPABILITY_IAM"],
    }
    result = None
    try:
        result = aws_command("cloudformation", "update_stack", kwargs)
    except AWSCommandError as e:
        if e.code != "ValidationError" or not e.detail.startswith(
            "No updates are to be performed"
        ):
            raise
        print("Stack is up to date")

    if result and wait_until_updated:
        if is_boto3_available():
            waiter = boto3.client("cloudformation").get_waiter("stack_update_complete")
            waiter.wait(StackName=result["StackId"])
        else:
            for i in range(120):
                time.sleep(30)
                logger.debug("Check stack update")
                stack = get_bootstrap_stack(postfix)
                if stack["StackStatus"] == "UPDATE_COMPLETE":
                    break
                if stack["StackStatus"] not in {
                    "UPDATE_IN_PROGRESS",
                    "UPDATE_COMPLETE_CLEANUP_IN_PROGRESS",
                }:
                    logger.debug(
                        f"Stack {stack['StackId']} update failed in state {stack['StackStatus']}"
                    )
                    raise Exception(f"Stack {stack['StackId']} update failed")


def get_stack_output(stack: dict[str, Any], name: str) -> str:
    for output in stack["Outputs"]:
        if output["OutputKey"] == name:
            return output["OutputValue"]
    raise KeyError(f"Key {name} not found in Outputs")


def get_aws_region() -> str:
    if is_boto3_available():
        return boto3.session.Session().region_name
    else:
        result = subprocess.run(
            ["aws", "configure", "get", "region"],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()


def init(args):
    # Psuedocode:
    #  1) Use git to get repository name -> derive unique seed
    #  2) Detect if boto3
    #  3) If not, detect if AWS CLI (aws command)
    #  4) Prompt for auto creation of stack
    #  5) Otherwise, let user perform manual creation (print CloudFormation template)
    #  6) Detect if gh cli
    #  7) Detect if necessary permissions on repo to perform automatic actions:
    #    7a) Add repo secrets and variables
    #    7b) Enable Workflows on forked repo
    # 8) Otherwise, print instructions for user to perform it themselves
    repo_name = get_git_repo_name()
    if not repo_name:
        print(
            "Unable to get git repo name. Are you running this in a git cloned repo directory?"
        )
        repo_name = input(
            'Please enter the GitHub repo name in the format "<user/company name>/<repo name>"'
        )
        if len(repo_name.split("/")) != 2:
            print("Not a valid repo name. Aborting...")
            sys.exit(1)
    repo_branch = input("Which branch will you use to deploy? (main) ").strip()
    if not repo_branch:
        repo_branch = "main"
    postfix = get_postfix(f"{repo_name}/{repo_branch}")
    if not is_aws_interface_available():
        print(
            "We cannot interface with AWS. Either install and configure the AWS CLI or install Boto3."
        )
        sys.exit(1)

    if is_aws_interface_available():
        aws_account_id = get_aws_account_id()
        stack = get_bootstrap_stack(postfix)
        if stack:
            print("Bootstrap stack exists.")
            if request_confirmation("Update stack?"):
                print("Updating stack...")
                update_bootstrap_stack(postfix, stack)
            else:
                print("Skipping stack update...")
        else:
            print("Bootstrap stack does not exist.")
            if request_confirmation(
                f"Create a new bootstrap stack in account {aws_account_id}?"
            ):
                print("Creating a new bootstrap stack...")
                create_bootstrap_stack(postfix)

        # Print GitHub instructions
        stack = get_bootstrap_stack(postfix)
        access_key_id = get_stack_output(stack, "AccessKeyID")
        secret_access_key = get_stack_output(stack, "SecretAccessKey")
        print("Create or update the following GitHub \033[1msecret\033[0m:")
        print("")
        print(f"  AWS_SECRET_ACCESS_KEY: {secret_access_key}")
        print("")
        print("Create or update the following GitHub \033[1mvariables\033[0m:")
        print("")
        print(f"  AWS_ACCESS_KEY_ID: {access_key_id}")
        print(f"  AWS_REGION: {get_aws_region()}")
        print("")
    else:
        print(
            "Unable to automatically interface with AWS because neither Boto3 nor the AWS CLI is available."
        )
        print(
            "Use the following CloudFormation template to create or update your stack manually:"
        )
        print(
            CLOUDFORMATION_INIT_TEMPLATE
            % {
                "postfix": postfix,
            }
        )
        print(
            "Then create/update the following GitHub \033[1msecret\033[0m with the Output from the Stack:"
        )
        print("")
        print("  AWS_SECRET_ACCESS_KEY")
        print("")
        print(
            "And also create/update the following GitHub \033[1mvariables\033[0m with the Output from the Stack:"
        )
        print("")
        print("  AWS_ACCESS_KEY_ID")
        print("  AWS_REGION")
        print("")
    print("PolGen init done.")


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers(
        required=True,
        title="commands",
        description="Different commands that can be executed",
    )
    parser_init = subparsers.add_parser(
        "init",
        help="Initialize the GitHub and AWS accounts after having forked the repo",
    )
    parser_init.add_argument("--verbose", "-v", action="store_true")
    parser_init.set_defaults(func=init)

    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.WARNING)
    args.func(args)


if __name__ == "__main__":
    main()
