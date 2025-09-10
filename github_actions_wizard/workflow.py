import os
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

yaml = YAML()


class Workflow:
    def __init__(self, name="CI Pipeline", run_name="CI Pipeline"):
        self.workflow = {"name": name, "run-name": run_name, "on": {}, "jobs": {}}
        self.file_name = None
        self.is_new_file = True

    def has_job(self, job_id):
        return job_id in self.workflow["jobs"]

    def get_jobs(self):
        return self.workflow["jobs"].keys()

    @property
    def jobs(self):
        return self.workflow["jobs"]

    def set_name(self, name, run_name=None):
        self.workflow["name"] = name
        if run_name:
            self.workflow["run-name"] = run_name
        return self

    def add_trigger_push(self, branches):
        self._add_trigger("push", "branches", branches)

    def add_trigger_release(self, types=["created"]):
        self._add_trigger("release", "types", types)

    def add_trigger_pull_request(self, branches):
        self._add_trigger("pull_request", "branches", branches)

    def add_permission(self, permission, level):
        self.workflow["permissions"] = self.workflow.get("permissions", {})
        self.workflow["permissions"][permission] = level

    def set_field(self, field, value):
        self.workflow[field] = value

    def add_job(self, job_id, **job):
        job["runs-on"] = job.get("runs-on", "ubuntu-latest")
        job["steps"] = []
        if "needs" in job and not isinstance(job["needs"], list):
            job["needs"] = [job["needs"]]

        self.workflow["jobs"][job_id] = job

        self.add_job_permission(job_id, "contents", "read")

    def add_job_permission(self, job_id, permission, level):
        self.workflow["jobs"][job_id]["permissions"] = self.workflow["jobs"][job_id].get("permissions", {})
        self.workflow["jobs"][job_id]["permissions"][permission] = level

    def get_job_field(self, job_id, field):
        return self.workflow["jobs"][job_id].get(field)

    def set_job_field(self, job_id, field, value):
        self.workflow["jobs"][job_id][field] = value
        return self

    def remove_job_field(self, job_id, field):
        if field in self.workflow["jobs"][job_id]:
            del self.workflow["jobs"][job_id][field]

    def add_job_step(self, job_id, **step):
        self.workflow["jobs"][job_id]["steps"].append(step)

    def add_job_shell_step(self, job_id, cmds, **step):
        if isinstance(cmds, list):
            run_cmd = "\n".join(cmds)
        else:
            run_cmd = cmds

        step["run"] = LiteralScalarString(run_cmd)  # Always use LiteralScalarString for block style (|) in YAML
        self.add_job_step(job_id, **step)
        return self

    def get_jobs_ids(self):
        return list(self.workflow["jobs"].keys())

    def add_upload_artifact_step(self, job_id, name="Upload Artifact", path="build"):
        if isinstance(path, list):
            path = "\n".join(path)
            path = LiteralScalarString(path)  # Use block style (|) in YAML for multi-line strings

        step = {
            "name": name,
            "uses": "actions/upload-artifact@v4",
            "with": {"name": "build", "path": path},
        }
        self.add_job_step(job_id, **step)

    def add_download_artifact_step(self, job_id, name="Download Artifact", path="build"):
        step = {
            "name": name,
            "uses": "actions/download-artifact@v5",
            "with": {"name": "build", "path": path},
        }
        self.add_job_step(job_id, **step)

    def save(self):
        path = f".github/workflows/{self.file_name}"
        os.makedirs(os.path.dirname(path), exist_ok=True)

        self._reorder_workflow()

        comment = (
            "# Generated initially using github-actions-wizard (https://github.com/cmdr2/github-actions-wizard)\n\n"
        )
        with open(path, "w") as f:
            if self.is_new_file:
                f.write(comment)
            yaml.dump(self.workflow, f)
        return path

    def load(self):
        path = f".github/workflows/{self.file_name}"
        if not os.path.exists(path):
            raise FileNotFoundError(f"Workflow file not found: {path}")

        with open(path, "r") as f:
            self.workflow = yaml.load(f)

        self.is_new_file = False

    # utilities for common steps
    def add_checkout_step(self, job_id):
        self.add_job_step(job_id, name="Checkout", uses="actions/checkout@v4")

    def add_cron_step(self, cron):
        self.workflow["on"]["schedule"] = [{"cron": cron}]
        return self

    def add_setup_python_step(self, job_id, python_version="3.x"):
        self.add_job_step(
            job_id,
            **{
                "name": "Set up Python",
                "uses": "actions/setup-python@v4",
                "with": {"python-version": python_version, "cache": "pip"},
            },
        )

    def _reorder_workflow(self):
        "Ensures that 'jobs' is the last key in the workflow, and 'steps' is the last key in each job."

        def _reorder_job(job):
            steps = job["steps"]
            del job["steps"]
            job["steps"] = steps  # Place the 'steps' key last

        jobs = self.workflow["jobs"]
        del self.workflow["jobs"]
        self.workflow["jobs"] = jobs  # Place the 'jobs' key last

        for job in jobs.values():
            _reorder_job(job)

    def reorder_jobs(self, ordered_job_ids):
        "Applies the new order of jobs as per the given list of job IDs."

        ordered_jobs = {
            job_id: self.workflow["jobs"][job_id] for job_id in ordered_job_ids if job_id in self.workflow["jobs"]
        }
        self.workflow["jobs"] = ordered_jobs
        return self

    def _add_trigger(self, trigger_type, types_key, types):
        types = types if isinstance(types, list) else [types]

        self.workflow["on"][trigger_type] = self.workflow["on"].get(trigger_type, {})
        self.workflow["on"][trigger_type][types_key] = self.workflow["on"][trigger_type].get(types_key, [])

        for t in types:
            if t not in self.workflow["on"][trigger_type][types_key]:
                self.workflow["on"][trigger_type][types_key].append(t)
