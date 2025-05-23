#!/usr/bin/python3
import argparse
import logging
import os
import subprocess
import sys


logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger()


def get_changed_files(base_ref: str) -> list[str]:
    try:
        result = subprocess.run(["git", "diff", "--name-only", base_ref], check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        logger.exception(f"Failed to get changed files\n\n{e.stdout}\n\n{e.stderr}")
        raise
    return result.stdout.splitlines()


def filter_policies(changed_files: list[str]) -> list[str]:
    return [file for file in changed_files if file.startswith("policies/") and file.endswith(".json")]


def get_system_prompt():
    with open("policies/_system.md") as f:
        return f.read()


def generate_markdown(system, policy):
    return "# Some test"


def main(base_ref):
    changed_or_added_files = get_changed_files(base_ref)
    policies = filter_policies(changed_or_added_files)

    system = get_system_prompt()

    policies_markdown = {}
    for policy in policies:
        # TODO: Check if the resulting policy already exists and if so, use it in the system query
        md = generate_markdown(system, policy)
        policies_markdown[policy] = md

    # TODO: Checkout the correct branch to create a new commit
    for policy_name, markdown in policies_markdown.items():
        markdown_path = os.path.join("src", "content", "docs", policy_name)
        if os.path.exists(markdown_path):
            logger.info("Resulting markdown file already exists")
        else:
            os.makedirs(os.path.dirname(markdown_path), exist_ok=True)
        with open(markdown_path, "w+") as f:
            f.write(markdown)
        logger.info(f"Updated markdown file {markdown_path}")
        print(policy_name)
    # TODO: Push as new commit to PR


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", required=True)
    args = parser.parse_args()

    main(args.base_ref)
