const API_URL = "https://f7v86e33l0.execute-api.us-east-1.amazonaws.com/default/iot-query";

let allData = [];
let lastRefreshTime = null;
let charts = {};

async function fetchData() {
  const res = await fetch(API_URL);
  if (!res.ok) throw new Error(`HTTP error! Status: ${res.status}`);
  return await res.json();
}

function setStatus(ok, text) {
  const dot = document.getElementById("status-dot");
  const statusText = document.getElementById("status-text");
  dot.style.background = ok ? "#22c55e" : "#ef4444";
  dot.style.boxShadow = ok ? "0 0 8px #22c55e" : "0 0 8px #ef4444";
  statusText.textContent = text;
}

function updateLastRefresh() {
  const el = document.getElementById("last-refresh");
  el.textContent = lastRefreshTime ? `Last: ${lastRefreshTime.toLocaleTimeString()}` : "—";
}

function groupByType(data) {
  return data.reduce((acc, item) => {
    acc[item.sensor_type] = acc[item.sensor_type] || [];
    acc[item.sensor_type].push(item);
    return acc;
  }, {});
}

function createKpis(groups) {
  const kpiGrid = document.getElementById("kpi-grid");
  kpiGrid.innerHTML = "";

  const types = Object.keys(groups);
  if (!types.length) {
    kpiGrid.innerHTML = `<div class="kpi-card">No data yet</div>`;
    return;
  }

  types.forEach(type => {
    const items = groups[type].slice(0, 20);
    const values = items.map(x => x.value);
    const avg = (values.reduce((a,b)=>a+b,0)/values.length).toFixed(2);
    const min = Math.min(...values).toFixed(2);
    const max = Math.max(...values).toFixed(2);
    const latest = items[0];

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

function createCharts(groups) {
  const chartGrid = document.getElementById("chart-grid");
  chartGrid.innerHTML = "";

  const types = Object.keys(groups);
  if (!types.length) return;

  types.forEach(type => {
    const card = document.createElement("div");
    card.className = "chart-card";
    card.innerHTML = `
      <h3 style="margin-top:0">${type.toUpperCase()} Trend</h3>
      <canvas id="chart-${type}" height="200"></canvas>
    `;
    chartGrid.appendChild(card);

    const ctx = document.getElementById(`chart-${type}`);
    const readings = groups[type].slice(0, 20).reverse();

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
          tension: 0.35,
          borderWidth: 2
        }]
      },
      options: {
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: "#94a3b8" } },
          y: { ticks: { color: "#94a3b8" } }
        }
      }
    });
  });
}

function updateAlerts(groups) {
  const banner = document.getElementById("alert-banner");
  let alerts = [];

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
    banner.style.display = "none";
  }
}

function updateTable() {
  const tbody = document.querySelector("#readings-table tbody");
  tbody.innerHTML = "";

  const sorted = [...allData].sort((a,b)=>b.timestamp-a.timestamp).slice(0,12);
  sorted.forEach(item => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${new Date(item.timestamp*1000).toLocaleTimeString()}</td>
      <td>${item.sensor_type}</td>
      <td>${item.value}</td>
      <td>${item.unit}</td>
    `;
    tbody.appendChild(row);
  });
}

async function updateDashboard() {
  try {
    const raw = await fetchData();

    // Handle array or {items: []} or {body:"[...]"}
    let data = Array.isArray(raw) ? raw : (raw.items || []);
    if (!Array.isArray(data) && raw.body) {
      data = JSON.parse(raw.body);
    }

    // Sort by newest first
    allData = data.sort((a, b) => b.timestamp - a.timestamp);

    lastRefreshTime = new Date();
    setStatus(true, "Live");
    updateLastRefresh();

    const groups = groupByType(allData);

    createKpis(groups);
    createCharts(groups);
    updateAlerts(groups);
    updateTable();
  } catch (err) {
    console.error(err);
    setStatus(false, "Offline");
  }
}

function manualRefresh() {
  updateDashboard();
}

function exportToCSV() {
  if (!allData.length) return alert("No data yet");
  let csv = "Timestamp,Sensor Type,Value,Unit\n";
  allData.forEach(item => {
    csv += `${new Date(item.timestamp*1000).toISOString()},${item.sensor_type},${item.value},${item.unit}\n`;
  });
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `iot-data-${new Date().toISOString().slice(0,19)}.csv`;
  a.click();
}

setInterval(updateDashboard, 5000);
updateDashboard();