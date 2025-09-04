# GitHub Actions Wizard

**GitHub Actions Wizard** is a simple wizard for generating GitHub Actions workflows for common tasks.

It goes beyond simple workflow generation by automatically setting up necessary permissions (such as creating AWS IAM Roles and Policies for S3 or Lambda deployments).

To use it, run the `github-actions-wizard` CLI tool in your repository's folder, and answer the interactive prompts. The generated workflow files will be saved in your repository's `.github/workflows` folder. You can customize these files further, as necessary.

---

## Features

- **Easy workflow generation** for deployments and tests
- **Automatic AWS permissions setup** for S3 and Lambda deployments
- **Interactive CLI** guides you through configuration
- **Edit generated workflows** to fine-tune for your project

## Why?

While you can certainly write these workflow files yourself, this tool reduces the friction of setting up deployments each time a new GitHub repository is created. The deployment setup is more than just the workflow yaml file (for e.g. AWS targets need IAM Role and Policy creation).

I needed this for myself because I release a lot of projects. The deployment targets vary per project - some copy files to AWS S3, others publish to PyPI, some release on itch.io, others deploy to AWS Lambda, and so on. It's a waste of time to look up and configure manually each time I release a new project.

---

## Supported Deployment & Test Targets

Currently, GitHub Actions Wizard supports:

- **Deployment:**
	- AWS S3 (static site or file uploads)
	- AWS Lambda (function deployment)
- **Testing:**
	- On commit (push to branch)
	- On release creation
	- On a schedule (cron)

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

You'll be guided through a series of prompts to select the type of workflow (deployment or test), target platform, branch, and other details. The tool will then generate the appropriate workflow YAML file and, for AWS deployments, set up the required IAM roles and policies.

---

## Examples


### 1. Deploy to AWS S3

```
$ github-actions-wizard

Select action type:
1. Test
2. Deployment
Enter option number: 2
Select deployment target:
1. AWS S3
2. AWS Lambda
Enter option number: 1
Enter GitHub repo (e.g., cmdr2/carbon, or full URL): myuser/myrepo
Enter branch name (will react to pushes on this branch) [default=main]: main
Select upload format:
1. Zip to a single file
2. Copy all files directly
Enter option number: 1
Enter AWS S3 path to deploy to (e.g., my-bucket-name/some/path/file.zip): my-bucket/my-app.zip
... (Automatically creates the necessary IAM roles)

✅ S3 setup complete.
Workflow written: .github/workflows/deploy_to_s3.yml. Please customize it as necessary.
**IMPORTANT:** Set GitHub repo variable S3_DEPLOY_ROLE to <generated-role-arn>
```

After this, pushes to the `main` branch of this repo will automatically upload a zip to S3.

### 2. Deploy to AWS Lambda

```
$ github-actions-wizard

Select action type:
1. Test
2. Deployment
Enter option number: 2
Select deployment target:
1. AWS S3
2. AWS Lambda
Enter option number: 2
Enter GitHub repo (e.g., cmdr2/carbon, or full URL): myuser/myrepo
Enter branch name (will react to pushes on this branch) [default=main]: main
Enter the AWS Lambda function name to deploy to: my-lambda-func
... (Automatically creates the necessary IAM roles)

✅ Lambda setup complete.
Workflow written: .github/workflows/deploy_to_s3.yml. Please customize it as necessary.
**IMPORTANT:** Set GitHub repo variable LAMBDA_DEPLOY_ROLE to <generated-role-arn>
```

After this, pushes to the `main` branch of this repo will automatically update the Lambda Function.

### 3. Set up a Test Workflow

```
$ github-actions-wizard

Select action type:
1. Test
2. Deployment
Enter option number: 1
Select test trigger:
1. Every commit push
2. Every release creation
3. At periodic intervals (automatically)
Enter option number: 1
Enter GitHub branch name (will react to pushes on this branch) [default=main]: main

✅ Test workflow setup complete.
Workflow written: .github/workflows/test_workflow.yml. Please customize it as necessary.
```

After this, pushes to the `main` branch of this repo will automatically run the configured tests.

---

## Customization

After generation, you can edit the workflow YAML files in `.github/workflows` to add project-specific steps or modify the configuration as needed.

---

## License

MIT
