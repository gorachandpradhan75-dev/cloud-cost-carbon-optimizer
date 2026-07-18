HOURS_PER_MONTH = 730

# Estimated Linux On-Demand hourly rates.
# Later this will be replaced with dynamic AWS pricing data.
INSTANCE_HOURLY_PRICES = {
    "t3.micro": 0.0104,
}


def estimate_instance_cost(instance_type: str):
    hourly_price = INSTANCE_HOURLY_PRICES.get(instance_type)

    if hourly_price is None:
        return {
            "hourly_cost_usd": None,
            "estimated_monthly_cost_usd": None,
        }

    monthly_cost = hourly_price * HOURS_PER_MONTH

    return {
        "hourly_cost_usd": round(hourly_price, 4),
        "estimated_monthly_cost_usd": round(monthly_cost, 2),
    }


def calculate_potential_savings(
    monthly_cost,
    optimization_status,
):
    if monthly_cost is None:
        return None

    if optimization_status == "IDLE":
        return round(monthly_cost, 2)

    if optimization_status == "UNDERUTILIZED":
        # Initial estimate: rightsizing could save about 50%.
        return round(monthly_cost * 0.50, 2)

    return 0.0