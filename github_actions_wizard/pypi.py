def add_setup_python_step(workflow, job_id):
    step = {"name": "Set up Python", "uses": "actions/setup-python@v4", "with": {"python-version": "3.x"}}
    workflow.add_job_step(job_id, **step)


def add_install_dependencies_step(workflow, job_id):
    workflow.add_job_shell_step(
        job_id,
        ["python -m pip install --upgrade pip", "pip install build wheel pytest toml requests"],
        name="Install dependencies",
    )


def add_check_pypi_version_step(workflow, job_id, package_name):
    workflow.add_job_shell_step(
        job_id,
        [
            f"TOML_VERSION=$(python -c \"import toml; print(toml.load('pyproject.toml')['project']['version'])\")",
            f"PYPI_VERSION=$(python -c \"import requests; r = requests.get('https://pypi.org/pypi/{package_name}/json'); print(None if r.status_code == 404 else r.json()['info']['version'])\")",
            'echo "Local version: $TOML_VERSION"',
            'echo "PyPI version: $PYPI_VERSION"',
            'if [ "$TOML_VERSION" = "$PYPI_VERSION" ]; then',
            '  echo "Versions match. Skipping publish."',
            '  echo "publish=false" >> $GITHUB_OUTPUT',
            "else",
            '  echo "Versions differ. Proceeding with publish."',
            '  echo "publish=true" >> $GITHUB_OUTPUT',
            "fi",
        ],
        name="Check PyPI version",
        id="check-version",
    )


def add_build_package_step(workflow, job_id):
    step = {
        "name": "Build package",
        "if": "steps.check-version.outputs.publish == 'true'",
    }
    workflow.add_job_shell_step(job_id, "python -m build", **step)


def add_publish_to_pypi_step(workflow, job_id):
    step = {
        "name": "Publish to PyPI",
        "if": "steps.check-version.outputs.publish == 'true'",
        "uses": "pypa/gh-action-pypi-publish@release/v1",
        "with": {"verbose": True},
    }
    workflow.add_job_step(job_id, **step)
