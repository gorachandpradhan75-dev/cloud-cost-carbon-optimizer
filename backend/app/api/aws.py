from fastapi import APIRouter

from app.services.aws_service import (
    get_ec2_instances,
    get_ec2_cpu_utilization,
)
from app.services.optimization_service import analyze_cpu_utilization
from app.services.cost_service import (
    estimate_instance_cost,
    calculate_potential_savings,
)
from app.services.carbon_service import (
    estimate_carbon_emissions,
    calculate_potential_carbon_reduction,
)


router = APIRouter(
    prefix="/aws",
    tags=["AWS"],
)


@router.get("/ec2/instances")
def list_ec2_instances():
    instances = get_ec2_instances()

    return {
        "count": len(instances),
        "instances": instances,
    }


@router.get("/ec2/metrics")
def list_ec2_metrics():
    instances = get_ec2_instances()

    metrics = []

    for instance in instances:
        if instance["state"] == "running":
            cpu_data = get_ec2_cpu_utilization(
                instance["instance_id"]
            )

            metrics.append(
                {
                    "instance_id": instance["instance_id"],
                    "instance_type": instance["instance_type"],
                    "state": instance["state"],
                    "average_cpu_24h": cpu_data["average_cpu"],
                    "datapoints": cpu_data["datapoints"],
                }
            )

    return {
        "count": len(metrics),
        "metrics": metrics,
    }


@router.get("/ec2/recommendations")
def get_ec2_recommendations():
    instances = get_ec2_instances()

    recommendations = []

    for instance in instances:
        # Analyze only running instances
        if instance["state"] != "running":
            continue

        # Get CloudWatch CPU utilization
        cpu_data = get_ec2_cpu_utilization(
            instance["instance_id"]
        )

        # Analyze instance utilization
        analysis = analyze_cpu_utilization(
            cpu_data["average_cpu"]
        )

        # Estimate instance cost
        cost = estimate_instance_cost(
            instance["instance_type"]
        )

        # Calculate potential cost savings
        potential_savings = calculate_potential_savings(
            cost["estimated_monthly_cost_usd"],
            analysis["optimization_status"],
        )

        # Estimate carbon emissions
        carbon = estimate_carbon_emissions(
            instance["instance_type"],
            region="us-east-1",
        )

        # Calculate potential carbon reduction
        potential_carbon_reduction = (
            calculate_potential_carbon_reduction(
                carbon["estimated_carbon_kg_monthly"],
                analysis["optimization_status"],
            )
        )

        recommendations.append(
            {
                "instance_id": instance["instance_id"],
                "instance_type": instance["instance_type"],
                "state": instance["state"],
                "average_cpu_24h": cpu_data["average_cpu"],
                "datapoints": cpu_data["datapoints"],

                # Optimization
                "optimization_status": analysis[
                    "optimization_status"
                ],
                "recommendation": analysis[
                    "recommendation"
                ],

                # Cost estimation
                "estimated_hourly_cost_usd": cost[
                    "hourly_cost_usd"
                ],
                "estimated_monthly_cost_usd": cost[
                    "estimated_monthly_cost_usd"
                ],
                "potential_monthly_savings_usd": (
                    potential_savings
                ),

                # Carbon estimation
                "estimated_energy_kwh_monthly": carbon[
                    "estimated_energy_kwh_monthly"
                ],
                "estimated_carbon_kg_monthly": carbon[
                    "estimated_carbon_kg_monthly"
                ],
                "potential_carbon_reduction_kg": (
                    potential_carbon_reduction
                ),
            }
        )

    # Calculate total estimated monthly cost
    total_monthly_cost = sum(
        item["estimated_monthly_cost_usd"] or 0
        for item in recommendations
    )

    # Calculate total potential cost savings
    total_potential_savings = sum(
        item["potential_monthly_savings_usd"] or 0
        for item in recommendations
    )

    # Calculate total estimated carbon emissions
    total_carbon = sum(
        item["estimated_carbon_kg_monthly"] or 0
        for item in recommendations
    )

    # Calculate total potential carbon reduction
    total_carbon_reduction = sum(
        item["potential_carbon_reduction_kg"] or 0
        for item in recommendations
    )

    return {
        "count": len(recommendations),

        "estimated_total_monthly_cost_usd": round(
            total_monthly_cost,
            2,
        ),

        "potential_total_monthly_savings_usd": round(
            total_potential_savings,
            2,
        ),

        "estimated_total_carbon_kg_monthly": round(
            total_carbon,
            3,
        ),

        "potential_total_carbon_reduction_kg": round(
            total_carbon_reduction,
            3,
        ),

        "recommendations": recommendations,
    }