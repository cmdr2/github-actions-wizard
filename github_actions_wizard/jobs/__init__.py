from .build_jobs import add_build_job
from .test_jobs import add_test_job
from .deploy_jobs import add_deploy_job

from .. import forms


def add_custom_workflow(workflow, looping=True):
    while True:
        action = forms.ask_action_to_perform(workflow)

        if action == "build":
            job_id = add_build_job(workflow)
        elif action == "test":
            job_id = add_test_job(workflow)
        elif action == "deploy":
            job_id = add_deploy_job(workflow)
        elif action == "quit":
            break

        print(f"\n✅ Job '{job_id}' added to the workflow.\n")

        if not looping:
            break
