import { useEffect, useState } from "react";

import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

import {
  getOptimizationHistory,
  getMultiAccountDashboard,
  getAWSAccounts,
  getParticipantEC2,
  getParticipantEC2Metrics,
  getParticipantRecommendations,
  runMultiAccountScan,
  getResearchDashboard,
  getMultiAccountCostSummary,
} from "./services/api";

import "./App.css";

function App() {
  // ============================================
  // State
  // ============================================

  const [summary, setSummary] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [history, setHistory] = useState([]);

  const [accounts, setAccounts] = useState([]);
  const [participantEC2, setParticipantEC2] = useState(null);
  const [participantMetrics, setParticipantMetrics] = useState(null);
  const [researchDashboard, setResearchDashboard] = useState(null);
  const [costSummary, setCostSummary] = useState(null);

  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState(null);

  const PARTICIPANT_ID = "Participant-001";

  // ============================================
  // Load Dashboard
  // ============================================

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);

      const [
        dashboardData,
        accountsData,
        ec2Data,
        metricsData,
        recommendationsData,
        historyData,
        researchData,
        costData,
      ] = await Promise.all([
        getMultiAccountDashboard(),
        getAWSAccounts(),
        getParticipantEC2(PARTICIPANT_ID),
        getParticipantEC2Metrics(PARTICIPANT_ID),
        getParticipantRecommendations(PARTICIPANT_ID),
        getOptimizationHistory(),
        getResearchDashboard(),
        getMultiAccountCostSummary(),
      ]);

      setSummary(dashboardData);

      setAccounts(accountsData?.accounts || []);

      setParticipantEC2(ec2Data || null);

      setParticipantMetrics(metricsData || null);

      setRecommendations(
        recommendationsData?.recommendations || []
      );

      setHistory(historyData?.history || []);

      setResearchDashboard(researchData || null);

      setCostSummary(costData || null);
    } catch (err) {
      console.error("Dashboard loading error:", err);

      setError(
        "Failed to load multi-account dashboard data. Make sure the backend server is running."
      );
    } finally {
      setLoading(false);
    }
  };

  // ============================================
  // Initial Load
  // ============================================

  useEffect(() => {
    loadDashboard();
  }, []);

  // ============================================
  // Run Multi Account Scan
  // ============================================

  const handleScan = async () => {
    try {
      setScanning(true);
      setError(null);

      await runMultiAccountScan();

      await loadDashboard();
    } catch (err) {
      console.error(
        "Multi-account optimization scan error:",
        err
      );

      setError(
        "Multi-account optimization scan failed. Please check the backend server."
      );
    } finally {
      setScanning(false);
    }
  };

  // ============================================
  // Derived Dashboard Values
  // ============================================

  const totalAccounts =
    Number(summary?.total_accounts ?? accounts.length ?? 0);

  const activeAccounts =
    Number(summary?.active_accounts ?? 0);

  const totalInstances =
    Number(
      summary?.total_instances ??
        researchDashboard?.infrastructure_summary
          ?.total_instances ??
        participantEC2?.instance_count ??
        0
    );

  const idleInstances =
    Number(
      summary?.optimization_summary?.idle_instances ??
        researchDashboard?.optimization_summary
          ?.idle_instances ??
        0
    );

  const underutilizedInstances =
    Number(
      summary?.optimization_summary
        ?.underutilized_instances ??
        researchDashboard?.optimization_summary
          ?.underutilized_instances ??
        0
    );

  const normalInstances =
    Number(
      summary?.optimization_summary?.normal_instances ??
        researchDashboard?.optimization_summary
          ?.normal_instances ??
        0
    );

  const optimizationOpportunities =
    Number(
      summary?.optimization_opportunities ??
        researchDashboard?.optimization_summary
          ?.optimization_opportunities ??
        idleInstances + underutilizedInstances
    );

  const runningInstances =
    participantEC2?.instances?.filter(
      (instance) =>
        instance.state?.toLowerCase() === "running"
    ).length ?? 0;

  const totalCost =
    Number(
      costSummary?.total_cost_usd ??
        researchDashboard?.cost_summary?.total_cost_usd ??
        0
    );

  // ============================================
  // Current Account
  // ============================================

  const currentAccount =
    accounts.find(
      (account) =>
        account.participant_id === PARTICIPANT_ID
    ) || accounts[0];

  // ============================================
  // CPU Chart Data
  // ============================================

  const cpuChartData =
    participantMetrics?.metrics?.map(
      (item, index) => ({
        name: `EC2-${index + 1}`,
        instanceId: item.instance_id,

        cpu24: Number(
          item.cpu_24h?.average_cpu ?? 0
        ),

        cpu7: Number(
          item.cpu_7d?.average_cpu ?? 0
        ),

        cpu30: Number(
          item.cpu_30d?.average_cpu ?? 0
        ),
      })
    ) || [];

  // ============================================
  // Optimization Chart
  // ============================================

  const optimizationChartData = [
    {
      name: "Idle",
      value: idleInstances,
    },
    {
      name: "Underutilized",
      value: underutilizedInstances,
    },
    {
      name: "Normal",
      value: normalInstances,
    },
  ];

  // ============================================
  // Historical Analytics
  // ============================================

  const historicalChartData = [...history]
    .sort((a, b) => a.id - b.id)
    .map((item) => ({
      scanId: `#${item.id}`,

      cpu: Number(
        item.average_cpu_24h ?? 0
      ),

      cost: Number(
        item.estimated_monthly_cost_usd ?? 0
      ),

      savings: Number(
        item.potential_monthly_savings_usd ?? 0
      ),

      carbonReduction: Number(
        item.potential_carbon_reduction_kg ?? 0
      ),

      time: item.created_at
        ? new Date(
            item.created_at
          ).toLocaleString()
        : "N/A",
    }));

  // ============================================
  // Loading Screen
  // ============================================

  if (loading && !summary) {
    return (
      <div className="loading">
        Loading multi-account dashboard...
      </div>
    );
  }

  // ============================================
  // Error Screen
  // ============================================

  if (error && !summary) {
    return (
      <div className="loading">
        {error}
      </div>
    );
  }

  // ============================================
  // UI
  // ============================================

  return (
    <div className="dashboard">

      {/* ========================================
          Dashboard Header
      ======================================== */}

      <div className="dashboard-header">
        <div>
          <h1>
            Cloud Cost & Carbon Optimizer
          </h1>

          <p>
            Multi-Account AWS Research Dashboard
          </p>
        </div>

        <button
          className="scan-button"
          onClick={handleScan}
          disabled={scanning}
        >
          {scanning
            ? "Scanning All Accounts..."
            : "Scan All AWS Accounts"}
        </button>
      </div>

      {/* ========================================
          Error Message
      ======================================== */}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {/* ========================================
          Dashboard Summary Cards
      ======================================== */}

      <div className="card-grid">

        <div className="card">
          <p>Total AWS Accounts</p>
          <h2>{totalAccounts}</h2>
        </div>

        <div className="card">
          <p>Active Accounts</p>
          <h2>{activeAccounts}</h2>
        </div>

        <div className="card">
          <p>Total EC2 Instances</p>
          <h2>{totalInstances}</h2>
        </div>

        <div className="card">
          <p>Running Instances</p>
          <h2>{runningInstances}</h2>
        </div>

        <div className="card">
          <p>Idle Instances</p>
          <h2>{idleInstances}</h2>
        </div>

        <div className="card">
          <p>Underutilized Instances</p>
          <h2>{underutilizedInstances}</h2>
        </div>

        <div className="card">
          <p>Normal Instances</p>
          <h2>{normalInstances}</h2>
        </div>

        <div className="card">
          <p>Optimization Opportunities</p>
          <h2>{optimizationOpportunities}</h2>
        </div>

        <div className="card">
          <p>30-Day AWS Cost</p>

          <h2>
            ${totalCost.toFixed(2)}
          </h2>
        </div>

      </div>

      {/* ========================================
          Current AWS Account
      ======================================== */}

      <section className="recommendations-section">

        <div className="section-header">
          <div>
            <h2>
              Current AWS Research Account
            </h2>

            <p>
              Registered participant account currently
              being analyzed by the optimizer.
            </p>
          </div>
        </div>

        {currentAccount ? (
          <div className="table-container">

            <table className="recommendations-table">

              <thead>
                <tr>
                  <th>Participant ID</th>
                  <th>Account Alias</th>
                  <th>Region</th>
                  <th>Status</th>
                </tr>
              </thead>

              <tbody>
                <tr>
                  <td>
                    {currentAccount.participant_id}
                  </td>

                  <td>
                    {currentAccount.account_alias}
                  </td>

                  <td>
                    {currentAccount.default_region}
                  </td>

                  <td>
                    <span className="status-badge normal">
                      {currentAccount.is_active
                        ? "ACTIVE"
                        : "INACTIVE"}
                    </span>
                  </td>
                </tr>
              </tbody>

            </table>

          </div>
        ) : (
          <div className="no-data">
            No registered AWS account available.
          </div>
        )}

      </section>

      {/* ========================================
          EC2 Infrastructure
      ======================================== */}

      <section className="recommendations-section">

        <div className="section-header">
          <div>
            <h2>
              EC2 Infrastructure
            </h2>

            <p>
              Live EC2 resources discovered from
              Participant-001.
            </p>
          </div>
        </div>

        {!participantEC2?.instances?.length ? (

          <div className="no-data">
            No EC2 instances available.
          </div>

        ) : (

          <div className="table-container">

            <table className="recommendations-table">

              <thead>
                <tr>
                  <th>Instance ID</th>
                  <th>Type</th>
                  <th>State</th>
                  <th>Availability Zone</th>
                  <th>Region</th>
                  <th>Launch Time</th>
                </tr>
              </thead>

              <tbody>

                {participantEC2.instances.map(
                  (instance) => (

                    <tr key={instance.instance_id}>

                      <td className="instance-id">
                        {instance.instance_id}
                      </td>

                      <td>
                        {instance.instance_type}
                      </td>

                      <td>
                        <span className="status-badge normal">
                          {instance.state?.toUpperCase()}
                        </span>
                      </td>

                      <td>
                        {instance.availability_zone}
                      </td>

                      <td>
                        {participantEC2.region}
                      </td>

                      <td>
                        {instance.launch_time
                          ? new Date(
                              instance.launch_time
                            ).toLocaleString()
                          : "N/A"}
                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        )}

      </section>

      {/* ========================================
          Visual Analytics
      ======================================== */}

      <section className="analytics-section">

        <div className="section-header">

          <div>

            <h2>
              Multi-Period Visual Analytics
            </h2>

            <p>
              AWS EC2 CPU utilization across 24-hour,
              7-day, and 30-day analysis periods.
            </p>

          </div>

        </div>

        <div className="charts-grid">

          {/* CPU Chart */}

          <div className="chart-card">

            <h3>
              EC2 Multi-Period CPU Utilization
            </h3>

            <p className="chart-description">
              Compare average CPU utilization across
              multiple analysis periods.
            </p>

            <div className="chart-wrapper">

              <ResponsiveContainer
                width="100%"
                height={300}
              >

                <BarChart data={cpuChartData}>

                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#334155"
                  />

                  <XAxis
                    dataKey="name"
                    stroke="#94a3b8"
                  />

                  <YAxis
                    stroke="#94a3b8"
                    unit="%"
                  />

                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1e293b",
                      border:
                        "1px solid #334155",
                      borderRadius: "8px",
                    }}
                  />

                  <Bar
                    dataKey="cpu24"
                    name="24 Hours"
                    fill="#3b82f6"
                    radius={[6, 6, 0, 0]}
                  />

                  <Bar
                    dataKey="cpu7"
                    name="7 Days"
                    fill="#22c55e"
                    radius={[6, 6, 0, 0]}
                  />

                  <Bar
                    dataKey="cpu30"
                    name="30 Days"
                    fill="#f59e0b"
                    radius={[6, 6, 0, 0]}
                  />

                </BarChart>

              </ResponsiveContainer>

            </div>

          </div>

          {/* Optimization Summary */}

          <div className="chart-card">

            <h3>
              Optimization Classification
            </h3>

            <p className="chart-description">
              Distribution of EC2 optimization
              classifications.
            </p>

            <div className="chart-wrapper">

              <ResponsiveContainer
                width="100%"
                height={300}
              >

                <BarChart
                  data={optimizationChartData}
                >

                  <CartesianGrid
                    strokeDasharray="3 3"
                    stroke="#334155"
                  />

                  <XAxis
                    dataKey="name"
                    stroke="#94a3b8"
                  />

                  <YAxis
                    stroke="#94a3b8"
                  />

                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1e293b",
                      border:
                        "1px solid #334155",
                      borderRadius: "8px",
                    }}
                  />

                  <Bar
                    dataKey="value"
                    name="Instances"
                    fill="#3b82f6"
                    radius={[6, 6, 0, 0]}
                  />

                </BarChart>

              </ResponsiveContainer>

            </div>

          </div>

        </div>

      </section>

      {/* ========================================
          Continue with PART 2 below
      ======================================== */}
            {/* ========================================
          Multi-Period EC2 Metrics
      ======================================== */}

      <section className="recommendations-section">

        <div className="section-header">

          <div>

            <h2>
              EC2 Multi-Period Metrics
            </h2>

            <p>
              CPU utilization analysis across 24 hours,
              7 days, and 30 days.
            </p>

          </div>

        </div>

        {!participantMetrics?.metrics?.length ? (

          <div className="no-data">
            No EC2 metrics available.
          </div>

        ) : (

          <div className="table-container">

            <table className="recommendations-table">

              <thead>

                <tr>
                  <th>Instance ID</th>
                  <th>Type</th>
                  <th>State</th>
                  <th>CPU 24 Hours</th>
                  <th>CPU 7 Days</th>
                  <th>CPU 30 Days</th>
                </tr>

              </thead>

              <tbody>

                {participantMetrics.metrics.map(
                  (item) => (

                    <tr key={item.instance_id}>

                      <td className="instance-id">
                        {item.instance_id}
                      </td>

                      <td>
                        {item.instance_type}
                      </td>

                      <td>

                        <span className="status-badge normal">

                          {item.state?.toUpperCase()}

                        </span>

                      </td>

                      <td>

                        {Number(
                          item.cpu_24h?.average_cpu ?? 0
                        ).toFixed(2)}
                        %

                      </td>

                      <td>

                        {Number(
                          item.cpu_7d?.average_cpu ?? 0
                        ).toFixed(2)}
                        %

                      </td>

                      <td>

                        {Number(
                          item.cpu_30d?.average_cpu ?? 0
                        ).toFixed(2)}
                        %

                      </td>

                    </tr>

                  )
                )}

              </tbody>

            </table>

          </div>

        )}

      </section>

      {/* ========================================
          Optimization Recommendations
      ======================================== */}

      <section className="recommendations-section">

        <div className="section-header">

          <div>

            <h2>
              Optimization Recommendations
            </h2>

            <p>
              Multi-period CPU analysis and AWS
              resource optimization recommendations.
            </p>

          </div>

        </div>

        {recommendations.length === 0 ? (

          <div className="no-data">
            No optimization recommendations available.
          </div>

        ) : (

          <div className="table-container">

            <table className="recommendations-table">

              <thead>

                <tr>
                  <th>Instance ID</th>
                  <th>Type</th>
                  <th>State</th>
                  <th>CPU 24H</th>
                  <th>CPU 7D</th>
                  <th>CPU 30D</th>
                  <th>Status</th>
                  <th>Confidence</th>
                  <th>Recommendation</th>
                </tr>

              </thead>

              <tbody>

                {recommendations.map((item) => (

                  <tr key={item.instance_id}>

                    <td className="instance-id">
                      {item.instance_id}
                    </td>

                    <td>
                      {item.instance_type}
                    </td>

                    <td>
                      {item.state}
                    </td>

                    <td>

                      {Number(
                        item.cpu_utilization?.[
                          "24_hours"
                        ] ?? 0
                      ).toFixed(2)}
                      %

                    </td>

                    <td>

                      {Number(
                        item.cpu_utilization?.[
                          "7_days"
                        ] ?? 0
                      ).toFixed(2)}
                      %

                    </td>

                    <td>

                      {Number(
                        item.cpu_utilization?.[
                          "30_days"
                        ] ?? 0
                      ).toFixed(2)}
                      %

                    </td>

                    <td>

                      <span
                        className={`status-badge ${
                          item.optimization_status
                            ?.toLowerCase() || ""
                        }`}
                      >

                        {item.optimization_status ||
                          "UNKNOWN"}

                      </span>

                    </td>

                    <td>
                      {item.confidence || "N/A"}
                    </td>

                    <td className="recommendation-text">
                      {item.recommendation}
                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        )}

      </section>

      {/* ========================================
          Multi Account Research Summary
      ======================================== */}

      <section className="recommendations-section">

        <div className="section-header">

          <div>

            <h2>
              Research Analysis Summary
            </h2>

            <p>
              Consolidated AWS multi-account
              infrastructure, optimization, and cost
              research results.
            </p>

          </div>

        </div>

        <div className="card-grid">

          <div className="card">

            <p>Successful Accounts</p>

            <h2>
              {Number(
                researchDashboard?.accounts_summary
                  ?.successful_accounts ?? 0
              )}
            </h2>

          </div>

          <div className="card">

            <p>Failed Accounts</p>

            <h2>
              {Number(
                researchDashboard?.accounts_summary
                  ?.failed_accounts ?? 0
              )}
            </h2>

          </div>

          <div className="card">

            <p>Research Instances</p>

            <h2>
              {Number(
                researchDashboard
                  ?.infrastructure_summary
                  ?.total_instances ?? 0
              )}
            </h2>

          </div>

          <div className="card">

            <p>Optimization Opportunities</p>

            <h2>
              {Number(
                researchDashboard
                  ?.optimization_summary
                  ?.optimization_opportunities ?? 0
              )}
            </h2>

          </div>

          <div className="card">

            <p>30-Day Research Cost</p>

            <h2>
              $
              {Number(
                researchDashboard?.cost_summary
                  ?.total_cost_usd ?? 0
              ).toFixed(2)}
            </h2>

          </div>

        </div>

      </section>

      {/* ========================================
          Optimization Scan History
      ======================================== */}

      <section className="history-section">

        <div className="section-header">

          <div>

            <h2>
              Optimization Scan History
            </h2>

            <p>
              Historical EC2 optimization scan results
              stored in PostgreSQL.
            </p>

          </div>

        </div>

        {history.length === 0 ? (

          <div className="no-data">
            No optimization scan history available.
          </div>

        ) : (

          <div className="table-container">

            <table className="recommendations-table">

              <thead>

                <tr>
                  <th>Scan ID</th>
                  <th>Instance ID</th>
                  <th>Type</th>
                  <th>CPU Usage</th>
                  <th>Status</th>
                  <th>Monthly Cost</th>
                  <th>Savings</th>
                  <th>Carbon Reduction</th>
                  <th>Scan Time</th>
                </tr>

              </thead>

              <tbody>

                {history.map((item) => (

                  <tr key={item.id}>

                    <td>
                      #{item.id}
                    </td>

                    <td className="instance-id">
                      {item.instance_id}
                    </td>

                    <td>
                      {item.instance_type}
                    </td>

                    <td>

                      {Number(
                        item.average_cpu_24h ?? 0
                      ).toFixed(2)}
                      %

                    </td>

                    <td>

                      <span
                        className={`status-badge ${
                          item.optimization_status
                            ?.toLowerCase() || ""
                        }`}
                      >

                        {item.optimization_status}

                      </span>

                    </td>

                    <td>

                      $
                      {Number(
                        item.estimated_monthly_cost_usd ??
                          0
                      ).toFixed(2)}

                    </td>

                    <td>

                      $
                      {Number(
                        item.potential_monthly_savings_usd ??
                          0
                      ).toFixed(2)}

                    </td>

                    <td>

                      {Number(
                        item.potential_carbon_reduction_kg ??
                          0
                      ).toFixed(3)}
                      {" "}kg

                    </td>

                    <td className="scan-time">

                      {item.created_at
                        ? new Date(
                            item.created_at
                          ).toLocaleString()
                        : "N/A"}

                    </td>

                  </tr>

                ))}

              </tbody>

            </table>

          </div>

        )}

      </section>

      {/* ========================================
          Historical Analytics
      ======================================== */}

      <section className="analytics-section">

        <div className="section-header">

          <div>

            <h2>
              Historical Analytics
            </h2>

            <p>
              Track EC2 utilization, cost savings,
              and carbon reduction across optimization
              scans.
            </p>

          </div>

        </div>

        {historicalChartData.length === 0 ? (

          <div className="no-data">
            No historical analytics data available.
          </div>

        ) : (

          <div className="charts-grid">

            {/* ==================================
                CPU Utilization Trend
            ================================== */}

            <div className="chart-card">

              <h3>
                CPU Utilization Trend
              </h3>

              <p className="chart-description">
                Historical average CPU utilization
                recorded during optimization scans.
              </p>

              <div className="chart-wrapper">

                <ResponsiveContainer
                  width="100%"
                  height={300}
                >

                  <LineChart
                    data={historicalChartData}
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#334155"
                    />

                    <XAxis
                      dataKey="scanId"
                      stroke="#94a3b8"
                    />

                    <YAxis
                      stroke="#94a3b8"
                      unit="%"
                    />

                    <Tooltip
                      contentStyle={{
                        backgroundColor:
                          "#1e293b",
                        border:
                          "1px solid #334155",
                        borderRadius: "8px",
                      }}
                      formatter={(value) => [
                        `${Number(
                          value
                        ).toFixed(2)}%`,
                        "CPU Usage",
                      ]}
                    />

                    <Line
                      type="monotone"
                      dataKey="cpu"
                      name="CPU Usage"
                      stroke="#3b82f6"
                      strokeWidth={3}
                    />

                  </LineChart>

                </ResponsiveContainer>

              </div>

            </div>

            {/* ==================================
                Cost Savings Trend
            ================================== */}

            <div className="chart-card">

              <h3>
                Cost Savings Trend
              </h3>

              <p className="chart-description">
                Potential monthly savings identified
                during each optimization scan.
              </p>

              <div className="chart-wrapper">

                <ResponsiveContainer
                  width="100%"
                  height={300}
                >

                  <LineChart
                    data={historicalChartData}
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#334155"
                    />

                    <XAxis
                      dataKey="scanId"
                      stroke="#94a3b8"
                    />

                    <YAxis
                      stroke="#94a3b8"
                    />

                    <Tooltip
                      contentStyle={{
                        backgroundColor:
                          "#1e293b",
                        border:
                          "1px solid #334155",
                        borderRadius: "8px",
                      }}
                      formatter={(value) => [
                        `$${Number(
                          value
                        ).toFixed(2)}`,
                        "Potential Savings",
                      ]}
                    />

                    <Line
                      type="monotone"
                      dataKey="savings"
                      name="Potential Savings"
                      stroke="#22c55e"
                      strokeWidth={3}
                    />

                  </LineChart>

                </ResponsiveContainer>

              </div>

            </div>

            {/* ==================================
                Carbon Reduction Trend
            ================================== */}

            <div className="chart-card">

              <h3>
                Carbon Reduction Trend
              </h3>

              <p className="chart-description">
                Potential carbon reduction identified
                across historical optimization scans.
              </p>

              <div className="chart-wrapper">

                <ResponsiveContainer
                  width="100%"
                  height={300}
                >

                  <LineChart
                    data={historicalChartData}
                  >

                    <CartesianGrid
                      strokeDasharray="3 3"
                      stroke="#334155"
                    />

                    <XAxis
                      dataKey="scanId"
                      stroke="#94a3b8"
                    />

                    <YAxis
                      stroke="#94a3b8"
                    />

                    <Tooltip
                      contentStyle={{
                        backgroundColor:
                          "#1e293b",
                        border:
                          "1px solid #334155",
                        borderRadius: "8px",
                      }}
                      formatter={(value) => [
                        `${Number(
                          value
                        ).toFixed(3)} kg`,
                        "Carbon Reduction",
                      ]}
                    />

                    <Line
                      type="monotone"
                      dataKey="carbonReduction"
                      name="Carbon Reduction"
                      stroke="#10b981"
                      strokeWidth={3}
                    />

                  </LineChart>

                </ResponsiveContainer>

              </div>

            </div>

          </div>

        )}

      </section>

    </div>
  );
}

export default App;