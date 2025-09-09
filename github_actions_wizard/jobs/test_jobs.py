def add_test_job(workflow):
    job_id = "test"

    workflow.add_job(job_id)

    workflow.add_download_artifact_step(job_id, path="build")
    workflow.add_job_shell_step(job_id, "echo Running tests...", name="Dummy Test Command")

    print("Added test job. The deployment steps will now run after the tests pass")
