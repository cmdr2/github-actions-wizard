import contextlib

from .cmd import get_default_github_repo


def ask_workflow_template(workflow):
    if workflow.get_jobs_ids():  # workflow already has jobs, can't use a template
        return "custom"

    options = [
        ("python_package", "Python package - build and publish to PyPI"),
        ("static_hugo_website", "Static Hugo website - build and deploy to GitHub Pages"),
        ("static_s3_website", "Static S3 website - build and deploy to AWS S3"),
        ("lambda_deploy", "AWS Lambda - build and deploy to AWS Lambda"),
        ("itch_io", "itch.io - build and publish to itch.io"),
        ("pytest_ci", "Pytest CI - run tests with pytest on push and pull request (test-only)"),
        ("custom", "Custom workflow"),
    ]
    return prompt_options("Select a workflow template to start with:", options)


def ask_action_to_perform(workflow):
    has_build, has_test = workflow.has_job("build"), workflow.has_job("test")

    options = [("deploy", "Add a deployment target")]
    if not has_build:
        options.append(("build", "Add a build step"))
    if not has_test:
        options.append(("test", "Add a test step"))

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
            ("github_pages", "GitHub Pages"),
            ("itch_io", "Publish to itch.io"),
            ("gh_release", "Add to GitHub Release"),
        ],
    )
    return target


def ask_workflow_file_name(default_filename="ci_workflow.yml"):
    file_name = input(f"Save as workflow file name [default={default_filename}]: ").strip()
    file_name = file_name or default_filename
    if not file_name.endswith(".yml") and not file_name.endswith(".yaml"):
        file_name += ".yml"
    return file_name


def ask_aws_s3_path():
    example = "my-bucket-name/some/path (or path/to/file.zip)"

    s3_path = input(f"Enter AWS S3 path to deploy to (e.g., {example}): ").strip()
    return s3_path


def ask_aws_lambda_function_name():
    function_name = input("Enter the AWS Lambda function name to deploy to (e.g., my-function): ").strip()
    return function_name


def ask_itch_io_user_name():
    user_name = input("Enter your itch.io user name (e.g., freebirdxr): ").strip()
    return user_name


def ask_itch_io_project_name():
    project_name = input("Enter your itch.io project name (e.g., freebird): ").strip()
    return project_name


def ask_deploy_trigger():
    trigger = prompt_options(
        "Select deployment trigger:",
        [
            ("push", "On branch push"),
            ("release", "On release creation"),
        ],
    )
    return trigger


def ask_github_repo_name():
    default_repo = get_default_github_repo()
    prompt_str = "Enter GitHub repo"
    if default_repo:
        prompt_str += f" [default={default_repo}]"
    else:
        prompt_str += " (e.g., cmdr2/carbon, or full URL)"
    github_repo = input(f"{prompt_str}: ").strip() or default_repo

    if not github_repo:
        print("No GitHub repo provided.")
        exit(1)
        return None, None

    if github_repo.startswith("http://") or github_repo.startswith("https://"):
        parts = github_repo.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1].replace(".git", "")
    else:
        owner, repo = github_repo.split("/")

    return owner, repo


def ask_github_branch_name(help_text="will react to pushes on this branch"):
    branch = input(f"Enter branch name ({help_text}) [default=main]: ").strip()
    return branch or "main"


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
