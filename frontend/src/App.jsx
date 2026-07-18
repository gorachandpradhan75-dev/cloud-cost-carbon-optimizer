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
  getDashboardSummary,
  runOptimizationScan,
  getEC2Recommendations,
  getOptimizationHistory,
} from "./services/api";

import "./App.css";

function App() {
  const [summary, setSummary] = useState(null);
  const [recommendations, setRecommendations] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState(null);

  // Load dashboard summary and recommendations
  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);

      const [
  summaryData,
  recommendationsData,
  historyData,
] = await Promise.all([
  getDashboardSummary(),
  getEC2Recommendations(),
  getOptimizationHistory(),
]);

setSummary(summaryData);

setRecommendations(
  recommendationsData.recommendations || []
);

setHistory(
  historyData.history || []
);

    } catch (err) {
      console.error("Dashboard loading error:", err);

      setError(
        "Failed to load dashboard data. Make sure the backend server is running."
      );
    } finally {
      setLoading(false);
    }
  };

  // Load dashboard when application starts
  useEffect(() => {
    loadDashboard();
  }, []);

  // Run optimization scan
  const handleScan = async () => {
    try {
      setScanning(true);
      setError(null);

      await runOptimizationScan();

      // Refresh dashboard data after scan
      await loadDashboard();
    } catch (err) {
      console.error("Optimization scan error:", err);

      setError(
        "Optimization scan failed. Please check the backend server."
      );
    } finally {
      setScanning(false);
    }
  };

  // ================================
  // Chart Data
  // ================================

  // CPU utilization data for each EC2 instance
  const cpuChartData = recommendations.map(
    (item, index) => ({
      name: `EC2-${index + 1}`,
      instanceId: item.instance_id,
      cpu: Number(item.average_cpu_24h ?? 0),
    })
  );

  // Cost vs savings
  const costChartData = [
    {
      name: "Monthly Cost",
      value: Number(
        summary?.estimated_monthly_cost_usd ?? 0
      ),
    },
    {
      name: "Potential Savings",
      value: Number(
        summary?.potential_monthly_savings_usd ?? 0
      ),
    },
  ];

  // Carbon emissions vs reduction
  const carbonChartData = [
    {
      name: "Carbon Emissions",
      value: Number(
        summary?.estimated_carbon_kg_monthly ?? 0
      ),
    },
    {
      name: "Potential Reduction",
      value: Number(
        summary?.potential_carbon_reduction_kg ?? 0
      ),
    },
  ];
  // Historical analytics data
const historicalChartData = [...history]
  .sort((a, b) => a.id - b.id)
  .map((item) => ({
    scanId: `#${item.id}`,
    cpu: Number(item.average_cpu_24h ?? 0),
    cost: Number(item.estimated_monthly_cost_usd ?? 0),
    savings: Number(item.potential_monthly_savings_usd ?? 0),
    carbonReduction: Number(
      item.potential_carbon_reduction_kg ?? 0
    ),
    time: item.created_at
      ? new Date(item.created_at).toLocaleString()
      : "N/A",
  }));
  // ================================
  // Loading Screen
  // ================================

  if (loading && !summary) {
    return (
      <div className="loading">
        Loading dashboard...
      </div>
    );
  }

  // ================================
  // Error Screen
  // ================================

  if (error && !summary) {
    return (
      <div className="loading">
        {error}
      </div>
    );
  }

  return (
    <div className="dashboard">

      {/* ============================
          Dashboard Header
      ============================ */}

      <div className="dashboard-header">
        <div>
          <h1>Cloud Cost & Carbon Optimizer</h1>
          <p>Dashboard Overview</p>
        </div>

        <button
          className="scan-button"
          onClick={handleScan}
          disabled={scanning}
        >
          {scanning
            ? "Scanning..."
            : "Run Optimization Scan"}
        </button>
      </div>

      {/* Error Message */}

      {error && (
        <div className="error-message">
          {error}
        </div>
      )}

      {/* ============================
          Dashboard Summary Cards
      ============================ */}

      <div className="card-grid">

        <div className="card">
          <p>Total Instances</p>

          <h2>
            {summary?.total_instances ?? 0}
          </h2>
        </div>

        <div className="card">
          <p>Running Instances</p>

          <h2>
            {summary?.running_instances ?? 0}
          </h2>
        </div>

        <div className="card">
          <p>Idle Instances</p>

          <h2>
            {summary?.idle_instances ?? 0}
          </h2>
        </div>

        <div className="card">
          <p>Underutilized Instances</p>

          <h2>
            {summary?.underutilized_instances ?? 0}
          </h2>
        </div>

        <div className="card">
          <p>Optimized Instances</p>

          <h2>
            {summary?.optimized_instances ?? 0}
          </h2>
        </div>

        <div className="card">
          <p>Estimated Monthly Cost</p>

          <h2>
            $
            {Number(
              summary?.estimated_monthly_cost_usd ?? 0
            ).toFixed(2)}
          </h2>
        </div>

        <div className="card">
          <p>Potential Monthly Savings</p>

          <h2>
            $
            {Number(
              summary?.potential_monthly_savings_usd ?? 0
            ).toFixed(2)}
          </h2>
        </div>

        <div className="card">
          <p>Carbon Emissions</p>

          <h2>
            {Number(
              summary?.estimated_carbon_kg_monthly ?? 0
            ).toFixed(3)}{" "}
            kg/month
          </h2>
        </div>

        <div className="card">
          <p>Potential Carbon Reduction</p>

          <h2>
            {Number(
              summary?.potential_carbon_reduction_kg ?? 0
            ).toFixed(3)}{" "}
            kg
          </h2>
        </div>

      </div>

      {/* ============================
          Visual Analytics
      ============================ */}

      <section className="analytics-section">

        <div className="section-header">
          <div>
            <h2>Visual Analytics</h2>

            <p>
              Real-time visualization of EC2 utilization,
              cloud cost optimization, and carbon impact.
            </p>
          </div>
        </div>

        <div className="charts-grid">

          {/* ========================
              CPU Utilization Chart
          ======================== */}

          <div className="chart-card">

            <h3>EC2 CPU Utilization</h3>

            <p className="chart-description">
              Average CPU utilization over the last 24 hours.
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
                      border: "1px solid #334155",
                      borderRadius: "8px",
                    }}
                    labelStyle={{
                      color: "#f8fafc",
                    }}
                  />

                  <Bar
                    dataKey="cpu"
                    name="CPU Usage"
                    fill="#3b82f6"
                    radius={[6, 6, 0, 0]}
                  />

                </BarChart>
              </ResponsiveContainer>

            </div>

          </div>

          {/* ========================
              Cost vs Savings Chart
          ======================== */}

          <div className="chart-card">

            <h3>
              Cost vs Potential Savings
            </h3>

            <p className="chart-description">
              Estimated monthly cloud cost and optimization
              savings opportunity.
            </p>

            <div className="chart-wrapper">

              <ResponsiveContainer
                width="100%"
                height={300}
              >
                <BarChart data={costChartData}>

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
                      border: "1px solid #334155",
                      borderRadius: "8px",
                    }}
                    formatter={(value) => [
                      `$${Number(value).toFixed(2)}`,
                      "USD",
                    ]}
                  />

                  <Bar
                    dataKey="value"
                    name="USD"
                    fill="#22c55e"
                    radius={[6, 6, 0, 0]}
                  />

                </BarChart>
              </ResponsiveContainer>

            </div>

          </div>

          {/* ========================
              Carbon Impact Chart
          ======================== */}

          <div className="chart-card">

            <h3>
              Carbon Impact
            </h3>

            <p className="chart-description">
              Estimated monthly carbon emissions and potential
              carbon reduction.
            </p>

            <div className="chart-wrapper">

              <ResponsiveContainer
                width="100%"
                height={300}
              >
                <BarChart data={carbonChartData}>

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
                      border: "1px solid #334155",
                      borderRadius: "8px",
                    }}
                    formatter={(value) => [
                      `${Number(value).toFixed(3)} kg`,
                      "Carbon",
                    ]}
                  />

                  <Bar
                    dataKey="value"
                    name="Carbon"
                    fill="#10b981"
                    radius={[6, 6, 0, 0]}
                  />

                </BarChart>
              </ResponsiveContainer>

            </div>

          </div>

        </div>

      </section>

      {/* ============================
          Optimization Recommendations
      ============================ */}

      <section className="recommendations-section">

        <div className="section-header">

          <div>

            <h2>
              Optimization Recommendations
            </h2>

            <p>
              EC2 resource optimization insights based on CPU
              utilization, cost, and carbon impact.
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
                  <th>CPU Usage</th>
                  <th>Status</th>
                  <th>Monthly Cost</th>
                  <th>Potential Savings</th>
                  <th>Carbon</th>
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
                      {Number(
                        item.average_cpu_24h ?? 0
                      ).toFixed(2)}
                      %
                    </td>

                    <td>

                      <span
                        className={`status-badge ${
                          item.optimization_status
                            ?.toLowerCase()
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
                        item.estimated_carbon_kg_monthly ??
                          0
                      ).toFixed(3)}{" "}
                      kg
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
      {/* ============================
    Optimization Scan History
============================ */}

<section className="history-section">

  <div className="section-header">
    <div>
      <h2>Optimization Scan History</h2>

      <p>
        Historical EC2 optimization scan results stored
        in PostgreSQL.
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
                      ?.toLowerCase()
                  }`}
                >
                  {item.optimization_status}
                </span>
              </td>

              <td>
                $
                {Number(
                  item.estimated_monthly_cost_usd ?? 0
                ).toFixed(2)}
              </td>

              <td>
                $
                {Number(
                  item.potential_monthly_savings_usd ?? 0
                ).toFixed(2)}
              </td>

              <td>
                {Number(
                  item.potential_carbon_reduction_kg ?? 0
                ).toFixed(3)}{" "}
                kg
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
{/* ============================
    Historical Analytics
============================ */}

<section className="analytics-section">

  <div className="section-header">
    <div>
      <h2>Historical Analytics</h2>
      <p>
        Track EC2 utilization, cost savings, and carbon
        reduction across optimization scans.
      </p>
    </div>
  </div>

  {historicalChartData.length === 0 ? (

    <div className="no-data">
      No historical analytics data available.
    </div>

  ) : (

    <div className="charts-grid">

      {/* CPU Utilization Trend */}

      <div className="chart-card">

        <h3>CPU Utilization Trend</h3>

        <p className="chart-description">
          Historical average CPU utilization recorded during
          optimization scans.
        </p>

        <div className="chart-wrapper">

          <ResponsiveContainer
            width="100%"
            height={300}
          >

            <LineChart data={historicalChartData}>

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
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                }}
                formatter={(value) => [
                  `${Number(value).toFixed(2)}%`,
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


      {/* Cost Savings Trend */}

      <div className="chart-card">

        <h3>Cost Savings Trend</h3>

        <p className="chart-description">
          Potential monthly savings identified during each
          optimization scan.
        </p>

        <div className="chart-wrapper">

          <ResponsiveContainer
            width="100%"
            height={300}
          >

            <LineChart data={historicalChartData}>

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
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                }}
                formatter={(value) => [
                  `$${Number(value).toFixed(2)}`,
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


      {/* Carbon Reduction Trend */}

      <div className="chart-card">

        <h3>Carbon Reduction Trend</h3>

        <p className="chart-description">
          Potential carbon reduction identified across
          historical optimization scans.
        </p>

        <div className="chart-wrapper">

          <ResponsiveContainer
            width="100%"
            height={300}
          >

            <LineChart data={historicalChartData}>

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
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  borderRadius: "8px",
                }}
                formatter={(value) => [
                  `${Number(value).toFixed(3)} kg`,
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