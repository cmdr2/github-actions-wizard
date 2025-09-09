from .jobs import add_build_job, add_test_job, add_deploy_job
from . import forms

TEMPLATE_ANSWERS = {
    "python_package": {"build_type": "python_build", "deploy_target": "pypi"},
    "static_hugo_website": {"build_type": "hugo", "deploy_target": "github_pages"},
    "static_s3_website": {"build_type": "copy", "deploy_target": "aws_s3"},
    "lambda_deploy": {"build_type": "zip", "deploy_target": "aws_lambda"},
}


def apply_template(workflow, template):
    answers = TEMPLATE_ANSWERS.get(template, {})

    with forms.override_ask_functions(**answers):
        add_build_job(workflow)
        add_deploy_job(workflow)
