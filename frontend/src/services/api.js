const API_BASE_URL = "http://127.0.0.1:8000";

export async function getDashboardSummary() {
  const response = await fetch(
    `${API_BASE_URL}/aws/dashboard/summary`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch dashboard summary");
  }

  return response.json();
}

export async function runOptimizationScan() {
  const response = await fetch(
    `${API_BASE_URL}/aws/ec2/scan`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    throw new Error("Failed to run optimization scan");
  }

  return response.json();
}

// NEW: Fetch EC2 optimization recommendations
export async function getEC2Recommendations() {
  const response = await fetch(
    `${API_BASE_URL}/aws/ec2/recommendations`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch EC2 recommendations");
  }

  return response.json();
}
export async function getOptimizationHistory() {
  const response = await fetch(
    `${API_BASE_URL}/aws/ec2/history`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch optimization history");
  }

  return response.json();
}