#!/usr/bin/python3
import argparse
import logging
import os
import subprocess
import sys


logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger()


ai_service = None


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


class GoogleGenAI:
    def __init__(self):
        try:
            from google import genai
            from google.genai import types
        except ImportError:
            logger.info("Installing Google genai")
            # Dynamic installation of google genai library
            subprocess.run(["pip", "install", "google-genai==1.16.1"], check=True, capture_output=True, text=True)
            from google import genai
            from google.genai import types
            logger.info("Google genai library installed")
        self.model = "gemini-2.5-flash-preview-05-20"
        self.client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
        self.genai = genai
        self.types = types

    def generate(self, system, policy):
        generate_content_config = self.types.GenerateContentConfig(
            response_mime_type="text/plain",
            system_instruction=[
                self.types.Part.from_text(text=system)
            ]
        )
        contents = [
            self.types.Content(
                role="user",
                parts=[
                    self.types.Part.from_text(text=policy),
                ],
            ),
        ]
        document = ""
        for chunk in self.client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=generate_content_config,
        ):
            document += chunk.text
        return document

def get_ai_service():
    # TODO: Read from config which genai service to use
    global ai_service
    if ai_service is None:
        ai_service = GoogleGenAI()
    return ai_service


def generate_markdown(system, policy):
    ai_client = get_ai_service()
    return ai_client.generate(system, policy)


def main(base_ref):
    changed_or_added_files = get_changed_files(base_ref)
    policies = filter_policies(changed_or_added_files)

    system = get_system_prompt()

    policies_markdown = {}
    for policy in policies:
        # TODO: Check if the resulting policy already exists and if so, use it in the system query
        md = generate_markdown(system, policy)
        policies_markdown[policy] = md

    for policy_name, markdown in policies_markdown.items():
        markdown_path = os.path.join("wiki", "src", "content", "docs", policy_name)
        root, ext = os.path.splitext(markdown_path)
        if ext == ".json":
            markdown_path = root + ".md"
        if os.path.exists(markdown_path):
            logger.info("Resulting markdown file already exists")
        else:
            os.makedirs(os.path.dirname(markdown_path), exist_ok=True)
        with open(markdown_path, "w+") as f:
            f.write(markdown)
        logger.info(f"Updated markdown file {markdown_path}")
        print(policy_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-ref", required=True)
    args = parser.parse_args()

    main(args.base_ref)
