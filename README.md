<h1 align="center">PolGen - AI powered policies Wiki</h1>

<p align="center">
    <em>PolGen policy wiki. Setup in minutes. Create policies using GenAI. Use GitHub PRs as the document control and review process.</em>
</p>
<p align="center">
    <em>Demo at <a href="https://example.com">https://example.com</a></em>
</p>

---

Automate the creation of a Company Wiki with policies. Declare your policies in a structured way and let AI generate
the content and package it in a user-friendly Wiki. Use GitHub PR review and approve workflow to manage document change control.

## Why use PolGen

- Create company policies using Gen AI. Only define the high-level requirements, let AI render it in human-readable form.
- Deploy a blazing fast company wiki using Astro and the Starlight theme.
- Serverless deployment on AWS, negligible hosting costs, zero maintenance.
- Use GitHub PRs and Workflow Actions as document review and control. ISO 27001 compliant.

## Demo

View our demo deployment at https://example.com.

- **username:** user
- **password:** PolGen-Demo-30

## Getting started

- Fork this repo
- Sign up for Gemini and request an API key (included with Google Workspace).
- Create an AWS account to deploy your wiki to:
  - Create an S3 bucket to hold the OpenTofu state. Name it `state-${substr(sha256(<repository name. ex: secu-ma/polgen>), 0, 16)}`
  - Create an IAM user and create credentials (AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY)
- Create the following GitHub secrets for the repository:
  - GEMINI_API_KEY
  - AWS_SECRET_ACCESS_KEY
- Create the following GitHub variables for the repository:
  - AWS_ACCESS_KEY_ID
  - AWS_REGION (ex: eu-west-1)
  - COGNITO_USER_EMAIL (optional, the email address for a user that will be able to access the Wiki. The user will receive an invitation with a temporary password.)
- Create a branch from main
- Edit policies in /policies/ (see /policies/examples/)
- Push to GitHub
- Create a PR to main
- Let the GitHub workflow generate your content and add to your PR
- (Optional) Edit the generated content
- Approve the PR and merge
- Let the GitHub workflow build and deploy your wiki with content

## License

This project is licensed under the terms of the [MPL 2.0](https://www.mozilla.org/MPL/) license.

Wiki based on the [Astro Starlight](https://github.com/withastro/starlight/) theme under the MIT license.  
Copyright (c) 2023 [Astro contributors](https://github.com/withastro/starlight/graphs/contributors).