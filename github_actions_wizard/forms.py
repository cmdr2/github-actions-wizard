from .cmd import get_default_github_repo


def ask_action_to_perform(workflow):
    has_build, has_test = workflow.has_job("build"), workflow.has_job("test")
    if has_build and has_test:
        return "deploy"

    options = [("deploy", "Add a deployment target")]
    if not has_build:
        options.append(("build", "Add a build step"))
    if not has_test:
        options.append(("test", "Add a test step"))

    return prompt_options("Select the action to perform:", options)


def ask_build_type():
    options = [
        ("dummy", "Dummy build step"),
        ("python_build", "Python wheel (.whl) and tar.gz package"),
        ("hugo", "Static site with Hugo"),
    ]
    return prompt_options("Select the type of build to perform:", options)


def ask_deployment_target():
    target = prompt_options(
        "Select deployment target:",
        [
            ("aws_s3", "AWS S3"),
            ("aws_lambda", "AWS Lambda"),
            ("pypi", "Publish to PyPI"),
            ("github_pages", "GitHub Pages"),
        ],
    )
    return target


def ask_aws_s3_path(is_file=False):
    example = "my-bucket-name/some/path/file.zip" if is_file else "my-bucket-name/some/path"

    s3_path = input(f"Enter AWS S3 path to deploy to (e.g., {example}): ").strip()
    return s3_path


def ask_aws_lambda_function_name():
    function_name = input("Enter the AWS Lambda function name to deploy to (e.g., my-function): ").strip()
    return function_name


def ask_deployment_trigger():
    trigger = prompt_options(
        "Select deployment trigger:",
        [
            ("push", "On branch push"),
            ("release", "On release creation"),
        ],
    )
    return trigger


def ask_upload_bundle_format():
    upload_format = prompt_options(
        "Select upload format:", [("zip", "Zip to a single file"), ("copy_all_files", "Copy all files directly")]
    )
    return upload_format


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
        if choice.isdigit() and 1 <= int(choice) <= len(options):
            selected = options[int(choice) - 1]
            return selected[0]
        print("Invalid choice. Try again.")
