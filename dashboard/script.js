// Dashboard frontend for the FEC IoT project.
// This script is responsible for everything the user sees — fetching data from AWS,
// rendering the KPI cards, drawing the trend charts, checking alert thresholds,
// and filling the recent readings table. It auto-refreshes every 5 seconds so
// the dashboard stays "live" without the user needing to manually reload.
//
// The data flow is: AWS DynamoDB → iot-query Lambda → API Gateway → this script → DOM

// API Gateway URL for the iot-query Lambda function.
// This endpoint returns up to 25 of the latest records per sensor type from DynamoDB.
const API_URL = "https://f7v86e33l0.execute-api.us-east-1.amazonaws.com/default/iot-query";

// We keep all fetched data in a module-level array so different functions
// (charts, table, alerts) can all reference the same dataset without re-fetching.
let allData = [];
let lastRefreshTime = null;

// Chart.js instances are stored here so we can destroy and recreate them on refresh.
// Without this, Chart.js would stack canvases on top of each other every update.
let charts = {};

// ── Data fetching ──────────────────────────────────────────────────────────────

async function fetchData() {
  // Simple fetch from the API Gateway endpoint — the Lambda handles auth & querying.
  // We throw on non-2xx responses so the catch block in updateDashboard handles it.
  const res = await fetch(API_URL);
  if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
  return await res.json();
}

// ── Status indicator ──────────────────────────────────────────────────────────

function setStatus(ok, text) {
  // Green dot = connected and receiving data; red dot = something went wrong.
  // The box-shadow creates the soft glow effect around the status dot.
  const dot = document.getElementById("status-dot");
  const statusText = document.getElementById("status-text");
  dot.style.background = ok ? "#22c55e" : "#ef4444";
  dot.style.boxShadow = ok ? "0 0 8px #22c55e" : "0 0 8px #ef4444";
  statusText.textContent = text;
}

function updateLastRefresh() {
  // Show users when the data was last successfully pulled so they know
  // if they're looking at stale data during a connection issue.
  const el = document.getElementById("last-refresh");
  el.textContent = lastRefreshTime ? `Last: ${lastRefreshTime.toLocaleTimeString()}` : "—";
}

// ── Data helpers ───────────────────────────────────────────────────────────────

function groupByType(data) {
  // Group the flat array of readings into an object keyed by sensor_type.
  // This makes it easy to render separate cards/charts for each sensor
  // without scanning the whole array every time.
  return data.reduce((acc, item) => {
    acc[item.sensor_type] = acc[item.sensor_type] || [];
    acc[item.sensor_type].push(item);
    return acc;
  }, {});
}

// ── KPI Cards ─────────────────────────────────────────────────────────────────

function createKpis(groups) {
  const kpiGrid = document.getElementById("kpi-grid");
  kpiGrid.innerHTML = "";   // clear old cards before redrawing

  const types = Object.keys(groups);
  if (!types.length) {
    kpiGrid.innerHTML = `<div class="kpi-card">No data yet</div>`;
    return;
  }

  types.forEach(type => {
    // Slice to the 20 most recent readings to keep the stats meaningful
    // (we don't want an old outlier dragging the average around)
    const items = groups[type].slice(0, 20);
    const values = items.map(x => x.value);
    const avg = (values.reduce((a,b)=>a+b,0)/values.length).toFixed(2);
    const min = Math.min(...values).toFixed(2);
    const max = Math.max(...values).toFixed(2);
    const latest = items[0];   // data is sorted newest-first, so index 0 is the most recent

    const card = document.createElement("div");
    card.className = "kpi-card";
    card.innerHTML = `
      <div class="kpi-title">${type.toUpperCase()}</div>
      <div class="kpi-value">${latest.value} ${latest.unit}</div>
      <div class="kpi-sub">Avg ${avg} • Min ${min} • Max ${max}</div>
    `;
    kpiGrid.appendChild(card);
  });
}

// ── Trend Charts ──────────────────────────────────────────────────────────────

function createCharts(groups) {
  const chartGrid = document.getElementById("chart-grid");
  chartGrid.innerHTML = "";   // clear and rebuild all charts on each refresh

  const types = Object.keys(groups);
  if (!types.length) return;

  types.forEach(type => {
    // Create a card container + canvas for each sensor type
    const card = document.createElement("div");
    card.className = "chart-card";
    card.innerHTML = `
      <h3 style="margin-top:0">${type.toUpperCase()} Trend</h3>
      <canvas id="chart-${type}" height="200"></canvas>
    `;
    chartGrid.appendChild(card);

    const ctx = document.getElementById(`chart-${type}`);

    // Data is sorted newest-first, but charts should read left-to-right chronologically,
    // so we reverse() before passing to Chart.js.
    const readings = groups[type].slice(0, 20).reverse();

    // Destroy the old chart instance if one exists — otherwise Chart.js throws an error
    // about the canvas already being in use.
    if (charts[type]) charts[type].destroy();

    charts[type] = new Chart(ctx, {
      type: "line",
      data: {
        labels: readings.map(r => new Date(r.timestamp * 1000).toLocaleTimeString()),
        datasets: [{
          data: readings.map(r => r.value),
          borderColor: "#38bdf8",
          backgroundColor: "rgba(56,189,248,0.15)",
          fill: true,
          tension: 0.35,   // slight curve makes the line look smoother / more natural
          borderWidth: 2
        }]
      },
      options: {
        plugins: { legend: { display: false } },   // no legend needed — the card title is enough
        scales: {
          x: { ticks: { color: "#94a3b8" } },
          y: { ticks: { color: "#94a3b8" } }
        }
      }
    });
  });
}

// ── Alert Banner ──────────────────────────────────────────────────────────────

function updateAlerts(groups) {
  const banner = document.getElementById("alert-banner");
  let alerts = [];

  // Mirror the same thresholds used in the fog node's processor.py
  // so alerts are consistent whether they come from the edge or the dashboard.
  if (groups.temperature) {
    const avg = groups.temperature.slice(0,20).reduce((a,b)=>a+b.value,0)/groups.temperature.slice(0,20).length;
    if (avg > 28) alerts.push("High temperature detected!");
  }
  if (groups.pm25) {
    const avg = groups.pm25.slice(0,20).reduce((a,b)=>a+b.value,0)/groups.pm25.slice(0,20).length;
    if (avg > 35) alerts.push("Poor air quality!");
  }

  if (alerts.length) {
    banner.style.display = "block";
    banner.textContent = "⚠️ " + alerts.join(" • ");
  } else {
    // Hide the banner entirely when everything is within normal range
    banner.style.display = "none";
  }
}

// ── Recent Readings Table ─────────────────────────────────────────────────────

function updateTable() {
  const tbody = document.querySelector("#readings-table tbody");
  tbody.innerHTML = "";

  // Sort by timestamp descending so newest readings appear at the top of the table,
  // then take the 12 most recent to keep the table a manageable size.
  const sorted = [...allData].sort((a,b)=>b.timestamp-a.timestamp).slice(0,12);
  sorted.forEach(item => {
    const row = document.createElement("tr");
    // Convert Unix timestamp (seconds) to a human-readable time string
    row.innerHTML = `
      <td>${new Date(item.timestamp*1000).toLocaleTimeString()}</td>
      <td>${item.sensor_type}</td>
      <td>${item.value}</td>
      <td>${item.unit}</td>
    `;
    tbody.appendChild(row);
  });
}

// ── Main update loop ──────────────────────────────────────────────────────────

async function updateDashboard() {
  try {
    const raw = await fetchData();

    // The Lambda can return data in a few different shapes depending on how API Gateway
    // is configured, so we handle all three cases here to be safe.
    let data = Array.isArray(raw) ? raw : (raw.items || []);
    if (!Array.isArray(data) && raw.body) {
      // API Gateway sometimes wraps the Lambda response body as a JSON string
      data = JSON.parse(raw.body);
    }

    // Keep data sorted newest-first throughout the app
    allData = data.sort((a, b) => b.timestamp - a.timestamp);

    lastRefreshTime = new Date();
    setStatus(true, "Live");
    updateLastRefresh();

    const groups = groupByType(allData);

    // Rebuild all UI components with fresh data
    createKpis(groups);
    createCharts(groups);
    updateAlerts(groups);
    updateTable();
  } catch (err) {
    // Don't crash the whole page — just show the offline indicator and log the error
    console.error(err);
    setStatus(false, "Offline");
  }
}

// Allows the user to force an immediate refresh by clicking the refresh button
function manualRefresh() {
  updateDashboard();
}

// ── CSV Export ────────────────────────────────────────────────────────────────

function exportToCSV() {
  if (!allData.length) return alert("No data yet");

  // Build the CSV string manually — no library needed for something this simple
  let csv = "Timestamp,Sensor Type,Value,Unit\n";
  allData.forEach(item => {
    // ISO format for timestamps makes the CSV easy to import into Excel or Google Sheets
    csv += `${new Date(item.timestamp*1000).toISOString()},${item.sensor_type},${item.value},${item.unit}\n`;
  });

  // Create a temporary download link and trigger it programmatically.
  // This is the standard browser trick for triggering file downloads from JavaScript.
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `iot-data-${new Date().toISOString().slice(0,19)}.csv`;
  a.click();
}

// ── Initialisation ────────────────────────────────────────────────────────────

// Poll every 5 seconds to keep the dashboard live without manual refreshes.
// This interval matches the sensor FREQUENCY_SEC in config.py, so we should
// see new data on roughly every refresh cycle.
setInterval(updateDashboard, 5000);

// Run immediately on page load so there's data visible straight away
// rather than waiting 5 seconds for the first interval tick.
updateDashboard();