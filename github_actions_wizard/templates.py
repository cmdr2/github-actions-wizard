from .jobs import add_build_job, add_test_job, add_deploy_job
from . import forms

CI_DEPLOY_FILE = "ci_deploy_workflow.yml"

TEMPLATES = {
    "python_package": {
        "build_type": "python_build",
        "deploy_target": "pypi",
        "default_workflow_file_name": CI_DEPLOY_FILE,
    },
    "static_hugo_website": {
        "build_type": "hugo",
        "deploy_target": "github_pages",
        "default_workflow_file_name": CI_DEPLOY_FILE,
    },
    "static_s3_website": {
        "build_type": "copy",
        "deploy_target": "aws_s3",
        "default_workflow_file_name": CI_DEPLOY_FILE,
    },
    "lambda_deploy": {
        "build_type": "zip",
        "deploy_target": "aws_lambda",
        "default_workflow_file_name": CI_DEPLOY_FILE,
    },
    "itch.io": {
        "build_type": "zip",
        "deploy_target": "itch.io",
        "default_workflow_file_name": CI_DEPLOY_FILE,
    },
}


def apply_template(workflow, template):
    answers = TEMPLATES.get(template, {})

    with forms.override_ask_functions(**answers):
        add_build_job(workflow)
        add_deploy_job(workflow)

        if "default_workflow_file_name" in answers:
            workflow.file_name = answers["default_workflow_file_name"]
