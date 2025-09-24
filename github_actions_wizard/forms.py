import contextlib

from .cmd import get_default_github_repo


def ask_workflow_template(workflow):
    if workflow.get_job_ids():  # workflow already has jobs, can't use a template
        return "custom"

    options = [
        ("python_package", "Python package - build and publish to PyPI"),
        ("node_package", "npm package - build and publish to npm"),
        ("static_hugo_website", "Static website - build and deploy to GitHub Pages"),
        ("static_s3_website", "Static website - build and deploy to AWS S3"),
        ("static_cloudflare_pages", "Static website - build and deploy to Cloudflare Pages"),
        ("lambda_deploy", "AWS Lambda - build and deploy to AWS Lambda"),
        ("itch_io", "itch.io - build and publish to itch.io"),
        ("pytest_ci", "Pytest CI - run tests with pytest on push and pull request (test-only)"),
        ("custom", "Custom workflow"),
    ]
    return prompt_options("Select a workflow template to start with:", options)


def ask_action_to_perform(workflow):
    has_build, has_test = workflow.has_job("build"), workflow.has_job("test")
    has_deploy = any(job_id.startswith("deploy") for job_id in workflow.get_job_ids())

    options = [("deploy", "Add a deployment job")]
    if not has_build:
        options.append(("build", "Add a build job"))
    if not has_test:
        options.append(("test", "Add a test job"))

    if has_deploy:
        options.append(("post_deploy", "Add a post-deployment job"))

    options.append(("quit", "Save and exit"))

    return prompt_options("Select the action to perform:", options)


def ask_build_type():
    options = [
        ("copy", "Copy all files (excluding .git and .github)"),
        ("zip", "Zip to a single file"),
        ("python_build", "Python wheel (.whl) and tar.gz package"),
        ("hugo", "Static site with Hugo"),
    ]
    return prompt_options("Select the type of build to perform:", options)


def ask_test_type():
    options = [
        ("pytest", "Run tests with pytest"),
        ("custom", "Custom test command"),
    ]
    return prompt_options("Select the type of test to perform:", options)


def ask_deploy_target():
    target = prompt_options(
        "Select deployment target:",
        [
            ("aws_s3", "AWS S3"),
            ("aws_lambda", "AWS Lambda"),
            ("pypi", "Publish to PyPI"),
            ("npm", "Publish to npm"),
            ("github_pages", "GitHub Pages"),
            ("cloudflare_pages", "Cloudflare Pages"),
            ("itch_io", "Publish to itch.io"),
            ("gh_release", "Add to GitHub Release"),
        ],
    )
    return target


def ask_post_deploy_type():
    options = [
        ("http_call", "Call an HTTP endpoint (e.g. to test a URL, or trigger a webhook)"),
        ("custom", "Custom command"),
    ]
    return prompt_options("Select the type of post-deployment action to perform:", options)


def ask_workflow_file_name(default_filename="ci_workflow.yml"):
    file_name = prompt_entry("Enter workflow file name", default=default_filename)
    if not file_name.endswith(".yml") and not file_name.endswith(".yaml"):
        file_name += ".yml"
    return file_name


def ask_aws_s3_path():
    example = "my-bucket-name/some/path (or path/to/file.zip)"

    return prompt_entry(f"Enter AWS S3 path to deploy to (e.g., {example})")


def ask_aws_lambda_function_name():
    return prompt_entry("Enter your AWS Lambda function name (e.g., my-function)")


def ask_itch_io_user_name():
    return prompt_entry("Enter your itch.io user name (e.g., freebirdxr)")


def ask_itch_io_project_name():
    return prompt_entry("Enter your itch.io project name (e.g., freebird)")


def ask_s3_sync_command():
    prompt = "Choose the copy command for AWS S3 deployment"
    options = [
        (
            "s3_sync_changes",
            "s3-sync-changes - (recommended) only uploads changed files. Adds a workflow dependency on https://github.com/cmdr2/s3-sync-changes",
        ),
        (
            "aws_s3_copy",
            "'aws s3 cp' - will upload every file on every deployment. No extra dependencies.",
        ),
    ]
    return prompt_options(prompt, options)


def ask_iam_prefix(default):
    return prompt_entry("Enter the IAM role prefix to use", default=default)


def ask_deploy_trigger():
    trigger = prompt_options(
        "Select deployment trigger:",
        [
            ("push", "On branch push"),
            ("release", "On release creation"),
        ],
    )
    return trigger


def ask_parent_deploy_job_id(job_ids):
    if not job_ids:
        raise ValueError("No jobs available to select as parent deploy job.")
    job_options = [(job_id, job_id) for job_id in job_ids if job_id.startswith("deploy")]
    return prompt_options("Select the parent deploy job for this post-deployment action:", job_options)


def ask_github_repo_name():
    default_repo = get_default_github_repo()
    prompt_str = "Enter GitHub repo"
    if default_repo:
        github_repo = prompt_entry(prompt_str, default=default_repo)
    else:
        github_repo = prompt_entry(f"{prompt_str} (e.g., cmdr2/carbon, or full URL)")

    if github_repo.startswith("http://") or github_repo.startswith("https://"):
        parts = github_repo.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1].replace(".git", "")
    else:
        owner, repo = github_repo.split("/")

    return owner, repo


def ask_github_branch_name(help_text="will react to pushes on this branch"):
    return prompt_entry(f"Enter branch name ({help_text})", default="main")


def ask_http_endpoint_url():
    return prompt_entry("Enter the HTTP endpoint URL to call (e.g., https://example.com/webhook)")


def ask_http_method():
    options = [
        ("GET", "GET"),
        ("POST", "POST"),
    ]
    return prompt_options("Select the HTTP method to use:", options)


def ask_http_json_body():
    return prompt_entry("Enter the HTTP request JSON body (for POST requests)", default="{}")


def ask_http_response_string_to_check():
    return prompt_entry("Enter the string to check in the HTTP response. Leave blank to skip this check.", default="")


def ask_cloudflare_pages_project_name():
    return prompt_entry("Enter your Cloudflare Pages project name (e.g., my-cloudflare-pages-project)")


def prompt_entry(prompt, **kwargs):
    has_default = "default" in kwargs
    prompt = prompt.strip()
    prompt = prompt if not has_default else f"{prompt} [default={kwargs['default']}]"
    while True:
        response = input(f"{prompt}: ").strip()
        if not response and not has_default:
            print("This field is required. Please enter a value.")
            continue
        print("")
        return response or kwargs["default"]


def prompt_options(prompt, options):
    """
    Show a prompt with numbered options and return the selected option.
    Options are a list of (id, label) tuples.
    Return the selected id.
    """
    print(prompt)
    for i, opt in enumerate(options, 1):
        label = opt[1]
        print(f"{i}. {label}")
    while True:
        choice = input("Enter option number: ").strip()
        print("")
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            selected = options[int(choice) - 1]
            return selected[0]
        print("Invalid choice. Try again.")


def prompt_yes_no(prompt, default="yes"):
    """
    Prompt the user for a yes/no question and return True for yes and False for no.
    Default is "yes" or "no".
    """
    prompt = prompt.strip()
    default = default.lower()
    if default not in ("yes", "no"):
        raise ValueError("Default must be 'yes' or 'no'")
    prompt_suffix = " [Y/n]: " if default == "yes" else " [y/N]: "
    while True:
        choice = input(f"{prompt}{prompt_suffix}").strip().lower()
        if not choice:
            choice = default
        if choice in ("y", "yes"):
            print("")
            return True
        if choice in ("n", "no"):
            print("")
            return False
        print("Invalid choice. Please enter 'y' or 'n'.")


@contextlib.contextmanager
def override_ask_functions(**answers):
    """
    Context manager to override ask_ functions in this module with canned answers.
    Usage:
        with override_ask_functions(build_type="python_build", github_branch_name="dev"):
            ...
    """
    import sys

    module = sys.modules[__name__]
    originals = {}
    try:
        for key, canned in answers.items():
            func_name = f"ask_{key}"
            if hasattr(module, func_name):
                originals[func_name] = getattr(module, func_name)

                def make_override(canned):
                    return lambda *a, **kw: canned

                setattr(module, func_name, make_override(canned))
        yield
    finally:
        for name, func in originals.items():
            setattr(module, name, func)
