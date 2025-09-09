from .. import forms, aws, pypi


def add_deploy_job(workflow):
    target = forms.ask_deploy_target()
    job_id = f"deploy_to_{target}"

    workflow.add_job(job_id)

    # get repo and trigger info
    gh_branch = None
    trigger = forms.ask_deploy_trigger()

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
        gh_owner, gh_repo = forms.ask_github_repo_name()

        if target == "aws_s3":
            add_s3_deploy_job(workflow, job_id, gh_owner, gh_repo, gh_branch)
        elif target == "aws_lambda":
            add_lambda_deploy_job(workflow, job_id, gh_owner, gh_repo, gh_branch)
    elif target == "pypi":
        add_pypi_deploy_job(workflow, job_id)
    elif target == "github_pages":
        add_github_pages_deploy_job(workflow, job_id)


# --- Deploy job helpers ---
def add_s3_deploy_job(workflow, job_id, gh_owner, gh_repo, gh_branch):
    ROLE_ENV_VAR = "S3_DEPLOY_ROLE"

    workflow.add_download_artifact_step(job_id, path=".")

    s3_path = forms.ask_aws_s3_path()
    is_zip_file = s3_path.endswith(".zip")

    print("\nConfiguring S3 deploy permissions in IAM...\n")

    aws_account_id = aws.get_account_id()  # fetching this after all the form questions, since this is slow
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


def add_lambda_deploy_job(workflow, job_id, gh_owner, gh_repo, gh_branch):
    ROLE_ENV_VAR = "LAMBDA_DEPLOY_ROLE"

    workflow.add_download_artifact_step(job_id, path=".")

    function_name = forms.ask_aws_lambda_function_name()

    print("\nConfiguring Lambda deploy permissions in IAM...\n")

    aws_account_id = aws.get_account_id()  # fetching this after all the form questions, since this is slow
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
