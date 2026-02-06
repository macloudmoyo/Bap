"""Dashboard generator — produces a self-contained HTML dashboard from BAP results."""

import json
from pathlib import Path

from .models import BapScoreResult, Rating, RATING_COLOURS


def _results_to_json(results: list[BapScoreResult]) -> str:
    """Serialize results for embedding in the HTML."""
    data = []
    for r in results:
        data.append({
            "name": r.campaign_name,
            "format": r.ad_format.value,
            "icp_size": r.icp_size,
            "reach": r.reach,
            "ap": r.ap,
            "aqi": r.aqi,
            "bap": r.bap,
            "spend": r.spend,
            "bap_per_1k": r.bap_per_1k,
            "cost_per_bap": r.cost_per_bap,
            "rating": r.rating.value,
            "dwell_index": r.dwell_index,
            "ctr_index": r.ctr_index,
            "view_index": r.view_index,
            "completion_index": r.completion_index,
            "recommendations": r.recommendations,
        })
    return json.dumps(data, indent=2)


def generate_dashboard(results: list[BapScoreResult], output_path: str | Path) -> None:
    """Generate a self-contained HTML dashboard file."""
    output_path = Path(output_path)
    data_json = _results_to_json(results)

    html = _DASHBOARD_TEMPLATE.replace("/* __DATA_PLACEHOLDER__ */", data_json)
    output_path.write_text(html, encoding="utf-8")


_DASHBOARD_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>BAP Dashboard — Humble Roots</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
<style>
  :root {
    --bg: #0f172a;
    --surface: #1e293b;
    --surface2: #334155;
    --text: #f1f5f9;
    --text-muted: #94a3b8;
    --border: #475569;
    --poor: #ef4444;
    --good: #f59e0b;
    --great: #22c55e;
    --excellent: #3b82f6;
    --elite: #a855f7;
    --accent: #38bdf8;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.6;
    padding: 24px;
  }

  .header {
    text-align: center;
    margin-bottom: 32px;
    padding-bottom: 24px;
    border-bottom: 1px solid var(--border);
  }
  .header h1 {
    font-size: 28px;
    font-weight: 700;
    background: linear-gradient(135deg, var(--accent), var(--elite));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .header p { color: var(--text-muted); margin-top: 4px; }

  /* KPI Cards */
  .kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 16px;
    margin-bottom: 32px;
  }
  .kpi-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    text-align: center;
  }
  .kpi-card .label { color: var(--text-muted); font-size: 13px; text-transform: uppercase; letter-spacing: 0.5px; }
  .kpi-card .value { font-size: 32px; font-weight: 700; margin-top: 4px; }
  .kpi-card .sub { color: var(--text-muted); font-size: 12px; margin-top: 2px; }

  /* Chart grid */
  .chart-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(480px, 1fr));
    gap: 24px;
    margin-bottom: 32px;
  }
  .chart-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
  }
  .chart-card h3 {
    font-size: 16px;
    margin-bottom: 16px;
    color: var(--text-muted);
  }
  .chart-card canvas { width: 100% !important; }

  /* Campaign table */
  .table-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 32px;
    overflow-x: auto;
  }
  .table-card h3 { font-size: 16px; margin-bottom: 16px; color: var(--text-muted); }

  table {
    width: 100%;
    border-collapse: collapse;
    font-size: 14px;
  }
  th {
    text-align: left;
    padding: 10px 12px;
    border-bottom: 2px solid var(--border);
    color: var(--text-muted);
    font-weight: 600;
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    white-space: nowrap;
  }
  td {
    padding: 10px 12px;
    border-bottom: 1px solid var(--surface2);
    white-space: nowrap;
  }
  tr:hover td { background: var(--surface2); }

  .badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 9999px;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }
  .badge-poor       { background: rgba(239,68,68,0.15); color: var(--poor); }
  .badge-good       { background: rgba(245,158,11,0.15); color: var(--good); }
  .badge-great      { background: rgba(34,197,94,0.15); color: var(--great); }
  .badge-excellent   { background: rgba(59,130,246,0.15); color: var(--excellent); }
  .badge-elite      { background: rgba(168,85,247,0.15); color: var(--elite); }

  /* Recommendations */
  .recs-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 32px;
  }
  .recs-card h3 { font-size: 16px; margin-bottom: 16px; color: var(--text-muted); }
  .rec-campaign { margin-bottom: 20px; }
  .rec-campaign h4 {
    font-size: 15px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .rec-list { list-style: none; padding: 0; }
  .rec-list li {
    padding: 8px 12px;
    margin-bottom: 6px;
    background: var(--surface2);
    border-radius: 8px;
    font-size: 13px;
    line-height: 1.5;
    border-left: 3px solid var(--accent);
  }

  .footer {
    text-align: center;
    color: var(--text-muted);
    font-size: 12px;
    padding-top: 24px;
    border-top: 1px solid var(--border);
  }
</style>
</head>
<body>

<div class="header">
  <h1>Humble Roots BAP Dashboard</h1>
  <p>Brand Awareness Penetration — Campaign Performance</p>
</div>

<div class="kpi-grid" id="kpi-grid"></div>
<div class="chart-grid">
  <div class="chart-card">
    <h3>BAP Score by Campaign</h3>
    <canvas id="bapBarChart"></canvas>
  </div>
  <div class="chart-card">
    <h3>Rating Distribution</h3>
    <canvas id="ratingPieChart"></canvas>
  </div>
  <div class="chart-card">
    <h3>AQI Breakdown (Quality Indices)</h3>
    <canvas id="aqiRadarChart"></canvas>
  </div>
  <div class="chart-card">
    <h3>BAP vs Spend Efficiency</h3>
    <canvas id="efficiencyChart"></canvas>
  </div>
  <div class="chart-card">
    <h3>Performance by Ad Format</h3>
    <canvas id="formatChart"></canvas>
  </div>
  <div class="chart-card">
    <h3>Awareness Penetration (AP) by Campaign</h3>
    <canvas id="apChart"></canvas>
  </div>
</div>

<div class="table-card">
  <h3>Campaign Scorecard</h3>
  <table id="scorecard-table">
    <thead>
      <tr>
        <th>Campaign</th>
        <th>Format</th>
        <th>ICP Size</th>
        <th>Reach</th>
        <th>AP</th>
        <th>AQI</th>
        <th>BAP</th>
        <th>Spend</th>
        <th>BAP/£1k</th>
        <th>Cost/BAP</th>
        <th>Rating</th>
      </tr>
    </thead>
    <tbody id="scorecard-body"></tbody>
  </table>
</div>

<div class="recs-card">
  <h3>Recommendations</h3>
  <div id="recs-container"></div>
</div>

<div class="footer">
  Humble Roots BAP Framework &mdash; Brand Awareness Penetration Scoring
</div>

<script>
const DATA = /* __DATA_PLACEHOLDER__ */[];

const RATING_COLORS = {
  'Poor': '#ef4444',
  'Good': '#f59e0b',
  'Great': '#22c55e',
  'Excellent': '#3b82f6',
  'Elite': '#a855f7',
};

Chart.defaults.color = '#94a3b8';
Chart.defaults.borderColor = '#334155';

// ── KPI Cards ──────────────────────────────────────────────────────────
function renderKPIs() {
  const grid = document.getElementById('kpi-grid');
  const totalCampaigns = DATA.length;
  const avgBap = DATA.reduce((s, d) => s + d.bap, 0) / totalCampaigns;
  const totalSpend = DATA.reduce((s, d) => s + d.spend, 0);
  const totalReach = DATA.reduce((s, d) => s + d.reach, 0);
  const avgAqi = DATA.reduce((s, d) => s + d.aqi, 0) / totalCampaigns;
  const bestCampaign = DATA.reduce((best, d) => d.bap > best.bap ? d : best, DATA[0]);

  const kpis = [
    { label: 'Campaigns', value: totalCampaigns, sub: 'active' },
    { label: 'Avg BAP', value: avgBap.toFixed(1), sub: 'brand awareness score', color: RATING_COLORS[getOverallRating(avgBap)] },
    { label: 'Avg AQI', value: avgAqi.toFixed(1), sub: 'quality index' },
    { label: 'Total Reach', value: totalReach.toLocaleString(), sub: 'unique people' },
    { label: 'Total Spend', value: '£' + totalSpend.toLocaleString(undefined, {minimumFractionDigits: 0}), sub: 'investment' },
    { label: 'Top Campaign', value: bestCampaign.bap.toFixed(1), sub: bestCampaign.name, color: RATING_COLORS[bestCampaign.rating] },
  ];

  grid.innerHTML = kpis.map(k => `
    <div class="kpi-card">
      <div class="label">${k.label}</div>
      <div class="value" style="${k.color ? 'color:' + k.color : ''}">${k.value}</div>
      <div class="sub">${k.sub}</div>
    </div>
  `).join('');
}

function getOverallRating(bap) {
  if (bap < 5) return 'Poor';
  if (bap < 15) return 'Good';
  if (bap < 30) return 'Great';
  if (bap < 50) return 'Excellent';
  return 'Elite';
}

// ── BAP Bar Chart ──────────────────────────────────────────────────────
function renderBapBar() {
  const sorted = [...DATA].sort((a, b) => b.bap - a.bap);
  new Chart(document.getElementById('bapBarChart'), {
    type: 'bar',
    data: {
      labels: sorted.map(d => d.name.length > 25 ? d.name.substring(0, 22) + '...' : d.name),
      datasets: [{
        label: 'BAP Score',
        data: sorted.map(d => d.bap),
        backgroundColor: sorted.map(d => RATING_COLORS[d.rating] + '99'),
        borderColor: sorted.map(d => RATING_COLORS[d.rating]),
        borderWidth: 1,
        borderRadius: 6,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { title: { display: true, text: 'BAP Score' }, grid: { color: '#1e293b' } },
        y: { grid: { display: false } }
      }
    }
  });
}

// ── Rating Pie Chart ───────────────────────────────────────────────────
function renderRatingPie() {
  const counts = {};
  DATA.forEach(d => { counts[d.rating] = (counts[d.rating] || 0) + 1; });
  const ratings = Object.keys(counts);

  new Chart(document.getElementById('ratingPieChart'), {
    type: 'doughnut',
    data: {
      labels: ratings,
      datasets: [{
        data: ratings.map(r => counts[r]),
        backgroundColor: ratings.map(r => RATING_COLORS[r]),
        borderColor: '#1e293b',
        borderWidth: 3,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'bottom' }
      }
    }
  });
}

// ── AQI Radar Chart ────────────────────────────────────────────────────
function renderAqiRadar() {
  // Show top 5 campaigns by BAP
  const top = [...DATA].sort((a, b) => b.bap - a.bap).slice(0, 5);
  const labels = ['Dwell Index', 'CTR Index', 'View Index', 'Completion Index'];

  new Chart(document.getElementById('aqiRadarChart'), {
    type: 'radar',
    data: {
      labels: labels,
      datasets: top.map((d, i) => ({
        label: d.name.length > 20 ? d.name.substring(0, 17) + '...' : d.name,
        data: [d.dwell_index, d.ctr_index, d.view_index, d.completion_index],
        borderColor: Object.values(RATING_COLORS)[i % 5],
        backgroundColor: Object.values(RATING_COLORS)[i % 5] + '20',
        borderWidth: 2,
        pointRadius: 3,
      }))
    },
    options: {
      responsive: true,
      scales: {
        r: {
          beginAtZero: true,
          grid: { color: '#334155' },
          angleLines: { color: '#334155' },
          pointLabels: { color: '#94a3b8', font: { size: 11 } },
          ticks: { color: '#94a3b8', backdropColor: 'transparent' },
        }
      },
      plugins: { legend: { position: 'bottom', labels: { font: { size: 11 } } } }
    }
  });
}

// ── Efficiency Scatter ─────────────────────────────────────────────────
function renderEfficiency() {
  new Chart(document.getElementById('efficiencyChart'), {
    type: 'scatter',
    data: {
      datasets: [{
        label: 'Campaigns',
        data: DATA.map(d => ({ x: d.spend, y: d.bap, label: d.name })),
        backgroundColor: DATA.map(d => RATING_COLORS[d.rating] + 'cc'),
        borderColor: DATA.map(d => RATING_COLORS[d.rating]),
        borderWidth: 1,
        pointRadius: 8,
        pointHoverRadius: 12,
      }]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const d = DATA[ctx.dataIndex];
              return `${d.name}: BAP ${d.bap} | Spend £${d.spend} | £${d.cost_per_bap}/BAP`;
            }
          }
        }
      },
      scales: {
        x: { title: { display: true, text: 'Spend (£)' }, grid: { color: '#1e293b' } },
        y: { title: { display: true, text: 'BAP Score' }, grid: { color: '#1e293b' } }
      }
    }
  });
}

// ── Format Comparison ──────────────────────────────────────────────────
function renderFormatChart() {
  const formats = {};
  DATA.forEach(d => {
    if (!formats[d.format]) formats[d.format] = { bap: [], aqi: [], ap: [] };
    formats[d.format].bap.push(d.bap);
    formats[d.format].aqi.push(d.aqi);
    formats[d.format].ap.push(d.ap);
  });

  const fmtLabels = Object.keys(formats);
  const avgBap = fmtLabels.map(f => formats[f].bap.reduce((s, v) => s + v, 0) / formats[f].bap.length);
  const avgAqi = fmtLabels.map(f => formats[f].aqi.reduce((s, v) => s + v, 0) / formats[f].aqi.length);

  new Chart(document.getElementById('formatChart'), {
    type: 'bar',
    data: {
      labels: fmtLabels,
      datasets: [
        {
          label: 'Avg BAP',
          data: avgBap,
          backgroundColor: '#3b82f699',
          borderColor: '#3b82f6',
          borderWidth: 1,
          borderRadius: 6,
        },
        {
          label: 'Avg AQI',
          data: avgAqi,
          backgroundColor: '#a855f799',
          borderColor: '#a855f7',
          borderWidth: 1,
          borderRadius: 6,
        }
      ]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'bottom' } },
      scales: {
        x: { grid: { display: false } },
        y: { grid: { color: '#1e293b' } }
      }
    }
  });
}

// ── AP Bar Chart ───────────────────────────────────────────────────────
function renderApChart() {
  const sorted = [...DATA].sort((a, b) => b.ap - a.ap);
  new Chart(document.getElementById('apChart'), {
    type: 'bar',
    data: {
      labels: sorted.map(d => d.name.length > 25 ? d.name.substring(0, 22) + '...' : d.name),
      datasets: [{
        label: 'AP (Awareness Penetration)',
        data: sorted.map(d => (d.ap * 100)),
        backgroundColor: '#38bdf899',
        borderColor: '#38bdf8',
        borderWidth: 1,
        borderRadius: 6,
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { title: { display: true, text: 'AP (%)' }, grid: { color: '#1e293b' } },
        y: { grid: { display: false } }
      }
    }
  });
}

// ── Scorecard Table ────────────────────────────────────────────────────
function renderTable() {
  const body = document.getElementById('scorecard-body');
  const sorted = [...DATA].sort((a, b) => b.bap - a.bap);

  body.innerHTML = sorted.map(d => `
    <tr>
      <td><strong>${d.name}</strong></td>
      <td>${d.format}</td>
      <td>${d.icp_size.toLocaleString()}</td>
      <td>${d.reach.toLocaleString()}</td>
      <td>${(d.ap * 100).toFixed(1)}%</td>
      <td>${d.aqi.toFixed(2)}</td>
      <td><strong>${d.bap.toFixed(2)}</strong></td>
      <td>£${d.spend.toLocaleString()}</td>
      <td>${d.bap_per_1k.toFixed(2)}</td>
      <td>£${d.cost_per_bap.toFixed(2)}</td>
      <td><span class="badge badge-${d.rating.toLowerCase()}">${d.rating}</span></td>
    </tr>
  `).join('');
}

// ── Recommendations ────────────────────────────────────────────────────
function renderRecs() {
  const container = document.getElementById('recs-container');
  const sorted = [...DATA].sort((a, b) => a.bap - b.bap);  // worst first

  container.innerHTML = sorted
    .filter(d => d.recommendations.length > 0)
    .map(d => `
      <div class="rec-campaign">
        <h4>
          <span class="badge badge-${d.rating.toLowerCase()}">${d.rating}</span>
          ${d.name}
          <span style="color:var(--text-muted);font-weight:400;font-size:13px">(BAP: ${d.bap.toFixed(2)})</span>
        </h4>
        <ul class="rec-list">
          ${d.recommendations.map(r => `<li>${r}</li>`).join('')}
        </ul>
      </div>
    `).join('');
}

// ── Init ───────────────────────────────────────────────────────────────
if (DATA.length > 0) {
  renderKPIs();
  renderBapBar();
  renderRatingPie();
  renderAqiRadar();
  renderEfficiency();
  renderFormatChart();
  renderApChart();
  renderTable();
  renderRecs();
} else {
  document.body.innerHTML = `
    <div style="text-align:center;padding:60px">
      <h1 style="color:var(--text-muted)">No Data</h1>
      <p style="color:var(--text-muted)">Run: python -m bap dashboard your_data.csv</p>
    </div>
  `;
}
</script>
</body>
</html>
"""
