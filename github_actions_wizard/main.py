import os

from . import forms
from .jobs import add_build_job, add_test_job, add_deploy_job
from .templates import apply_template
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

    template = forms.ask_workflow_template(workflow)
    if template == "custom":
        show_workflow_jobs(workflow)

        action = forms.ask_action_to_perform(workflow)

        if action == "build":
            add_build_job(workflow)
        elif action == "test":
            add_test_job(workflow)
        elif action == "deploy":
            add_deploy_job(workflow)
    else:
        apply_template(workflow, template)

    write_workflow_file(workflow)


def write_workflow_file(workflow):
    update_job_dependencies(workflow)
    ensure_job_order(workflow)

    workflow_file = workflow.save()
    print(f"\n✅ Workflow update complete. Workflow written: {workflow_file}. Please customize it as necessary.")


def show_workflow_jobs(workflow):
    jobs = workflow.get_jobs_ids()
    if jobs:
        print("Current workflow jobs:")
        for job in jobs:
            print(f" - {job}")
        print("")


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
