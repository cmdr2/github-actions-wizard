from .. import forms


def add_test_job(workflow):
    test_type = forms.ask_test_type()

    job_id = "test"

    workflow.add_job(job_id)

    if test_type == "pytest":
        add_pytest_test_steps(workflow, job_id)
    elif test_type == "custom":
        add_custom_test_steps(workflow, job_id)

    return job_id


def add_pytest_test_steps(workflow, job_id):
    workflow.add_download_artifact_step(job_id, path=".")
    workflow.add_setup_python_step(job_id)
    workflow.add_job_shell_step(
        job_id,
        [
            "python -m pip install --upgrade pip",
            "pip install pytest",
            "if [ -f requirements.txt ]; then pip install -r requirements.txt; fi",
        ],
        name="Install dependencies",
    )
    workflow.add_job_shell_step(job_id, "python -m pytest", name="Run tests")


def add_custom_test_steps(workflow, job_id):
    workflow.add_download_artifact_step(job_id, path="build")
    workflow.add_job_shell_step(job_id, "echo Running tests...", name="Dummy Test Command")
