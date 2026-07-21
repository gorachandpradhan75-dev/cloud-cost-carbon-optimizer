import boto3
from datetime import datetime, timedelta, timezone


AWS_REGION = "us-east-1"


def get_ec2_instances(
    session=None,
    region_name=AWS_REGION,
):
    """
    Fetch EC2 instances using either the default
    AWS credentials or a supplied assumed-role session.
    """

    if session is None:
        session = boto3.Session()

    ec2 = session.client(
        "ec2",
        region_name=region_name,
    )

    response = ec2.describe_instances()

    instances = []

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instances.append(
                {
                    "instance_id": instance["InstanceId"],
                    "instance_type": instance["InstanceType"],
                    "state": instance["State"]["Name"],
                    "availability_zone": instance[
                        "Placement"
                    ]["AvailabilityZone"],
                    "launch_time": instance["LaunchTime"],
                }
            )

    return instances


def _get_cpu_metric(
    instance_id: str,
    start_time: datetime,
    end_time: datetime,
    period: int,
):
    """
    Internal helper function to fetch average EC2 CPU
    utilization from AWS CloudWatch.
    """

    cloudwatch = boto3.client(
        "cloudwatch",
        region_name=AWS_REGION,
    )

    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[
            {
                "Name": "InstanceId",
                "Value": instance_id,
            }
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=period,
        Statistics=["Average"],
    )

    datapoints = response.get(
        "Datapoints",
        [],
    )

    if not datapoints:
        return {
            "average_cpu": None,
            "datapoints": 0,
        }

    average_cpu = sum(
        point["Average"]
        for point in datapoints
    ) / len(datapoints)

    return {
        "average_cpu": round(
            average_cpu,
            2,
        ),
        "datapoints": len(
            datapoints
        ),
    }


def get_ec2_cpu_utilization(
    instance_id: str,
    hours: int = 24,
    session=None,
    region_name=AWS_REGION,
):
    if session is None:
        session = boto3.Session()

    cloudwatch = session.client(
        "cloudwatch",
        region_name=region_name,
    )

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=hours)

    response = cloudwatch.get_metric_statistics(
        Namespace="AWS/EC2",
        MetricName="CPUUtilization",
        Dimensions=[
            {
                "Name": "InstanceId",
                "Value": instance_id,
            }
        ],
        StartTime=start_time,
        EndTime=end_time,
        Period=3600,
        Statistics=["Average"],
    )

    datapoints = response.get("Datapoints", [])

    if not datapoints:
        return {
            "instance_id": instance_id,
            "average_cpu": None,
            "datapoints": 0,
        }

    average_cpu = sum(
        point["Average"]
        for point in datapoints
    ) / len(datapoints)

    return {
        "instance_id": instance_id,
        "average_cpu": round(average_cpu, 2),
        "datapoints": len(datapoints),
    }


def get_ec2_cpu_utilization_multi_period(
    instance_id: str,
):
    """
    Fetch EC2 CPU utilization for multiple
    research analysis periods:

    - Last 24 hours
    - Last 7 days
    - Last 30 days
    """

    end_time = datetime.now(
        timezone.utc
    )

    # -------------------------
    # 24 Hour CPU Utilization
    # -------------------------

    cpu_24h = _get_cpu_metric(
        instance_id=instance_id,
        start_time=end_time - timedelta(
            hours=24
        ),
        end_time=end_time,
        period=3600,
    )

    # -------------------------
    # 7 Day CPU Utilization
    # -------------------------

    cpu_7d = _get_cpu_metric(
        instance_id=instance_id,
        start_time=end_time - timedelta(
            days=7
        ),
        end_time=end_time,
        period=3600,
    )

    # -------------------------
    # 30 Day CPU Utilization
    # -------------------------

    cpu_30d = _get_cpu_metric(
        instance_id=instance_id,
        start_time=end_time - timedelta(
            days=30
        ),
        end_time=end_time,
        period=86400,
    )

    return {
        "instance_id": instance_id,

        "cpu_24h": {
            "average_cpu": cpu_24h[
                "average_cpu"
            ],
            "datapoints": cpu_24h[
                "datapoints"
            ],
        },

        "cpu_7d": {
            "average_cpu": cpu_7d[
                "average_cpu"
            ],
            "datapoints": cpu_7d[
                "datapoints"
            ],
        },

        "cpu_30d": {
            "average_cpu": cpu_30d[
                "average_cpu"
            ],
            "datapoints": cpu_30d[
                "datapoints"
            ],
        },
    }