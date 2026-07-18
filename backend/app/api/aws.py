from fastapi import APIRouter

from app.core.database import SessionLocal
from app.models.optimization_scan import OptimizationScan

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


def generate_ec2_recommendations():
    """
    Fetch running EC2 instances and generate cost,
    utilization, and carbon optimization recommendations.
    """

    instances = get_ec2_instances()
    recommendations = []

    for instance in instances:
        if instance["state"] != "running":
            continue

        # Get CloudWatch CPU utilization
        cpu_data = get_ec2_cpu_utilization(
            instance["instance_id"]
        )

        # Analyze CPU utilization
        analysis = analyze_cpu_utilization(
            cpu_data["average_cpu"]
        )

        # Estimate EC2 cost
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
                "optimization_status": analysis[
                    "optimization_status"
                ],
                "recommendation": analysis[
                    "recommendation"
                ],
                "estimated_hourly_cost_usd": cost[
                    "hourly_cost_usd"
                ],
                "estimated_monthly_cost_usd": cost[
                    "estimated_monthly_cost_usd"
                ],
                "potential_monthly_savings_usd": (
                    potential_savings
                ),
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

    return recommendations


def build_recommendation_response(recommendations):
    """
    Build API response and calculate overall totals.
    """

    total_monthly_cost = sum(
        item["estimated_monthly_cost_usd"] or 0
        for item in recommendations
    )

    total_potential_savings = sum(
        item["potential_monthly_savings_usd"] or 0
        for item in recommendations
    )

    total_carbon = sum(
        item["estimated_carbon_kg_monthly"] or 0
        for item in recommendations
    )

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
                    "average_cpu_24h": cpu_data[
                        "average_cpu"
                    ],
                    "datapoints": cpu_data["datapoints"],
                }
            )

    return {
        "count": len(metrics),
        "metrics": metrics,
    }


@router.get("/ec2/recommendations")
def get_ec2_recommendations():
    """
    Generate current recommendations without
    saving anything to the database.
    """

    recommendations = generate_ec2_recommendations()

    return build_recommendation_response(
        recommendations
    )


@router.post("/ec2/scan")
def run_ec2_optimization_scan():
    """
    Run a new optimization scan and save
    the results to PostgreSQL.
    """

    recommendations = generate_ec2_recommendations()

    db = SessionLocal()

    try:
        for item in recommendations:
            scan = OptimizationScan(
                instance_id=item["instance_id"],
                instance_type=item["instance_type"],
                average_cpu_24h=item[
                    "average_cpu_24h"
                ],
                optimization_status=item[
                    "optimization_status"
                ],
                estimated_monthly_cost_usd=item[
                    "estimated_monthly_cost_usd"
                ],
                potential_monthly_savings_usd=item[
                    "potential_monthly_savings_usd"
                ],
                estimated_energy_kwh_monthly=item[
                    "estimated_energy_kwh_monthly"
                ],
                estimated_carbon_kg_monthly=item[
                    "estimated_carbon_kg_monthly"
                ],
                potential_carbon_reduction_kg=item[
                    "potential_carbon_reduction_kg"
                ],
            )

            db.add(scan)

        db.commit()

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()

    response = build_recommendation_response(
        recommendations
    )

    response["message"] = (
        "Optimization scan completed and saved successfully."
    )

    return response


@router.get("/ec2/history")
def get_optimization_history():
    """
    Return the latest 100 saved optimization records.
    """

    db = SessionLocal()

    try:
        scans = (
            db.query(OptimizationScan)
            .order_by(
                OptimizationScan.created_at.desc()
            )
            .limit(100)
            .all()
        )

        history = []

        for scan in scans:
            history.append(
                {
                    "id": scan.id,
                    "instance_id": scan.instance_id,
                    "instance_type": scan.instance_type,
                    "average_cpu_24h": (
                        scan.average_cpu_24h
                    ),
                    "optimization_status": (
                        scan.optimization_status
                    ),
                    "estimated_monthly_cost_usd": (
                        scan.estimated_monthly_cost_usd
                    ),
                    "potential_monthly_savings_usd": (
                        scan.potential_monthly_savings_usd
                    ),
                    "estimated_energy_kwh_monthly": (
                        scan.estimated_energy_kwh_monthly
                    ),
                    "estimated_carbon_kg_monthly": (
                        scan.estimated_carbon_kg_monthly
                    ),
                    "potential_carbon_reduction_kg": (
                        scan.potential_carbon_reduction_kg
                    ),
                    "created_at": scan.created_at,
                }
            )

        return {
            "count": len(history),
            "history": history,
        }

    finally:
        db.close()
@router.get("/dashboard/summary")
def get_dashboard_summary():
    """
    Generate a summary of current EC2 infrastructure,
    cost, savings, and carbon optimization metrics.
    """

    recommendations = generate_ec2_recommendations()

    total_instances = len(recommendations)

    running_instances = sum(
        1
        for item in recommendations
        if item["state"] == "running"
    )

    idle_instances = sum(
        1
        for item in recommendations
        if item["optimization_status"] == "IDLE"
    )

    underutilized_instances = sum(
        1
        for item in recommendations
        if item["optimization_status"] == "UNDERUTILIZED"
    )

    optimized_instances = sum(
        1
        for item in recommendations
        if item["optimization_status"] == "OPTIMIZED"
    )

    total_monthly_cost = sum(
        item["estimated_monthly_cost_usd"] or 0
        for item in recommendations
    )

    total_potential_savings = sum(
        item["potential_monthly_savings_usd"] or 0
        for item in recommendations
    )

    total_carbon = sum(
        item["estimated_carbon_kg_monthly"] or 0
        for item in recommendations
    )

    total_carbon_reduction = sum(
        item["potential_carbon_reduction_kg"] or 0
        for item in recommendations
    )

    return {
        "total_instances": total_instances,
        "running_instances": running_instances,
        "idle_instances": idle_instances,
        "underutilized_instances": underutilized_instances,
        "optimized_instances": optimized_instances,
        "estimated_monthly_cost_usd": round(
            total_monthly_cost,
            2,
        ),
        "potential_monthly_savings_usd": round(
            total_potential_savings,
            2,
        ),
        "estimated_carbon_kg_monthly": round(
            total_carbon,
            3,
        ),
        "potential_carbon_reduction_kg": round(
            total_carbon_reduction,
            3,
        ),
    }