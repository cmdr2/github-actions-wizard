import os
from ruamel.yaml import YAML

yaml = YAML()


class Workflow:
    def __init__(self, name="deploy", run_name="Deployment"):
        self.workflow = {"name": name, "run-name": run_name, "on": {}, "jobs": {}}

        # add default steps
        self.add_job("deploy", runs_on="ubuntu-latest")
        self.add_read_permission("deploy")
        self.add_job_step("deploy", name="Checkout", uses="actions/checkout@v4")

    def set_name(self, name, run_name=None):
        self.workflow["name"] = name
        if run_name:
            self.workflow["run-name"] = run_name
        return self

    def add_read_permission(self, job_id):
        if "permissions" not in self.workflow["jobs"][job_id]:
            self.workflow["jobs"][job_id]["permissions"] = {}

        self.workflow["jobs"][job_id]["permissions"]["contents"] = "read"

    def add_id_token_write_permission(self, job_id):
        if "permissions" not in self.workflow["jobs"][job_id]:
            self.workflow["jobs"][job_id]["permissions"] = {}

        self.workflow["jobs"][job_id]["permissions"]["id-token"] = "write"

    def set_trigger_push(self, branches):
        self.workflow["on"]["push"] = {"branches": branches}

    def set_release_trigger(self, types=["created"]):
        self.workflow["on"]["release"] = {"types": types}

    def add_job(self, job_id, runs_on="ubuntu-latest"):
        job = {"runs-on": runs_on, "steps": []}
        self.workflow["jobs"][job_id] = job

    def add_job_step(self, job_id, **step):
        self.workflow["jobs"][job_id]["steps"].append(step)

    def add_job_shell_step(self, job_id, cmds, **step):
        """
        Adds a shell step to the specified job.
        cmds: str or list of str (commands)
        name: Optional step name
        shell: Shell to use (default: bash)
        """
        if isinstance(cmds, list):
            run_cmd = "\n".join(cmds)
        else:
            run_cmd = cmds
        # Use ruamel.yaml.scalarstring.LiteralScalarString for block style if multi-line
        from ruamel.yaml.scalarstring import LiteralScalarString

        if "\n" in run_cmd:
            step["run"] = LiteralScalarString(run_cmd)
        else:
            step["run"] = run_cmd
        self.add_job_step(job_id, **step)
        return self

    def add_cron_step(self, cron):
        self.workflow["on"]["schedule"] = [{"cron": cron}]
        return self

    def write(self, file_name="deploy.yml"):
        path = f".github/workflows/{file_name}"
        os.makedirs(os.path.dirname(path), exist_ok=True)

        comment = (
            "# Generated initially using github-actions-wizard (https://github.com/cmdr2/github-actions-wizard)\n\n"
        )
        with open(path, "w") as f:
            f.write(comment)
            yaml.dump(self.workflow, f)
        return path
