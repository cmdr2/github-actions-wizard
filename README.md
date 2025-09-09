# GitHub Actions Wizard

**GitHub Actions Wizard** is a simple tool for generating GitHub Actions workflows for common deployment tasks.

It goes beyond simple workflow generation by automatically setting up necessary permissions (such as creating AWS IAM Roles and Policies for S3 or Lambda deployments).

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

## Supported Targets

**Deployment targets:**
- AWS S3 (static site or zip-and-upload)
- AWS Lambda (function deployment)
- Publish to PyPI
- GitHub Pages

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

Select the action to perform:
1. Add a deployment target
2. Add a build step
3. Add a test step
Enter option number: 1

Select deployment target:
1. AWS S3
2. AWS Lambda
3. Publish to PyPI
Enter option number: 1

Enter GitHub repo (e.g., cmdr2/carbon, or full URL): myuser/myrepo
Select deployment trigger:
1. On branch push
2. On release creation
Enter option number: 1

Enter branch name (will react to pushes on this branch) [default=main]: main

Select upload format:
1. Zip to a single file
2. Copy all files directly
Enter option number: 1

Enter AWS S3 path to deploy to (e.g., my-bucket-name/some/path/file.zip): my-bucket/my-app.zip

... (Automatically creates the necessary IAM roles)

**IMPORTANT:** Please ensure that you set the S3_DEPLOY_ROLE environment variable (in your GitHub repository) to <generated-role-arn>
Added deployment step: deploy_to_aws_s3

✅ Workflow update complete. Workflow written: .github/workflows/gha_workflow.yml. Please customize it as necessary.
```

After this, pushes to the `main` branch of this repo will automatically upload a zip to AWS S3.

### 2. Deploy to AWS Lambda

```
$ github-actions-wizard

Select the action to perform:
1. Add a deployment target
2. Add a build step
3. Add a test step
Enter option number: 1

Select deployment target:
1. AWS S3
2. AWS Lambda
3. Publish to PyPI
Enter option number: 2

Enter GitHub repo (e.g., cmdr2/carbon, or full URL): myuser/myrepo

Select deployment trigger:
1. On branch push
2. On release creation
Enter option number: 2

Enter the AWS Lambda function name to deploy to: my-lambda-func

... (Automatically creates the necessary IAM roles)

**IMPORTANT:** Please ensure that you set the LAMBDA_DEPLOY_ROLE environment variable (in your GitHub repository) to <generated-role-arn>
Added deployment step: deploy_to_aws_lambda

✅ Workflow update complete. Workflow written: .github/workflows/gha_workflow.yml. Please customize it as necessary.
```

After this, pushes to the `main` branch of this repo will automatically update the AWS Lambda Function.

---

## Customization

After generation, you can edit the workflow YAML file in `.github/workflows` to add project-specific steps or modify the configuration as needed.

---

## License

MIT
