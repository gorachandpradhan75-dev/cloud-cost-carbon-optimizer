def analyze_cpu_utilization(average_cpu):
    if average_cpu is None:
        return {
            "optimization_status": "UNKNOWN",
            "recommendation": "Insufficient CloudWatch data for analysis.",
        }

    if average_cpu < 2:
        return {
            "optimization_status": "IDLE",
            "recommendation": (
                "Instance has very low CPU utilization. "
                "Consider stopping it if it is not required."
            ),
        }

    if average_cpu < 10:
        return {
            "optimization_status": "UNDERUTILIZED",
            "recommendation": (
                "Instance appears underutilized. "
                "Consider rightsizing to a smaller instance type."
            ),
        }

    return {
        "optimization_status": "NORMAL",
        "recommendation": (
            "Instance utilization is within the normal range. "
            "No immediate optimization action is recommended."
        ),
    }

def analyze_multi_period_cpu(
    cpu_24h,
    cpu_7d,
    cpu_30d,
):
    """
    Analyze EC2 CPU utilization using short-term
    and long-term CloudWatch metrics.

    Research v2 optimization logic:
    - 24 hours
    - 7 days
    - 30 days
    """

    available_metrics = [
        value
        for value in [
            cpu_24h,
            cpu_7d,
            cpu_30d,
        ]
        if value is not None
    ]

    if not available_metrics:
        return {
            "optimization_status": "UNKNOWN",
            "confidence": "LOW",
            "recommendation": (
                "Insufficient CloudWatch data "
                "for multi-period analysis."
            ),
        }

    # Use the maximum observed average CPU across
    # available periods as a conservative safeguard.
    peak_period_average = max(
        available_metrics
    )

    # ---------------------------------
    # IDLE
    # ---------------------------------

    if peak_period_average < 2:
        return {
            "optimization_status": "IDLE",
            "confidence": (
                "HIGH"
                if len(available_metrics) == 3
                else "MEDIUM"
            ),
            "recommendation": (
                "Instance shows consistently very low CPU "
                "utilization across available analysis periods. "
                "Consider stopping it if it is not required."
            ),
        }

    # ---------------------------------
    # UNDERUTILIZED
    # ---------------------------------

    if peak_period_average < 10:
        return {
            "optimization_status": "UNDERUTILIZED",
            "confidence": (
                "HIGH"
                if len(available_metrics) == 3
                else "MEDIUM"
            ),
            "recommendation": (
                "Instance shows low CPU utilization across "
                "the analyzed periods. Consider rightsizing "
                "to a smaller instance type."
            ),
        }

    # ---------------------------------
    # NORMAL
    # ---------------------------------

    return {
        "optimization_status": "NORMAL",
        "confidence": (
            "HIGH"
            if len(available_metrics) == 3
            else "MEDIUM"
        ),
        "recommendation": (
            "Instance utilization indicates meaningful "
            "workload activity. No immediate optimization "
            "action is recommended."
        ),
    }