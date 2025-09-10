from .jobs import add_custom_workflow
from . import forms

CI_DEPLOY_FILE = "ci_deploy_workflow.yml"
CI_TEST_FILE = "ci_test_workflow.yml"

TEMPLATES = {
    "python_package": {
        "default_workflow_file_name": CI_DEPLOY_FILE,
        "jobs": [
            {"action_to_perform": "build", "build_type": "python_build"},
            {"action_to_perform": "deploy", "deploy_target": "pypi"},
        ],
    },
    "static_hugo_website": {
        "default_workflow_file_name": CI_DEPLOY_FILE,
        "jobs": [
            {"action_to_perform": "build", "build_type": "hugo"},
            {"action_to_perform": "deploy", "deploy_target": "github_pages"},
        ],
    },
    "static_s3_website": {
        "default_workflow_file_name": CI_DEPLOY_FILE,
        "jobs": [
            {"action_to_perform": "build", "build_type": "copy"},
            {"action_to_perform": "deploy", "deploy_target": "aws_s3"},
        ],
    },
    "lambda_deploy": {
        "default_workflow_file_name": CI_DEPLOY_FILE,
        "jobs": [
            {"action_to_perform": "build", "build_type": "zip"},
            {"action_to_perform": "deploy", "deploy_target": "aws_lambda"},
        ],
    },
    "itch_io": {
        "default_workflow_file_name": CI_DEPLOY_FILE,
        "jobs": [
            {"action_to_perform": "build", "build_type": "zip"},
            {"action_to_perform": "deploy", "deploy_target": "itch_io"},
        ],
    },
    "pytest_ci": {
        "default_workflow_file_name": CI_TEST_FILE,
        "jobs": [{"action_to_perform": "test", "test_type": "pytest"}],
    },
}


def apply_template(workflow, template):
    template = TEMPLATES.get(template, {})

    workflow.file_name = template.get("default_workflow_file_name")

    for job in template.get("jobs", []):
        answers = job.copy()
        with forms.override_ask_functions(**answers):
            add_custom_workflow(workflow, looping=False)

    # hack to ensure that test-only workflows have a trigger
    actions = {job.get("action_to_perform") for job in template.get("jobs", [])}
    if actions == {"test"}:
        fix_test_only_workflow(workflow)


def fix_test_only_workflow(workflow):
    workflow.add_trigger_push(branches=["main"])
    workflow.add_trigger_pull_request(branches=["main"])

    workflow.set_name("CI Tests", run_name="CI Tests")

    # replace download-artifact with checkout, since there is no build job
    def replace_download_with_checkout():
        for job in workflow.jobs.values():
            for i, step in enumerate(job["steps"]):
                if step.get("uses").startswith("actions/download-artifact"):
                    job["steps"][i] = {
                        "name": "Checkout code",
                        "uses": "actions/checkout@v4",
                    }
                    return

    replace_download_with_checkout()
