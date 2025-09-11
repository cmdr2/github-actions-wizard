from .. import forms


def add_post_deploy_job(workflow):
    post_deploy_type = forms.ask_post_deploy_type()
    parent_job_id = forms.ask_parent_deploy_job_id(workflow.get_job_ids())

    job_id = f"post_deploy_{post_deploy_type}"
    workflow.add_job(job_id, needs=parent_job_id)

    if post_deploy_type == "http_call":
        add_http_call_post_deploy_steps(workflow, job_id)
    elif post_deploy_type == "custom":
        add_custom_command_post_deploy_steps(workflow, job_id)

    return job_id


def add_http_call_post_deploy_steps(workflow, job_id):
    url = forms.ask_http_endpoint_url()
    method = forms.ask_http_method()

    cmd = f"curl -L -X {method} '{url}' -o response.json -w 'Response code: %{{response_code}}\\n'"
    if method == "POST":
        body = forms.ask_http_json_body()
        cmd += f" -H \"Content-Type: application/json\" -d '{body}'"

    workflow.add_job_shell_step(
        job_id,
        cmd,
        name="Call HTTP endpoint",
    )

    response_check = forms.ask_http_response_string_to_check()
    if response_check:
        check_cmd = [
            f'echo "Checking response for string: {response_check}"',
            f'if grep -q "{response_check}" response.json; then',
            '  echo "Response check passed"',
            "else",
            '  echo "Response check failed!"',
            '  echo "Got response:"',
            "  cat response.json",
            "  exit 1",
            "fi",
        ]
        workflow.add_job_shell_step(
            job_id,
            check_cmd,
            name="Check HTTP response",
        )


def add_custom_command_post_deploy_steps(workflow, job_id):
    workflow.add_job_shell_step(
        job_id,
        ["echo 'Add your custom commands here'", "echo 'For example, notify a service, check the deployment, etc.'"],
        name="Custom post-deployment commands",
    )
