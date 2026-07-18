HOURS_PER_MONTH = 730

# Simplified estimated average power consumption in watts.
# These values are assumptions for the initial project model.
INSTANCE_POWER_WATTS = {
    "t3.micro": 5.0,
}

# Simplified carbon-intensity assumptions in grams CO2e per kWh.
# Later these values can be replaced with a verified external dataset/API.
REGION_CARBON_INTENSITY = {
    "us-east-1": 350,
}


def estimate_carbon_emissions(
    instance_type: str,
    region: str = "us-east-1",
):
    power_watts = INSTANCE_POWER_WATTS.get(instance_type)
    carbon_intensity = REGION_CARBON_INTENSITY.get(region)

    if power_watts is None or carbon_intensity is None:
        return {
            "estimated_energy_kwh_monthly": None,
            "estimated_carbon_kg_monthly": None,
        }

    # Convert watts to kilowatts and estimate monthly energy.
    energy_kwh = (
        power_watts / 1000
    ) * HOURS_PER_MONTH

    # Carbon intensity is gCO2e/kWh.
    carbon_grams = energy_kwh * carbon_intensity
    carbon_kg = carbon_grams / 1000

    return {
        "estimated_energy_kwh_monthly": round(
            energy_kwh, 3
        ),
        "estimated_carbon_kg_monthly": round(
            carbon_kg, 3
        ),
    }


def calculate_potential_carbon_reduction(
    estimated_carbon_kg,
    optimization_status,
):
    if estimated_carbon_kg is None:
        return None

    if optimization_status == "IDLE":
        return round(estimated_carbon_kg, 3)

    if optimization_status == "UNDERUTILIZED":
        # Initial assumption: rightsizing may reduce
        # estimated carbon impact by about 50%.
        return round(estimated_carbon_kg * 0.50, 3)

    return 0.0