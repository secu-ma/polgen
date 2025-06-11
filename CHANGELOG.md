# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-06-11

### Added

- Add multiple code quality and developer aids:
  - Use [Black](https://github.com/psf/black) for Python code formatting
  - Use [Prettier](https://github.com/prettier/prettier) for Wiki and Lambda@Edge code formatting
  - [MPL license header check](https://github.com/viperproject/check-license-header)
  - PR workflow checks
  - [Renovate](https://github.com/renovatebot/renovate) for dependency update management

### Changed

- Multiple (dev) dependencies updated. Most notably, Lambda@Edge runs on **Node 22** now.

### Fixed

- Running `polgen.py init` without Boto3 or AWS CLI installed now correctly prints manual instructions.


## [0.1.0] - 2025-06-01

### Added

- Wiki based on [Astro Starlight](https://github.com/withastro/starlight/).
- Example Information Security Policy and Password Policy.
- PR pipeline using Gemini to generate policies from requirements.
- Build and deployment pipeline using AWS as the cloud provider.
- `polgen.py init` script to bootstrap the AWS account and help with quick start setup.
- AWS Bootstrap infrastructure based on CloudFormation.
- Wiki infrastructure based on [OpenTofu](https://opentofu.org/).
- Released under the terms of the [MPL 2.0](https://www.mozilla.org/MPL/) license.
