import os

from . import aws, pypi, forms, cmd
from .workflow import Workflow


def main():
    if not os.path.exists(".git"):
        print("This script must be run from a Git repository.")
        return

    print("""# GitHub Actions Wizard\nhttps://github.com/cmdr2/github-actions-wizard\n""")

    interactive_workflow_wizard()


def interactive_workflow_wizard():
    workflow = Workflow()
    workflow.load()

    show_workflow_jobs(workflow)

    action = forms.ask_action_to_perform(workflow)

    if action == "build":
        add_build_job(workflow)
    elif action == "test":
        add_test_job(workflow)
    elif action == "deploy":
        add_deployment_job(workflow)

    update_job_dependencies(workflow)
    ensure_job_order(workflow)

    # Write workflow file
    workflow_file = workflow.save()
    print(f"\n✅ Workflow update complete. Workflow written: {workflow_file}. Please customize it as necessary.")


def show_workflow_jobs(workflow):
    jobs = workflow.get_jobs_ids()
    if jobs:
        print("Current workflow jobs:")
        for job in jobs:
            print(f" - {job}")
        print("")


def add_build_job(workflow):
    build_type = forms.ask_build_type()

    job_id = "build"

    workflow.add_job(job_id)
    workflow.add_checkout_step(job_id)

    if build_type == "copy_all":
        add_copy_all_build_steps(workflow, job_id)
    elif build_type == "zip":
        add_zip_build_steps(workflow, job_id)
    elif build_type == "python_build":
        add_python_build_steps(workflow, job_id)
    elif build_type == "hugo":
        add_hugo_build_steps(workflow, job_id)


def add_copy_all_build_steps(workflow, job_id):
    workflow.add_job_shell_step(
        job_id,
        ["mkdir build", "rsync -av --exclude='.git' --exclude='.github' ./ build/"],
        name="Copy files excluding .git and .github",
    )
    workflow.add_upload_artifact_step(job_id, path="build")
    print("Added copy-all build job. The deployment steps will now use the files that were checked out.")


def add_zip_build_steps(workflow, job_id):
    cmd.add_workflow_zip_step(workflow, job_id, zip_name="build.zip")
    workflow.add_upload_artifact_step(job_id, path="build.zip")
    print("Added zip build job. The deployment steps will now use the 'build.zip' artifact.")


def add_python_build_steps(workflow, job_id):
    pypi.add_setup_python_step(workflow, job_id)
    pypi.add_install_dependencies_step(workflow, job_id)
    pypi.add_build_package_step(workflow, job_id)
    workflow.add_upload_artifact_step(job_id, path=["dist", "pyproject.toml"])
    print("Added python build job. The deployment steps will now use the 'dist' directory.")


def add_hugo_build_steps(workflow, job_id):
    workflow.add_job_step(
        job_id,
        **{
            "name": "Setup Hugo",
            "uses": "peaceiris/actions-hugo@v2",
            "with": {"hugo-version": "latest"},
        },
    )
    workflow.add_job_shell_step(job_id, "hugo --minify", name="Build")
    workflow.add_job_step(
        job_id,
        **{
            "name": "Upload pages artifact",
            "uses": "actions/upload-pages-artifact@v3",
            "with": {"name": "build", "path": "public"},
        },
    )
    print("Added Hugo build job. The deployment steps will now use the Hugo 'public' directory as an artifact.")


def add_test_job(workflow):
    job_id = "test"

    workflow.add_job(job_id)

    workflow.add_download_artifact_step(job_id, path="build")
    workflow.add_job_shell_step(job_id, "echo Running tests...", name="Dummy Test Command")

    print("Added test job. The deployment steps will now run after the tests pass")


def add_deployment_job(workflow):
    target = forms.ask_deployment_target()
    job_id = f"deploy_to_{target}"

    workflow.add_job(job_id)

    # get repo and trigger info
    gh_owner, gh_repo = forms.ask_github_repo_name()
    gh_branch = None
    trigger = forms.ask_deployment_trigger()

    # set the job condition, based on the trigger
    if trigger == "push":
        gh_branch = forms.ask_github_branch_name(help_text="will react to pushes on this branch")
        workflow.add_trigger_push(gh_branch)
        workflow.set_job_field(job_id, "if", f"github.ref == 'refs/heads/{gh_branch}'")
    elif trigger == "release":
        workflow.add_trigger_release(types=["created"])
        workflow.set_job_field(job_id, "if", "github.event_name == 'release' && github.event.action == 'created'")

    workflow.add_job_permission(job_id, "id-token", "write")

    # add the remaining target-specific deployment steps
    if target.startswith("aws_"):
        aws_account_id = aws.get_account_id()

        if target == "aws_s3":
            add_s3_deploy_job(workflow, job_id, aws_account_id, gh_owner, gh_repo, gh_branch)
        elif target == "aws_lambda":
            add_lambda_deploy_job(workflow, job_id, aws_account_id, gh_owner, gh_repo, gh_branch)
    elif target == "pypi":
        add_pypi_deploy_job(workflow, job_id)
    elif target == "github_pages":
        add_github_pages_deploy_job(workflow, job_id)

    print(f"Added deployment job: {job_id}")


# --- Deploy job helpers ---
def add_s3_deploy_job(workflow, job_id, aws_account_id, gh_owner, gh_repo, gh_branch):
    ROLE_ENV_VAR = "S3_DEPLOY_ROLE"

    workflow.add_download_artifact_step(job_id, path=".")

    s3_path = forms.ask_aws_s3_path()
    is_zip_file = s3_path.endswith(".zip")
    role_arn = aws.create_policy_and_role_for_github_to_s3_deploy(
        aws_account_id, s3_path, gh_owner, gh_repo, gh_branch, is_zip_file
    )

    aws.add_workflow_fetch_aws_credentials_step(workflow, job_id, role_env_var=ROLE_ENV_VAR)

    if is_zip_file:
        aws.add_workflow_s3_cp_step(workflow, job_id, "build.zip", s3_path, acl="public-read")
    else:
        aws.add_workflow_s3_sync_step(workflow, job_id, ".", s3_path)

    print("")
    print(
        f"**IMPORTANT:** Please ensure that you set the {ROLE_ENV_VAR} environment variable (in your GitHub repository) to {role_arn}"
    )


def add_lambda_deploy_job(workflow, job_id, aws_account_id, gh_owner, gh_repo, gh_branch):
    ROLE_ENV_VAR = "LAMBDA_DEPLOY_ROLE"

    workflow.add_download_artifact_step(job_id, path=".")

    function_name = forms.ask_aws_lambda_function_name()
    role_arn = aws.create_policy_and_role_for_github_to_lambda_deploy(
        aws_account_id, function_name, gh_owner, gh_repo, gh_branch
    )
    aws.add_workflow_fetch_aws_credentials_step(workflow, job_id, role_env_var=ROLE_ENV_VAR)
    aws.add_workflow_lambda_deploy_step(workflow, job_id, function_name, "build.zip")

    print("")
    print(
        f"**IMPORTANT:** Please ensure that you set the {ROLE_ENV_VAR} environment variable (in your GitHub repository) to {role_arn}"
    )


def add_pypi_deploy_job(workflow, job_id):
    workflow.add_download_artifact_step(job_id, path=".")

    pypi.add_setup_python_step(workflow, job_id)
    workflow.add_job_shell_step(job_id, ["python -m pip install --upgrade pip", "pip install toml requests"])
    pypi.add_check_pypi_version_step(workflow, job_id)
    pypi.add_publish_to_pypi_step(workflow, job_id)

    print("")
    print(
        "**IMPORTANT:** Please ensure that you've added GitHub as a trusted publisher in your PyPI account: https://docs.pypi.org/trusted-publishers/"
    )
    print(f"Note: You can use the workflow file name ({workflow.file_name}) while configuring the trusted publisher.")


def add_github_pages_deploy_job(workflow, job_id):
    workflow.add_job_permission(job_id, "pages", "write")

    workflow.set_field("concurrency", {"group": "pages", "cancel-in-progress": True})

    workflow.add_job_shell_step(job_id, "echo Publishing the 'build' artifact", name="Publish Message")
    workflow.add_job_step(
        job_id,
        **{
            "name": "Deploy to GitHub Pages",
            "id": "deployment",
            "uses": "actions/deploy-pages@v4",
            "with": {"artifact_name": "build"},
        },
    )

    workflow.set_job_field(
        job_id, "environment", {"name": "github-pages", "url": "${{ steps.deployment.outputs.page_url }}"}
    )


def ensure_job_order(workflow):
    """
    Reorders jobs in the workflow so that build comes first, then test, then all deploy jobs, then others.
    Does NOT modify dependencies.
    """
    jobs = workflow.get_jobs_ids()
    build_jobs = [j for j in jobs if j == "build"]
    test_jobs = [j for j in jobs if j == "test"]
    deploy_jobs = [j for j in jobs if j.startswith("deploy_to_")]
    other_jobs = [j for j in jobs if j not in build_jobs + test_jobs + deploy_jobs]

    ordered = build_jobs + test_jobs + deploy_jobs + other_jobs
    workflow.reorder_jobs(ordered)


def update_job_dependencies(workflow):
    # loop through all the jobs, and update their 'needs' based on the workflow
    has_build = workflow.has_job("build")
    has_test = workflow.has_job("test")

    for job_id in workflow.get_jobs_ids():
        if job_id.startswith("deploy_to_"):
            if has_test:
                workflow.set_job_field(job_id, "needs", "test")
            elif has_build:
                workflow.set_job_field(job_id, "needs", "build")
        elif job_id == "test":
            if has_build:
                workflow.set_job_field(job_id, "needs", "build")


if __name__ == "__main__":
    main()
