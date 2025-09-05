import os

from . import aws, pypi, forms, cmd
from .workflow import Workflow


def main():
    if not os.path.exists(".git"):
        print("This script must be run from a Git repository.")
        return

    print(
        """# GitHub Actions Wizard
https://github.com/cmdr2/github-actions-wizard
"""
    )

    deployment_workflow()


def deployment_workflow():
    target = forms.ask_deployment_target()

    gh_owner, gh_repo = forms.ask_github_repo_name()
    gh_branch = None
    trigger = forms.ask_deployment_trigger()

    workflow = Workflow()
    if trigger == "push":
        gh_branch = forms.ask_github_branch_name(help_text="will react to pushes on this branch")
        workflow.set_trigger_push(gh_branch)
    elif trigger == "release":
        workflow.set_release_trigger()

    if target.startswith("aws_"):
        aws_account_id = aws.get_account_id()

        workflow.add_id_token_write_permission("deploy")

        if target == "aws_s3":
            s3_deploy_workflow(aws_account_id, gh_owner, gh_repo, gh_branch, workflow)
        elif target == "aws_lambda":
            lambda_deploy_workflow(aws_account_id, gh_owner, gh_repo, gh_branch, workflow)
    elif target == "pypi":
        pypi_publish_workflow(workflow)


def s3_deploy_workflow(aws_account_id, gh_owner, gh_repo, gh_branch, workflow):
    ROLE_ENV_VAR = "S3_DEPLOY_ROLE"
    upload_format = forms.ask_upload_bundle_format()

    s3_path = forms.ask_aws_s3_path(is_file=upload_format == "zip")

    role_arn = aws.create_policy_and_role_for_github_to_s3_deploy(
        aws_account_id, s3_path, gh_owner, gh_repo, gh_branch, upload_format
    )

    workflow.set_name("Deploy to S3")

    aws.add_workflow_fetch_aws_credentials_step(workflow, role_env_var=ROLE_ENV_VAR)

    if upload_format == "zip":
        cmd.add_workflow_zip_step(workflow, zip_name="deploy.zip")
        aws.add_workflow_s3_cp_step(workflow, "deploy.zip", s3_path, acl="public-read")
    elif upload_format == "copy_all_files":
        aws.add_workflow_s3_sync_step(workflow, ".", s3_path)

    workflow_file = workflow.write("deploy_to_s3.yml")

    print("\n✅ S3 setup complete.")
    print(f"Workflow written: {workflow_file}. Please customize it as necessary.")
    print(f"**IMPORTANT:** Set GitHub repo variable {ROLE_ENV_VAR} to {role_arn}")


def lambda_deploy_workflow(aws_account_id, gh_owner, gh_repo, gh_branch, workflow):
    ROLE_ENV_VAR = "LAMBDA_DEPLOY_ROLE"

    function_name = forms.ask_aws_lambda_function_name()

    role_arn = aws.create_policy_and_role_for_github_to_lambda_deploy(
        aws_account_id, function_name, gh_owner, gh_repo, gh_branch
    )

    workflow.set_name("Deploy to Lambda")

    aws.add_workflow_fetch_aws_credentials_step(workflow, role_env_var=ROLE_ENV_VAR)

    cmd.add_workflow_zip_step(workflow, zip_name="function.zip")
    aws.add_workflow_lambda_deploy_step(workflow, function_name, "function.zip")

    workflow_file = workflow.write("deploy_to_lambda.yml")

    print("\n✅ Lambda setup complete.")
    print(f"Workflow written: {workflow_file}. Please customize it as necessary.")
    print(f"**IMPORTANT:** Set GitHub repo variable {ROLE_ENV_VAR} to {role_arn}")


def pypi_publish_workflow(workflow):
    package_name = cmd.get_package_name_from_pyproject()

    print(f"Setting up PyPI publish for package: {package_name}")

    workflow.set_name("Publish to PyPI")
    workflow.add_id_token_write_permission("deploy")

    pypi.add_setup_python_step(workflow)
    pypi.add_install_dependencies_step(workflow)
    pypi.add_check_pypi_version_step(workflow, package_name)
    pypi.add_build_package_step(workflow)
    pypi.add_publish_to_pypi_step(workflow)

    workflow_file = workflow.write("publish_to_pypi.yml")
    workflow_file_name = os.path.basename(workflow_file)

    print("\n✅ PyPI setup complete.")
    print(f"Workflow written: {workflow_file}. Please customize it as necessary.")
    print(
        "**IMPORTANT:** Please ensure that you've added GitHub as a trusted publisher in your PyPI account: https://docs.pypi.org/trusted-publishers/"
    )
    print(f"Note: You can use the workflow file name ({workflow_file_name}) while configuring the trusted publisher.")


if __name__ == "__main__":
    main()
