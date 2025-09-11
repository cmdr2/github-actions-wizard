import json
import time

from .cmd import run, run_capture, as_temp_file


def get_account_id():
    ensure_aws_cli_exists()

    print("Fetching your AWS Account ID...")

    output = run_capture(["aws", "sts", "get-caller-identity", "--query", "Account", "--output", "text"])
    return output.strip()


def create_policy_and_role_for_github_deploy(aws_account_id, gh_owner, gh_repo, gh_branch, iam_name, policy_doc):
    ensure_aws_cli_exists()

    trust_doc = _get_github_iam_trust_policy(aws_account_id, gh_owner, gh_repo, gh_branch)
    policy_arn = create_iam_policy(iam_name, policy_doc)
    role_arn = create_iam_role(iam_name, trust_doc)

    print("Waiting 5 seconds for IAM policy to propagate...")
    time.sleep(5)

    attach_iam_policy(iam_name, policy_arn)

    return role_arn


def create_policy_and_role_for_github_to_s3_deploy(
    role_name, aws_account_id, s3_path, gh_owner, gh_repo, gh_branch, is_zip_file
):
    s3_bucket_name = s3_path.split("/")[0]

    policy_doc = _get_s3_put_iam_policy(s3_bucket_name, s3_path, is_zip_file)

    role_arn = create_policy_and_role_for_github_deploy(
        aws_account_id, gh_owner, gh_repo, gh_branch, role_name, policy_doc
    )
    return role_arn


def create_policy_and_role_for_github_to_lambda_deploy(
    role_name, aws_account_id, function_name, gh_owner, gh_repo, gh_branch
):
    policy_doc = _get_lambda_update_iam_policy(function_name)

    role_arn = create_policy_and_role_for_github_deploy(
        aws_account_id, gh_owner, gh_repo, gh_branch, role_name, policy_doc
    )
    return role_arn


def create_iam_policy(policy_name, policy_file):
    output = run_capture(
        ["aws", "iam", "create-policy", "--policy-name", policy_name, "--policy-document", f"file://{policy_file}"]
    )
    policy_arn = json.loads(output)["Policy"]["Arn"]
    return policy_arn


def create_iam_role(role_name, trust_file):
    output = run_capture(
        ["aws", "iam", "create-role", "--role-name", role_name, "--assume-role-policy-document", f"file://{trust_file}"]
    )
    role_arn = json.loads(output)["Role"]["Arn"]
    return role_arn


def attach_iam_policy(role_name, policy_arn):
    run(["aws", "iam", "attach-role-policy", "--role-name", role_name, "--policy-arn", policy_arn])


def add_workflow_fetch_aws_credentials_step(workflow, job_id, role_env_var, aws_region="us-east-1"):
    step = {
        "name": "Configure AWS credentials",
        "uses": "aws-actions/configure-aws-credentials@v4",
        "with": {
            "role-to-assume": "${{ vars." + role_env_var + " }}",
            "aws-region": aws_region,
        },
    }
    workflow.add_job_step(job_id, **step)
    return workflow


def add_workflow_s3_cp_step(workflow, job_id, local_path, s3_path, acl="public-read"):
    cmd = f"aws s3 cp '{local_path}' 's3://{s3_path}' --acl {acl}"
    workflow.add_job_shell_step(job_id, cmd, name="Upload File to S3")
    return workflow


def add_workflow_s3_sync_step(workflow, job_id, local_path, s3_path):
    cmd = f"aws s3 sync '{local_path}' 's3://{s3_path}' --acl public-read"
    workflow.add_job_shell_step(job_id, cmd, name="Sync Files to S3")
    return workflow


def add_workflow_lambda_deploy_step(workflow, job_id, function_name, zip_file):
    cmd = f"aws lambda update-function-code --function-name '{function_name}' --zip-file 'fileb://{zip_file}' --query LastUpdateStatus"
    workflow.add_job_shell_step(job_id, cmd, name="Deploy to Lambda")
    return workflow


def _get_s3_put_iam_policy(s3_bucket_name, s3_path, is_zip_file):
    res_path = s3_path if is_zip_file else f"{s3_path}/*"
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": ["s3:PutObject", "s3:PutObjectAcl"],
                "Effect": "Allow",
                "Resource": [f"arn:aws:s3:::{res_path}"],
            }
        ],
    }
    if not is_zip_file:  # needs this for 'aws s3 sync'
        policy_doc["Statement"].append(
            {
                "Action": ["s3:ListBucket"],
                "Effect": "Allow",
                "Resource": [f"arn:aws:s3:::{s3_bucket_name}"],
            }
        )
    return as_temp_file(policy_doc, suffix="-s3-put-policy.json")


def _get_lambda_update_iam_policy(function_name):
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Action": ["lambda:UpdateFunctionCode", "lambda:GetFunctionConfiguration"],
                "Effect": "Allow",
                "Resource": [f"arn:aws:lambda:*:*:function:{function_name}"],
            }
        ],
    }
    return as_temp_file(policy_doc, suffix="-lambda-policy.json")


def _get_github_iam_trust_policy(aws_account_id, gh_owner, gh_repo, gh_branch):
    sub = f"repo:{gh_owner}/{gh_repo}:ref:refs"
    condition = {
        "StringEquals": {
            "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
        }
    }
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Federated": f"arn:aws:iam::{aws_account_id}:oidc-provider/token.actions.githubusercontent.com"
                },
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": condition,
            }
        ],
    }
    if gh_branch is None:  # is a release
        condition["StringLike"] = {}
        condition["StringLike"]["token.actions.githubusercontent.com:sub"] = f"{sub}/tags/*"
    else:
        condition["StringEquals"]["token.actions.githubusercontent.com:sub"] = f"{sub}/heads/{gh_branch}"

    return as_temp_file(policy_doc, suffix="-github-trust-policy.json")


def ensure_aws_cli_exists():
    try:
        run_capture(["aws", "--version"])
    except:
        print("AWS CLI not found or not working. Please install/configure AWS CLI and try again.")
        exit(1)
