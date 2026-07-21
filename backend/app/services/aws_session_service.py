import boto3


def get_default_aws_session():
    """
    Create a boto3 session using the credentials
    configured in the local AWS environment.

    This represents the central/default AWS account.
    """

    return boto3.Session()


def get_aws_account_identity(session=None):
    """
    Return the AWS account and ARN associated
    with the supplied boto3 session.
    """

    if session is None:
        session = get_default_aws_session()

    sts = session.client("sts")

    identity = sts.get_caller_identity()

    return {
        "account_id": identity["Account"],
        "arn": identity["Arn"],
    }

def assume_role_session(
    role_arn: str,
    session_name: str = "cloud-cost-optimizer-research",
):
    """
    Assume a cross-account IAM role and return
    a temporary authenticated boto3 session.

    No permanent access keys from participant
    accounts are required.
    """

    sts = boto3.client("sts")

    response = sts.assume_role(
        RoleArn=role_arn,
        RoleSessionName=session_name,
    )

    credentials = response["Credentials"]

    session = boto3.Session(
        aws_access_key_id=credentials["AccessKeyId"],
        aws_secret_access_key=credentials["SecretAccessKey"],
        aws_session_token=credentials["SessionToken"],
    )

    return session