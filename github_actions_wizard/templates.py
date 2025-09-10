from .jobs import add_custom_workflow
from . import forms

CI_DEPLOY_FILE = "ci_deploy_workflow.yml"

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
    "itch.io": {
        "default_workflow_file_name": CI_DEPLOY_FILE,
        "jobs": [
            {"action_to_perform": "build", "build_type": "zip"},
            {"action_to_perform": "deploy", "deploy_target": "itch.io"},
        ],
    },
}


def apply_template(workflow, template):
    template = TEMPLATES.get(template, {})

    workflow.file_name = template.get("default_workflow_file_name")

    for job in template.get("jobs", []):
        answers = job.copy()
        with forms.override_ask_functions(**answers):
            add_custom_workflow(workflow)
