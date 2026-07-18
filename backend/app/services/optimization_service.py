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