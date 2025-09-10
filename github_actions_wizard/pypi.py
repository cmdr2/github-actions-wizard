def add_install_dependencies_step(workflow, job_id):
    workflow.add_job_shell_step(
        job_id,
        ["python -m pip install --upgrade pip", "pip install build wheel"],
        name="Install dependencies",
    )


def add_check_pypi_version_step(workflow, job_id):
    workflow.add_job_shell_step(
        job_id,
        [
            f"PACKAGE_NAME=$(python -c \"import toml; print(toml.load('pyproject.toml')['project']['name'])\")",
            f"TOML_VERSION=$(python -c \"import toml; print(toml.load('pyproject.toml')['project']['version'])\")",
            f"PYPI_VERSION=$(python -c \"import requests; r = requests.get('https://pypi.org/pypi/$PACKAGE_NAME/json'); print(None if r.status_code == 404 else r.json()['info']['version'])\")",
            'echo "Package name: $PACKAGE_NAME"',
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
    workflow.add_job_shell_step(job_id, "python -m build", name="Build package")


def add_publish_to_pypi_step(workflow, job_id):
    step = {
        "name": "Publish to PyPI",
        "if": "steps.check-version.outputs.publish == 'true'",
        "uses": "pypa/gh-action-pypi-publish@release/v1",
        "with": {"verbose": True},
    }
    workflow.add_job_step(job_id, **step)
