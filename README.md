# GitHub Actions Wizard

**GitHub Actions Wizard** is a simple tool for generating GitHub Actions workflows for common deployment tasks.

Built primarily for my needs, but you're free to use it, if you find it useful.

It goes beyond simple workflow generation by automatically setting up necessary permissions (such as creating AWS IAM Roles and Policies for S3 or Lambda deployments). The intent is to quickly generate the overall workflow boilerplate, and then customize by editing the generated file.

To use it, run the `github-actions-wizard` CLI tool in your repository's folder, and answer the interactive prompts. The generated workflow file will be saved in your repository's `.github/workflows` folder. You can customize the file further, as necessary.

---

## Features

- **Easy workflow generation** for deployments
- **Automatic AWS permissions setup** for S3 and Lambda deployments
- **Supports multiple deployment targets** for setting up pipelines like `build -> test -> [deploy0, deploy1, ...]`
- **Interactive CLI** guides you through configuration
- **Edit generated workflows** to fine-tune for your project

## Why?

While you can certainly write these workflow files yourself, this tool reduces the friction of setting up deployments each time a new GitHub repository is created. The deployment setup is more than just the workflow yaml file (for e.g. AWS targets need IAM Role and Policy creation).

I needed this for myself because I release a lot of projects. The deployment targets vary per project - some copy files to AWS S3, others publish to PyPI, some release on itch.io, others deploy to AWS Lambda, and so on. It's a waste of time to look up and configure CI/CD manually each time I release a new project.

---

## Workflow Templates
- **Python package** - build and publish to PyPI
- **Static Hugo website** - build and deploy to GitHub Pages
- **Static S3 website** - build and deploy to AWS S3
- **AWS Lambda** - build and deploy to AWS Lambda
- **itch.io** - build and publish to itch.io
- **Pytest CI** - run tests with pytest on push and pull request (test-only)
- **Custom workflow**

## Custom Workflows

**Deployment targets:**
- AWS S3 (static site or zip-and-upload)
- AWS Lambda (function deployment)
- Publish to PyPI
- GitHub Pages
- Publish to itch.io
- Add build artifacts to GitHub release

**Build types:**
- Python wheel (.whl) and tar.gz package
- Static site with Hugo
- Dummy build

---

## Installation

You can install GitHub Actions Wizard via pip:

```sh
pip install github-actions-wizard
```

This will install the command-line tool as `github-actions-wizard`.

---

## Usage

Run the wizard from the root of your Git repository:

```sh
github-actions-wizard
```

You'll be guided through a series of prompts to select the deployment target, branch, and other details. The tool will then generate the appropriate workflow YAML file and, for AWS deployments, set up the required IAM roles and policies.

---

## Examples


### 1. Deploy to AWS S3

```
$ github-actions-wizard

Select a workflow template to start with:
1. Python package - build and publish to PyPI
2. Static Hugo website - build and deploy to GitHub Pages
3. Static S3 website - build and deploy to AWS S3
4. AWS Lambda - deploy a Python function to AWS Lambda
5. Custom workflow
Enter option number: 3

Select deployment trigger:
1. On branch push
2. On release creation
Enter option number: 1

Enter branch name (will react to pushes on this branch) [default=main]:
Enter GitHub repo [default=cmdr2/carbon]:
Enter AWS S3 path to deploy to (e.g., my-bucket-name/some/path (or path/to/file.zip)): me.cmdr2.org/carbon

Configuring S3 deploy permissions in IAM...

**IMPORTANT:** Please ensure that you set the S3_DEPLOY_ROLE environment variable (in your GitHub repository) to <generated-arn>

✅ Workflow update complete. Workflow written: .github/workflows/gha_workflow.yml. Please customize it as necessary.
```

After this, pushes to the `main` branch of this repo will automatically upload to AWS S3.

### 2. Deploy to AWS Lambda

```
$ github-actions-wizard

Select a workflow template to start with:
1. Python package - build and publish to PyPI
2. Static Hugo website - build and deploy to GitHub Pages
3. Static S3 website - build and deploy to AWS S3
4. AWS Lambda - deploy a Python function to AWS Lambda
5. itch.io - build and publish to itch.io
6. Pytest CI - run tests with pytest on push and pull request (test-only)
7. Custom workflow
Enter option number: 4

Select deployment trigger:
1. On branch push
2. On release creation
Enter option number: 1

Enter branch name (will react to pushes on this branch) [default=main]:
Enter GitHub repo [default=cmdr2/blog-agent]:
Enter the AWS Lambda function name to deploy to (e.g., my-function): blog-agent

Configuring Lambda deploy permissions in IAM...

**IMPORTANT:** Please ensure that you set the LAMBDA_DEPLOY_ROLE environment variable (in your GitHub repository) to <generated-arn>

✅ Workflow update complete. Workflow written: .github/workflows/gha_workflow.yml. Please customize it as necessary.
```

After this, pushes to the `main` branch of this repo will automatically update the AWS Lambda Function.

### 3. Deploy to PyPI

```
$ github-actions-wizard

Select a workflow template to start with:
1. Python package - build and publish to PyPI
2. Static Hugo website - build and deploy to GitHub Pages
3. Static S3 website - build and deploy to AWS S3
4. AWS Lambda - deploy a Python function to AWS Lambda
5. itch.io - build and publish to itch.io
6. Pytest CI - run tests with pytest on push and pull request (test-only)
7. Custom workflow
Enter option number: 1

Select deployment trigger:
1. On branch push
2. On release creation
Enter option number: 2

**IMPORTANT:** Please ensure that you've added GitHub as a trusted publisher in your PyPI account: https://docs.pypi.org/trusted-publishers/
Note: You can use the workflow file name (gha_workflow.yml) while configuring the trusted publisher.

✅ Workflow update complete. Workflow written: .github/workflows/gha_workflow.yml. Please customize it as necessary.
```

---

## Customization

After generation, you can edit the workflow YAML file in `.github/workflows` to add project-specific steps or modify the configuration as needed.

---

## License

MIT
