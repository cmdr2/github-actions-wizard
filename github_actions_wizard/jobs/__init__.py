from .build_jobs import add_build_job
from .test_jobs import add_test_job
from .deploy_jobs import add_deploy_job

from .. import forms


def add_custom_workflow(workflow):
    action = forms.ask_action_to_perform(workflow)

    if action == "build":
        add_build_job(workflow)
    elif action == "test":
        add_test_job(workflow)
    elif action == "deploy":
        add_deploy_job(workflow)
