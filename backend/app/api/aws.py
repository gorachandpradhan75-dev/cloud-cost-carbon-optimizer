from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import APIRouter, HTTPException
from app.core.database import SessionLocal
from app.models.aws_account import AWSAccount
from app.services.aws_session_service import (
    get_aws_account_identity,
    assume_role_session,
)
from datetime import date, timedelta
from app.services.optimization_service import analyze_multi_period_cpu
from app.core.database import SessionLocal
from app.models.optimization_scan import OptimizationScan
from app.services.cost_explorer_service import (
    get_actual_aws_cost,
    get_aws_cost_by_service,
    get_actual_ec2_cost,
)
from app.services.aws_service import (
    get_ec2_instances,
    get_ec2_cpu_utilization,
    get_ec2_cpu_utilization_multi_period,
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

from app.services.optimization_service import (
    analyze_cpu_utilization,
    analyze_multi_period_cpu,
)
router = APIRouter(
    prefix="/aws",
    tags=["AWS"],
)
class AWSAccountCreate(BaseModel):
    participant_id: str
    account_alias: str | None = None
    role_arn: str
    default_region: str = "us-east-1"

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
@router.get("/ec2/metrics/multi-period")
def list_ec2_multi_period_metrics():
    instances = get_ec2_instances()

    metrics = []

    for instance in instances:
        if instance["state"] != "running":
            continue

        cpu_data = get_ec2_cpu_utilization_multi_period(
            instance["instance_id"]
        )

        metrics.append(
            {
                "instance_id": instance["instance_id"],
                "instance_type": instance["instance_type"],
                "state": instance["state"],
                "availability_zone": instance[
                    "availability_zone"
                ],
                "cpu_24h": cpu_data["cpu_24h"],
                "cpu_7d": cpu_data["cpu_7d"],
                "cpu_30d": cpu_data["cpu_30d"],
            }
        )

    return {
        "count": len(metrics),
        "analysis_periods": [
            "24_hours",
            "7_days",
            "30_days",
        ],
        "metrics": metrics,
    }

@router.get("/ec2/recommendations/multi-period")
def get_ec2_multi_period_recommendations():
    """
    Generate Research v2 optimization recommendations
    using 24-hour, 7-day, and 30-day CloudWatch CPU data.
    """

    instances = get_ec2_instances()

    recommendations = []

    for instance in instances:
        if instance["state"] != "running":
            continue

        # Fetch real multi-period CloudWatch CPU metrics
        cpu_data = get_ec2_cpu_utilization_multi_period(
            instance["instance_id"]
        )

        cpu_24h = cpu_data["cpu_24h"]["average_cpu"]
        cpu_7d = cpu_data["cpu_7d"]["average_cpu"]
        cpu_30d = cpu_data["cpu_30d"]["average_cpu"]

        # Research v2 multi-period optimization analysis
        analysis = analyze_multi_period_cpu(
            cpu_24h=cpu_24h,
            cpu_7d=cpu_7d,
            cpu_30d=cpu_30d,
        )

        recommendations.append(
            {
                "instance_id": instance["instance_id"],
                "instance_type": instance["instance_type"],
                "state": instance["state"],
                "availability_zone": instance[
                    "availability_zone"
                ],

                "cpu_utilization": {
                    "24_hours": cpu_24h,
                    "7_days": cpu_7d,
                    "30_days": cpu_30d,
                },

                "optimization_status": analysis[
                    "optimization_status"
                ],
                "confidence": analysis[
                    "confidence"
                ],
                "recommendation": analysis[
                    "recommendation"
                ],
            }
        )

    return {
        "count": len(recommendations),
        "analysis_method": "multi_period_cpu_analysis",
        "recommendations": recommendations,
    }

@router.get("/cost/actual")
def get_aws_actual_cost(days: int = 30):
    """
    Fetch actual AWS account-level historical cost
    from AWS Cost Explorer.
    """

    cost_data = get_actual_aws_cost(
        days=days
    )

    return {
        "source": "AWS Cost Explorer",
        "cost_data": cost_data,
    }

@router.get("/cost/by-service")
def get_aws_service_costs(days: int = 30):
    """
    Fetch actual AWS cost grouped by AWS service
    using AWS Cost Explorer.
    """

    cost_data = get_aws_cost_by_service(
        days=days
    )

    return {
        "source": "AWS Cost Explorer",
        "cost_data": cost_data,
    }

@router.get("/cost/ec2")
def get_aws_ec2_actual_cost(days: int = 30):
    """
    Fetch actual EC2-related cost
    from AWS Cost Explorer.
    """

    cost_data = get_actual_ec2_cost(
        days=days
    )

    return {
        "source": "AWS Cost Explorer",
        "scope": "EC2",
        "cost_data": cost_data,
    }

@router.get("/cost/comparison")
def get_cost_comparison(days: int = 30):
    """
    Compare actual AWS EC2-related billed cost from Cost Explorer
    with the optimization model's estimated monthly cost
    and potential monthly savings.

    Note:
    Actual billed cost and projected monthly cost represent
    different cost concepts and should not be treated as
    directly equivalent values.
    """

    # Fetch actual EC2-related billing data from AWS Cost Explorer
    actual_cost_data = get_actual_ec2_cost(
        days=days
    )

    # Generate current EC2 optimization recommendations
    recommendations = generate_ec2_recommendations()

    # Calculate projected monthly infrastructure cost
    estimated_monthly_cost = sum(
        item["estimated_monthly_cost_usd"] or 0
        for item in recommendations
    )

    # Calculate potential monthly savings
    potential_monthly_savings = sum(
        item["potential_monthly_savings_usd"] or 0
        for item in recommendations
    )

    return {
        "actual_billing": {
            "source": "AWS Cost Explorer",
            "metric": actual_cost_data["metric"],
            "period": actual_cost_data["period"],
            "ec2_compute_cost_usd": actual_cost_data[
                "ec2_compute_cost_usd"
            ],
            "ec2_other_cost_usd": actual_cost_data[
                "ec2_other_cost_usd"
            ],
            "actual_ec2_related_cost_usd": actual_cost_data[
                "total_ec2_related_cost_usd"
            ],
            "estimated": actual_cost_data["estimated"],
        },

        "optimization_model": {
            "source": "Cloud Cost Optimizer Pricing Model",
            "instance_count": len(recommendations),
            "estimated_monthly_cost_usd": round(
                estimated_monthly_cost,
                2,
            ),
            "potential_monthly_savings_usd": round(
                potential_monthly_savings,
                2,
            ),
        },

        "analysis": {
            "actual_cost_basis": (
                "AWS Cost Explorer UnblendedCost"
            ),
            "estimated_cost_basis": (
                "Projected EC2 monthly cost using the "
                "optimizer pricing model"
            ),
            "savings_basis": (
                "Potential savings calculated from "
                "resource utilization recommendations"
            ),
            "note": (
                "Actual billed cost and projected monthly cost "
                "represent different cost concepts and should "
                "not be treated as directly equivalent values."
            ),
        },
    }

@router.get("/accounts/current")
def get_current_aws_account():
    """
    Return the identity of the currently connected AWS account.
    """

    identity = get_aws_account_identity()

    return {
        "account_id": identity["account_id"],
        "arn": identity["arn"],
    }

@router.post("/accounts")
def register_aws_account(account: AWSAccountCreate):
    """
    Register a participant AWS account.

    Permanent AWS access keys are not stored.
    Only the cross-account IAM Role ARN is saved.
    """

    db: Session = SessionLocal()

    try:
        existing_account = (
            db.query(AWSAccount)
            .filter(
                AWSAccount.participant_id
                == account.participant_id
            )
            .first()
        )

        if existing_account:
            return {
                "status": "already_exists",
                "message": (
                    "Participant ID is already registered."
                ),
            }

        aws_account = AWSAccount(
            participant_id=account.participant_id,
            account_alias=account.account_alias,
            role_arn=account.role_arn,
            default_region=account.default_region,
            is_active=True,
        )

        db.add(aws_account)
        db.commit()
        db.refresh(aws_account)

        return {
            "status": "registered",
            "account": {
                "id": aws_account.id,
                "participant_id": aws_account.participant_id,
                "account_alias": aws_account.account_alias,
                "default_region": aws_account.default_region,
                "is_active": aws_account.is_active,
            },
        }

    finally:
        db.close()

@router.get("/accounts")
def list_aws_accounts():
    """
    List all registered AWS research accounts.
    """

    db: Session = SessionLocal()

    try:
        accounts = (
            db.query(AWSAccount)
            .order_by(AWSAccount.id)
            .all()
        )

        return {
            "count": len(accounts),
            "accounts": [
                {
                    "id": account.id,
                    "participant_id": account.participant_id,
                    "account_alias": account.account_alias,
                    "role_arn": account.role_arn,
                    "default_region": account.default_region,
                    "is_active": account.is_active,
                }
                for account in accounts
            ],
        }

    finally:
        db.close()

@router.get("/accounts/{participant_id}/test-connection")
def test_participant_account_connection(
    participant_id: str,
):
    """
    Test STS AssumeRole connectivity for a
    registered participant AWS account.
    """

    db: Session = SessionLocal()

    try:
        account = (
            db.query(AWSAccount)
            .filter(
                AWSAccount.participant_id
                == participant_id
            )
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=404,
                detail="Participant account not found.",
            )

        if not account.is_active:
            raise HTTPException(
                status_code=400,
                detail="Participant account is inactive.",
            )

        try:
            session = assume_role_session(
                role_arn=account.role_arn
            )

            identity = get_aws_account_identity(
                session=session
            )

        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Unable to assume participant "
                    f"AWS role: {str(exc)}"
                ),
            )

        return {
            "status": "connected",
            "participant_id": account.participant_id,
            "account_alias": account.account_alias,
            "default_region": account.default_region,
            "aws_identity": {
                "account_id": identity["account_id"],
                "arn": identity["arn"],
            },
        }

    finally:
        db.close()

@router.get("/accounts/{participant_id}/ec2")
def get_participant_ec2_instances(
    participant_id: str,
):
    """
    Fetch EC2 instances from a registered participant
    AWS account using STS AssumeRole.
    """

    db: Session = SessionLocal()

    try:
        account = (
            db.query(AWSAccount)
            .filter(
                AWSAccount.participant_id
                == participant_id
            )
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=404,
                detail="Participant account not found.",
            )

        if not account.is_active:
            raise HTTPException(
                status_code=400,
                detail="Participant account is inactive.",
            )

        try:
            session = assume_role_session(
                role_arn=account.role_arn
            )

            instances = get_ec2_instances(
                session=session,
                region_name=account.default_region,
            )

        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Unable to scan participant AWS account: "
                    f"{str(exc)}"
                ),
            )

        return {
            "participant_id": account.participant_id,
            "account_alias": account.account_alias,
            "region": account.default_region,
            "instance_count": len(instances),
            "instances": instances,
        }

    finally:
        db.close()

@router.get("/accounts/{participant_id}/ec2/metrics")
def get_participant_ec2_metrics(
    participant_id: str,
):
    db: Session = SessionLocal()

    try:
        account = (
            db.query(AWSAccount)
            .filter(
                AWSAccount.participant_id == participant_id
            )
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=404,
                detail="Participant account not found.",
            )

        if not account.is_active:
            raise HTTPException(
                status_code=400,
                detail="Participant account is inactive.",
            )

        try:
            session = assume_role_session(
                role_arn=account.role_arn
            )

            instances = get_ec2_instances(
                session=session,
                region_name=account.default_region,
            )

            metrics = []

            for instance in instances:
                instance_id = instance["instance_id"]

                cpu_24h = get_ec2_cpu_utilization(
                    instance_id,
                    hours=24,
                    session=session,
                    region_name=account.default_region,
                )

                cpu_7d = get_ec2_cpu_utilization(
                    instance_id,
                    hours=24 * 7,
                    session=session,
                    region_name=account.default_region,
                )

                cpu_30d = get_ec2_cpu_utilization(
                    instance_id,
                    hours=24 * 30,
                    session=session,
                    region_name=account.default_region,
                )

                metrics.append(
                    {
                        "instance_id": instance_id,
                        "instance_type": instance["instance_type"],
                        "state": instance["state"],
                        "availability_zone": instance[
                            "availability_zone"
                        ],
                        "cpu_24h": cpu_24h,
                        "cpu_7d": cpu_7d,
                        "cpu_30d": cpu_30d,
                    }
                )

        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Unable to fetch participant "
                    f"CloudWatch metrics: {str(exc)}"
                ),
            )

        return {
            "participant_id": account.participant_id,
            "account_alias": account.account_alias,
            "region": account.default_region,
            "instance_count": len(instances),
            "analysis_periods": [
                "24_hours",
                "7_days",
                "30_days",
            ],
            "metrics": metrics,
        }

    finally:
        db.close()

@router.get("/accounts/{participant_id}/ec2/recommendations")
def get_participant_ec2_recommendations(
    participant_id: str,
):
    """
    Generate multi-period EC2 optimization recommendations
    for a registered participant AWS account.
    """

    db: Session = SessionLocal()

    try:
        account = (
            db.query(AWSAccount)
            .filter(
                AWSAccount.participant_id == participant_id
            )
            .first()
        )

        if not account:
            raise HTTPException(
                status_code=404,
                detail="Participant account not found.",
            )

        if not account.is_active:
            raise HTTPException(
                status_code=400,
                detail="Participant account is inactive.",
            )

        try:
            session = assume_role_session(
                role_arn=account.role_arn
            )

            instances = get_ec2_instances(
                session=session,
                region_name=account.default_region,
            )

            recommendations = []

            for instance in instances:
                instance_id = instance["instance_id"]

                cpu_24h = get_ec2_cpu_utilization(
                    instance_id,
                    hours=24,
                    session=session,
                    region_name=account.default_region,
                )

                cpu_7d = get_ec2_cpu_utilization(
                    instance_id,
                    hours=24 * 7,
                    session=session,
                    region_name=account.default_region,
                )

                cpu_30d = get_ec2_cpu_utilization(
                    instance_id,
                    hours=24 * 30,
                    session=session,
                    region_name=account.default_region,
                )

                analysis = analyze_multi_period_cpu(
                    cpu_24h["average_cpu"],
                    cpu_7d["average_cpu"],
                    cpu_30d["average_cpu"],
                )

                recommendations.append(
                    {
                        "instance_id": instance_id,
                        "instance_type": instance["instance_type"],
                        "state": instance["state"],
                        "availability_zone": instance[
                            "availability_zone"
                        ],
                        "cpu_utilization": {
                            "24_hours": cpu_24h[
                                "average_cpu"
                            ],
                            "7_days": cpu_7d[
                                "average_cpu"
                            ],
                            "30_days": cpu_30d[
                                "average_cpu"
                            ],
                        },
                        "optimization_status": analysis[
                            "optimization_status"
                        ],
                        "confidence": analysis[
                            "confidence"
                        ],
                        "recommendation": analysis[
                            "recommendation"
                        ],
                    }
                )

        except HTTPException:
            raise

        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=(
                    "Unable to generate participant "
                    f"recommendations: {str(exc)}"
                ),
            )

        return {
            "participant_id": account.participant_id,
            "account_alias": account.account_alias,
            "region": account.default_region,
            "instance_count": len(instances),
            "analysis_method": "multi_period_cpu_analysis",
            "recommendations": recommendations,
        }

    finally:
        db.close()

@router.post("/accounts/scan-all")
def scan_all_participant_accounts():
    """
    Scan all active registered AWS participant accounts.

    Each account is accessed through STS AssumeRole.
    A failure in one account does not stop other accounts.
    """

    db: Session = SessionLocal()

    try:
        accounts = (
            db.query(AWSAccount)
            .filter(AWSAccount.is_active == True)
            .order_by(AWSAccount.id)
            .all()
        )

        results = []

        successful_scans = 0
        failed_scans = 0
        total_instances = 0
        idle_instances = 0
        underutilized_instances = 0
        normal_instances = 0
        unknown_instances = 0
        
        for account in accounts:
            try:
                session = assume_role_session(
                    role_arn=account.role_arn
                )

                instances = get_ec2_instances(
                    session=session,
                    region_name=account.default_region,
                )

                account_recommendations = []

                for instance in instances:
                    instance_id = instance["instance_id"]

                    cpu_24h = get_ec2_cpu_utilization(
                        instance_id,
                        hours=24,
                        session=session,
                        region_name=account.default_region,
                    )

                    cpu_7d = get_ec2_cpu_utilization(
                        instance_id,
                        hours=24 * 7,
                        session=session,
                        region_name=account.default_region,
                    )

                    cpu_30d = get_ec2_cpu_utilization(
                        instance_id,
                        hours=24 * 30,
                        session=session,
                        region_name=account.default_region,
                    )

                    analysis = analyze_multi_period_cpu(
                        cpu_24h["average_cpu"],
                        cpu_7d["average_cpu"],
                        cpu_30d["average_cpu"],
                    )
                    status = analysis["optimization_status"]

                    if status == "IDLE":
                        idle_instances += 1

                    elif status == "UNDERUTILIZED":
                        underutilized_instances += 1

                    elif status == "NORMAL":
                        normal_instances += 1

                    else:
                        unknown_instances += 1
                    account_recommendations.append(
                        {
                            "instance_id": instance_id,
                            "instance_type": instance[
                                "instance_type"
                            ],
                            "state": instance["state"],
                            "cpu_utilization": {
                                "24_hours": cpu_24h[
                                    "average_cpu"
                                ],
                                "7_days": cpu_7d[
                                    "average_cpu"
                                ],
                                "30_days": cpu_30d[
                                    "average_cpu"
                                ],
                            },
                            "optimization_status": analysis[
                                "optimization_status"
                            ],
                            "confidence": analysis[
                                "confidence"
                            ],
                            "recommendation": analysis[
                                "recommendation"
                            ],
                        }
                    )

                instance_count = len(instances)

                total_instances += instance_count
                successful_scans += 1

                results.append(
                    {
                        "participant_id": account.participant_id,
                        "account_alias": account.account_alias,
                        "region": account.default_region,
                        "scan_status": "SUCCESS",
                        "instance_count": instance_count,
                        "recommendations": account_recommendations,
                    }
                )

            except Exception as exc:
                failed_scans += 1

                results.append(
                    {
                        "participant_id": account.participant_id,
                        "account_alias": account.account_alias,
                        "region": account.default_region,
                        "scan_status": "FAILED",
                        "instance_count": 0,
                        "error": str(exc),
                        "recommendations": [],
                    }
                )

        return {
            "scan_type": "multi_account_optimization_scan",
            "total_accounts": len(accounts),
            "successful_scans": successful_scans,
            "failed_scans": failed_scans,
            "total_instances": total_instances,
            "optimization_summary": {
                "idle_instances": idle_instances,
                "underutilized_instances": underutilized_instances,
                "normal_instances": normal_instances,
                "unknown_instances": unknown_instances,
            },
            "accounts": results,
        }
    finally:
        db.close()



@router.get("/accounts/dashboard/summary")
def get_multi_account_dashboard_summary():
    """
    Return aggregated dashboard summary
    across all registered AWS accounts.
    """

    db: Session = SessionLocal()

    try:
        accounts = (
            db.query(AWSAccount)
            .filter(AWSAccount.is_active == True)
            .order_by(AWSAccount.id)
            .all()
        )

        total_accounts = len(accounts)
        active_accounts = len(accounts)

        total_instances = 0
        idle_instances = 0
        underutilized_instances = 0
        normal_instances = 0
        unknown_instances = 0

        successful_accounts = 0
        failed_accounts = 0

        for account in accounts:
            try:
                session = assume_role_session(
                    role_arn=account.role_arn
                )

                instances = get_ec2_instances(
                    session=session,
                    region_name=account.default_region,
                )

                successful_accounts += 1
                total_instances += len(instances)

                for instance in instances:
                    instance_id = instance["instance_id"]

                    cpu_24h = get_ec2_cpu_utilization(
                        instance_id,
                        hours=24,
                        session=session,
                        region_name=account.default_region,
                    )

                    cpu_7d = get_ec2_cpu_utilization(
                        instance_id,
                        hours=24 * 7,
                        session=session,
                        region_name=account.default_region,
                    )

                    cpu_30d = get_ec2_cpu_utilization(
                        instance_id,
                        hours=24 * 30,
                        session=session,
                        region_name=account.default_region,
                    )

                    analysis = analyze_multi_period_cpu(
                        cpu_24h["average_cpu"],
                        cpu_7d["average_cpu"],
                        cpu_30d["average_cpu"],
                    )

                    status = analysis["optimization_status"]

                    if status == "IDLE":
                        idle_instances += 1

                    elif status == "UNDERUTILIZED":
                        underutilized_instances += 1

                    elif status == "NORMAL":
                        normal_instances += 1

                    else:
                        unknown_instances += 1

            except Exception:
                failed_accounts += 1

        optimization_opportunities = (
            idle_instances + underutilized_instances
        )

        return {
            "dashboard_type": (
                "multi_account_optimization_dashboard"
            ),
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "successful_accounts": successful_accounts,
            "failed_accounts": failed_accounts,
            "total_instances": total_instances,
            "optimization_summary": {
                "idle_instances": idle_instances,
                "underutilized_instances": (
                    underutilized_instances
                ),
                "normal_instances": normal_instances,
                "unknown_instances": unknown_instances,
            },
            "optimization_opportunities": (
                optimization_opportunities
            ),
        }

    finally:
        db.close()

@router.get("/accounts/cost/summary")
def get_multi_account_cost_summary(days: int = 30):
    """
    Aggregate AWS Cost Explorer billing data
    across all active registered participant accounts.
    """

    db = SessionLocal()

    try:
        accounts = (
            db.query(AWSAccount)
            .filter(AWSAccount.is_active == True)
            .all()
        )

        results = []

        successful_accounts = 0
        failed_accounts = 0
        total_cost_usd = 0.0

        for account in accounts:
            try:
                # Create cross-account AWS session
                session = assume_role_session(
                    role_arn=account.role_arn
                )

                # Cost Explorer client
                ce_client = session.client(
                    "ce",
                    region_name="us-east-1"
                )

                end_date = date.today()
                start_date = end_date - timedelta(
                    days=days
                )

                response = ce_client.get_cost_and_usage(
                    TimePeriod={
                        "Start": start_date.isoformat(),
                        "End": end_date.isoformat(),
                    },
                    Granularity="MONTHLY",
                    Metrics=["UnblendedCost"],
                )

                account_cost = 0.0

                for period in response.get(
                    "ResultsByTime", []
                ):
                    amount = (
                        period
                        .get("Total", {})
                        .get("UnblendedCost", {})
                        .get("Amount", "0")
                    )

                    account_cost += float(amount)

                total_cost_usd += account_cost
                successful_accounts += 1

                results.append(
                    {
                        "participant_id":
                            account.participant_id,
                        "account_alias":
                            account.account_alias,
                        "region":
                            account.default_region,
                        "cost_usd":
                            round(account_cost, 8),
                        "status": "SUCCESS",
                    }
                )

            except Exception as exc:
                failed_accounts += 1

                results.append(
                    {
                        "participant_id":
                            account.participant_id,
                        "account_alias":
                            account.account_alias,
                        "region":
                            account.default_region,
                        "cost_usd": 0,
                        "status": "FAILED",
                        "error": str(exc),
                    }
                )

        return {
            "summary_type":
                "multi_account_cost_summary",
            "analysis_period_days":
                days,
            "total_accounts":
                len(accounts),
            "successful_accounts":
                successful_accounts,
            "failed_accounts":
                failed_accounts,
            "total_cost_usd":
                round(total_cost_usd, 8),
            "accounts":
                results,
        }

    finally:
        db.close()

@router.get("/accounts/research/dashboard")
def get_research_dashboard(days: int = 30):
    """
    Combined research dashboard for multi-account
    cloud cost and optimization analysis.
    """

    db: Session = SessionLocal()

    try:
        accounts = (
            db.query(AWSAccount)
            .filter(AWSAccount.is_active == True)
            .all()
        )

        total_accounts = len(accounts)
        successful_accounts = 0
        failed_accounts = 0

        total_instances = 0
        idle_instances = 0
        underutilized_instances = 0
        normal_instances = 0
        unknown_instances = 0

        total_cost_usd = 0.0

        account_results = []

        for account in accounts:
            try:
                # Assume participant AWS role
                session = assume_role_session(
                    role_arn=account.role_arn
                )

                # -------------------------
                # EC2 + OPTIMIZATION DATA
                # -------------------------

                instances = get_ec2_instances(
                    session=session,
                    region_name=account.default_region,
                )

                instance_count = len(instances)
                total_instances += instance_count

                for instance in instances:
                    instance_id = instance["instance_id"]

                    cpu_24h = get_ec2_cpu_utilization(
                        instance_id,
                        hours=24,
                        session=session,
                        region_name=account.default_region,
                    )

                    cpu_7d = get_ec2_cpu_utilization(
                        instance_id,
                        hours=24 * 7,
                        session=session,
                        region_name=account.default_region,
                    )

                    cpu_30d = get_ec2_cpu_utilization(
                        instance_id,
                        hours=24 * 30,
                        session=session,
                        region_name=account.default_region,
                    )

                    analysis = analyze_multi_period_cpu(
                        cpu_24h["average_cpu"],
                        cpu_7d["average_cpu"],
                        cpu_30d["average_cpu"],
                    )

                    status = analysis["optimization_status"]

                    if status == "IDLE":
                        idle_instances += 1

                    elif status == "UNDERUTILIZED":
                        underutilized_instances += 1

                    elif status == "NORMAL":
                        normal_instances += 1

                    else:
                        unknown_instances += 1

                # -------------------------
                # COST EXPLORER DATA
                # -------------------------

                ce_client = session.client(
                    "ce",
                    region_name="us-east-1",
                )

                end_date = date.today()
                start_date = end_date - timedelta(
                    days=days
                )

                cost_response = (
                    ce_client.get_cost_and_usage(
                        TimePeriod={
                            "Start":
                                start_date.isoformat(),
                            "End":
                                end_date.isoformat(),
                        },
                        Granularity="MONTHLY",
                        Metrics=["UnblendedCost"],
                    )
                )

                account_cost = 0.0

                for period in cost_response.get(
                    "ResultsByTime", []
                ):
                    amount = (
                        period
                        .get("Total", {})
                        .get("UnblendedCost", {})
                        .get("Amount", "0")
                    )

                    account_cost += float(amount)

                total_cost_usd += account_cost
                successful_accounts += 1

                account_results.append(
                    {
                        "participant_id":
                            account.participant_id,
                        "account_alias":
                            account.account_alias,
                        "region":
                            account.default_region,
                        "status": "SUCCESS",
                        "instance_count":
                            instance_count,
                        "cost_usd":
                            round(account_cost, 8),
                    }
                )

            except Exception as exc:
                failed_accounts += 1

                account_results.append(
                    {
                        "participant_id":
                            account.participant_id,
                        "account_alias":
                            account.account_alias,
                        "region":
                            account.default_region,
                        "status": "FAILED",
                        "error": str(exc),
                    }
                )

        optimization_opportunities = (
            idle_instances
            + underutilized_instances
        )

        return {
            "dashboard_type":
                "multi_account_research_dashboard",
            "analysis_period_days":
                days,
            "accounts_summary": {
                "total_accounts":
                    total_accounts,
                "successful_accounts":
                    successful_accounts,
                "failed_accounts":
                    failed_accounts,
            },
            "infrastructure_summary": {
                "total_instances":
                    total_instances,
            },
            "optimization_summary": {
                "idle_instances":
                    idle_instances,
                "underutilized_instances":
                    underutilized_instances,
                "normal_instances":
                    normal_instances,
                "unknown_instances":
                    unknown_instances,
                "optimization_opportunities":
                    optimization_opportunities,
            },
            "cost_summary": {
                "total_cost_usd":
                    round(total_cost_usd, 8),
            },
            "accounts":
                account_results,
        }

    finally:
        db.close()