from .. import forms, cmd, pypi


def add_build_job(workflow):
    build_type = forms.ask_build_type()

    job_id = "build"

    workflow.add_job(job_id)
    workflow.add_checkout_step(job_id)

    if build_type == "copy":
        add_copy_build_steps(workflow, job_id)
    elif build_type == "zip":
        add_zip_build_steps(workflow, job_id)
    elif build_type == "python_build":
        add_python_build_steps(workflow, job_id)
    elif build_type == "hugo":
        add_hugo_build_steps(workflow, job_id)

    return job_id


def add_copy_build_steps(workflow, job_id):
    workflow.add_job_shell_step(
        job_id,
        ["mkdir build", "rsync -av --exclude '.git' --exclude '.github' --exclude 'build' ./ build/"],
        name="Copy files into the build",
    )
    workflow.add_upload_artifact_step(job_id, path="build")


def add_zip_build_steps(workflow, job_id):
    cmd.add_workflow_zip_step(workflow, job_id, zip_name="build.zip")
    workflow.add_upload_artifact_step(job_id, path="build.zip")


def add_python_build_steps(workflow, job_id):
    workflow.add_setup_python_step(job_id)
    pypi.add_install_dependencies_step(workflow, job_id)
    pypi.add_build_package_step(workflow, job_id)
    workflow.add_upload_artifact_step(job_id, path=["dist", "pyproject.toml"])


def add_hugo_build_steps(workflow, job_id):
    workflow.add_job_step(
        job_id,
        **{
            "name": "Setup Hugo",
            "uses": "peaceiris/actions-hugo@v2",
            "with": {"hugo-version": "latest"},
        },
    )
    workflow.add_job_shell_step(job_id, "hugo --minify", name="Build")
    workflow.add_job_step(
        job_id,
        **{
            "name": "Upload pages artifact",
            "uses": "actions/upload-pages-artifact@v3",
            "with": {"name": "build", "path": "public"},
        },
    )
