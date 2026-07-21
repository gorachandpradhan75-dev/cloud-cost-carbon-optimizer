import boto3
from datetime import date, timedelta


def get_actual_aws_cost(days: int = 30):
    """
    Fetch actual AWS account-level cost from AWS Cost Explorer.

    The returned value uses the UnblendedCost metric.
    For an incomplete billing period, AWS may mark
    the result as estimated.
    """

    client = boto3.client(
        "ce",
        region_name="us-east-1",
    )

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    response = client.get_cost_and_usage(
        TimePeriod={
            "Start": start_date.isoformat(),
            "End": end_date.isoformat(),
        },
        Granularity="MONTHLY",
        Metrics=[
            "UnblendedCost"
        ],
    )

    results = response.get(
        "ResultsByTime",
        []
    )

    total_cost = 0.0
    estimated = False

    for result in results:
        amount = (
            result
            .get("Total", {})
            .get("UnblendedCost", {})
            .get("Amount", "0")
        )

        total_cost += float(amount)

        if result.get("Estimated", False):
            estimated = True

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days,
        },
        "metric": "UnblendedCost",
        "actual_cost_usd": round(
            total_cost,
            10,
        ),
        "estimated": estimated,
    }

def get_aws_cost_by_service(days: int = 30):
    """
    Fetch actual AWS cost grouped by AWS service
    using AWS Cost Explorer.
    """

    client = boto3.client(
        "ce",
        region_name="us-east-1",
    )

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    response = client.get_cost_and_usage(
        TimePeriod={
            "Start": start_date.isoformat(),
            "End": end_date.isoformat(),
        },
        Granularity="MONTHLY",
        Metrics=[
            "UnblendedCost"
        ],
        GroupBy=[
            {
                "Type": "DIMENSION",
                "Key": "SERVICE",
            }
        ],
    )

    service_costs = {}

    estimated = False

    for result in response.get(
        "ResultsByTime",
        []
    ):
        if result.get("Estimated", False):
            estimated = True

        for group in result.get(
            "Groups",
            []
        ):
            service_name = group[
                "Keys"
            ][0]

            amount = float(
                group[
                    "Metrics"
                ][
                    "UnblendedCost"
                ][
                    "Amount"
                ]
            )

            service_costs[
                service_name
            ] = (
                service_costs.get(
                    service_name,
                    0.0,
                )
                + amount
            )

    services = [
        {
            "service": service,
            "cost_usd": round(
                cost,
                10,
            ),
        }
        for service, cost
        in service_costs.items()
    ]

    # Highest cost first
    services.sort(
        key=lambda item: item[
            "cost_usd"
        ],
        reverse=True,
    )

    total_cost = sum(
        item["cost_usd"]
        for item in services
    )

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days,
        },
        "metric": "UnblendedCost",
        "total_cost_usd": round(
            total_cost,
            10,
        ),
        "estimated": estimated,
        "service_count": len(
            services
        ),
        "services": services,
    }

def get_actual_ec2_cost(days: int = 30):
    """
    Fetch actual EC2-related AWS costs from Cost Explorer.

    Separates:
    - Amazon EC2 - Compute
    - EC2 - Other
    """

    client = boto3.client(
        "ce",
        region_name="us-east-1",
    )

    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    response = client.get_cost_and_usage(
        TimePeriod={
            "Start": start_date.isoformat(),
            "End": end_date.isoformat(),
        },
        Granularity="MONTHLY",
        Metrics=[
            "UnblendedCost"
        ],
        GroupBy=[
            {
                "Type": "DIMENSION",
                "Key": "SERVICE",
            }
        ],
        Filter={
            "Dimensions": {
                "Key": "SERVICE",
                "Values": [
                    "Amazon Elastic Compute Cloud - Compute",
                    "EC2 - Other",
                ],
            }
        },
    )

    compute_cost = 0.0
    other_cost = 0.0
    estimated = False

    for result in response.get(
        "ResultsByTime",
        []
    ):
        if result.get("Estimated", False):
            estimated = True

        for group in result.get(
            "Groups",
            []
        ):
            service_name = group["Keys"][0]

            amount = float(
                group[
                    "Metrics"
                ][
                    "UnblendedCost"
                ][
                    "Amount"
                ]
            )

            if (
                service_name
                == "Amazon Elastic Compute Cloud - Compute"
            ):
                compute_cost += amount

            elif service_name == "EC2 - Other":
                other_cost += amount

    total_ec2_cost = (
        compute_cost
        + other_cost
    )

    return {
        "period": {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "days": days,
        },
        "metric": "UnblendedCost",
        "ec2_compute_cost_usd": round(
            compute_cost,
            10,
        ),
        "ec2_other_cost_usd": round(
            other_cost,
            10,
        ),
        "total_ec2_related_cost_usd": round(
            total_ec2_cost,
            10,
        ),
        "estimated": estimated,
    }