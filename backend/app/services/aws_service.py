import boto3
from datetime import datetime, timedelta, timezone


AWS_REGION = "us-east-1"


def get_ec2_instances():
    ec2 = boto3.client("ec2", region_name=AWS_REGION)

    response = ec2.describe_instances()

    instances = []

    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instances.append(
                {
                    "instance_id": instance["InstanceId"],
                    "instance_type": instance["InstanceType"],
                    "state": instance["State"]["Name"],
                    "availability_zone": instance["Placement"]["AvailabilityZone"],
                    "launch_time": instance["LaunchTime"],
                }
            )

    return instances


def get_ec2_cpu_utilization(instance_id: str):
    cloudwatch = boto3.client(
        "cloudwatch",
        region_name=AWS_REGION,
    )

    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(hours=24)

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
        point["Average"] for point in datapoints
    ) / len(datapoints)

    return {
        "instance_id": instance_id,
        "average_cpu": round(average_cpu, 2),
        "datapoints": len(datapoints),
    }