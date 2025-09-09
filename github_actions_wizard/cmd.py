import subprocess
import tempfile
import json
import os


def run_capture(cmd):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, check=True, capture_output=True, text=True)
    return result.stdout


def run(cmd):
    print(f"Running: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)


def as_temp_file(data, suffix=""):
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="w") as tmp_file:
        json.dump(data, tmp_file, indent=2)
        return tmp_file.name


def add_workflow_zip_step(workflow, job_id, zip_name="deploy.zip"):
    zip_cmd = f"zip -r {zip_name} . -x '.git/*' '.github/*' 'LICENSE' 'README.md' '*.sh'"
    workflow.add_job_shell_step(job_id, zip_cmd, name="Create Zip Archive")
    return workflow


def get_default_github_repo():
    git_config_path = os.path.join(os.getcwd(), ".git", "config")
    if os.path.exists(git_config_path):
        with open(git_config_path, "r") as f:
            for line in f:
                if line.strip().startswith("url ="):
                    url = line.strip().split("=", 1)[1].strip()
                    if url.startswith("http://") or url.startswith("https://") or url.startswith("git@"):
                        # Handle both HTTPS and SSH URLs
                        if url.startswith("git@"):
                            # git@github.com:owner/repo.git
                            url = url.split(":", 1)[-1]
                        else:
                            # https://github.com/owner/repo.git
                            url = url.rstrip("/").split("/")[-2] + "/" + url.rstrip("/").split("/")[-1]
                        repo = url[:-4] if url.endswith(".git") else url
                        return repo
    return None
