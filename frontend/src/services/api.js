const API_BASE_URL = "http://127.0.0.1:8000";

/* =========================================================
   SINGLE ACCOUNT / EXISTING APIs
========================================================= */

// Dashboard Summary
export async function getDashboardSummary() {
  const response = await fetch(
    `${API_BASE_URL}/aws/dashboard/summary`
  );

  if (!response.ok) {
    throw new Error("Failed to fetch dashboard summary");
  }

  return response.json();
}


// Run Single Account Optimization Scan
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


// Single Account EC2 Recommendations
export async function getEC2Recommendations() {
  const response = await fetch(
    `${API_BASE_URL}/aws/ec2/recommendations`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch EC2 recommendations"
    );
  }

  return response.json();
}


// Optimization History
export async function getOptimizationHistory() {
  const response = await fetch(
    `${API_BASE_URL}/aws/ec2/history`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch optimization history"
    );
  }

  return response.json();
}


/* =========================================================
   MULTI-ACCOUNT / RESEARCH APIs
========================================================= */


// ---------------------------------------------------------
// Get All Registered AWS Accounts
// ---------------------------------------------------------

export async function getAWSAccounts() {
  const response = await fetch(
    `${API_BASE_URL}/aws/accounts`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch AWS accounts"
    );
  }

  return response.json();
}


// ---------------------------------------------------------
// Get Current AWS Account
// ---------------------------------------------------------

export async function getCurrentAWSAccount() {
  const response = await fetch(
    `${API_BASE_URL}/aws/accounts/current`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch current AWS account"
    );
  }

  return response.json();
}


// ---------------------------------------------------------
// Test Participant AWS Connection
// ---------------------------------------------------------

export async function testParticipantConnection(
  participantId
) {
  const response = await fetch(
    `${API_BASE_URL}/aws/accounts/${participantId}/test-connection`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to test participant AWS connection"
    );
  }

  return response.json();
}


// ---------------------------------------------------------
// Get Participant EC2 Instances
// ---------------------------------------------------------

export async function getParticipantEC2(
  participantId
) {
  const response = await fetch(
    `${API_BASE_URL}/aws/accounts/${participantId}/ec2`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch participant EC2 instances"
    );
  }

  return response.json();
}


// ---------------------------------------------------------
// Get Participant EC2 Metrics
// ---------------------------------------------------------

export async function getParticipantEC2Metrics(
  participantId
) {
  const response = await fetch(
    `${API_BASE_URL}/aws/accounts/${participantId}/ec2/metrics`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch participant EC2 metrics"
    );
  }

  return response.json();
}


// ---------------------------------------------------------
// Participant EC2 Recommendations
// ---------------------------------------------------------

export async function getParticipantRecommendations(
  participantId
) {
  const response = await fetch(
    `${API_BASE_URL}/aws/accounts/${participantId}/ec2/recommendations`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch participant recommendations"
    );
  }

  return response.json();
}


// Compatibility function
// Keep this in case another component uses this name.

export async function getParticipantEC2Recommendations(
  participantId
) {
  return getParticipantRecommendations(
    participantId
  );
}


// ---------------------------------------------------------
// Run Multi-Account Optimization Scan
// ---------------------------------------------------------

export async function runMultiAccountScan() {
  const response = await fetch(
    `${API_BASE_URL}/aws/accounts/scan-all`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    throw new Error(
      "Failed to run multi-account optimization scan"
    );
  }

  return response.json();
}


// Compatibility function

export async function scanAllAccounts() {
  return runMultiAccountScan();
}


// ---------------------------------------------------------
// Multi-Account Dashboard Summary
// ---------------------------------------------------------

export async function getMultiAccountDashboard() {
  const response = await fetch(
    `${API_BASE_URL}/aws/accounts/dashboard/summary`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch multi-account dashboard"
    );
  }

  return response.json();
}


// ---------------------------------------------------------
// Multi-Account Cost Summary
// ---------------------------------------------------------

export async function getMultiAccountCostSummary(
  days = 30
) {
  const response = await fetch(
    `${API_BASE_URL}/aws/accounts/cost/summary?days=${days}`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch multi-account cost summary"
    );
  }

  return response.json();
}


// ---------------------------------------------------------
// Research Dashboard
// ---------------------------------------------------------

export async function getResearchDashboard(
  days = 30
) {
  const response = await fetch(
    `${API_BASE_URL}/aws/accounts/research/dashboard?days=${days}`
  );

  if (!response.ok) {
    throw new Error(
      "Failed to fetch research dashboard"
    );
  }

  return response.json();
}