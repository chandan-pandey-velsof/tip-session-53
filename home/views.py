import json
import requests as http_requests
from django.conf import settings
from django.http import HttpResponse


def index(request):
    """Patent Detail page — search by US application number, show patent info + cost estimate."""
    html = PAGE_HTML
    return HttpResponse(html, content_type="text/html")


PAGE_HTML = """\
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Patent Detail — TriangleIP</title>
<link rel='stylesheet' href='/static/tip_design.css'>
<style>
  .tip-search-row { display:flex; gap:12px; align-items:center; flex-wrap:wrap; }
  .tip-search-row input { flex:1; min-width:260px; padding:10px 14px; border:1px solid var(--tip-border, #d0d5dd); border-radius:8px; font-size:15px; font-family:inherit; }
  .tip-search-row input:focus { outline:none; border-color:var(--tip-primary); box-shadow:0 0 0 3px rgba(47,84,235,.15); }
  .tip-placeholder { text-align:center; padding:60px 20px; color:var(--tip-text-secondary, #667085); }
  .tip-placeholder svg { margin-bottom:16px; opacity:.35; }
  .tip-error-card { border-left:4px solid var(--tip-color-error, #d92d20); }
  .tip-error-card .tip-card-title { color:var(--tip-color-error, #d92d20); }
  .tip-stats-row { display:grid; grid-template-columns:repeat(auto-fill, minmax(200px, 1fr)); gap:16px; }
  .tip-card-value { font-size:28px; font-weight:700; color:var(--tip-primary); line-height:1.2; }
  .tip-card-label { font-size:13px; color:var(--tip-text-secondary, #667085); margin-top:4px; }
  .tip-section-title { font-size:18px; font-weight:600; margin:32px 0 16px; color:var(--tip-text-primary, #101828); }
  .tip-cost-grid { display:grid; grid-template-columns:repeat(auto-fill, minmax(220px, 1fr)); gap:16px; }
  .tip-maint-table { width:100%; border-collapse:collapse; }
  .tip-maint-table th, .tip-maint-table td { padding:10px 14px; text-align:left; border-bottom:1px solid var(--tip-border, #d0d5dd); font-size:14px; }
  .tip-maint-table th { font-weight:600; color:var(--tip-text-secondary, #667085); font-size:12px; text-transform:uppercase; letter-spacing:.5px; }
  .tip-maint-table td:last-child { font-weight:600; color:var(--tip-primary); }
  .tip-diagnostics summary { cursor:pointer; font-weight:600; font-size:14px; color:var(--tip-text-secondary, #667085); }
  .tip-diagnostics pre { background:#f9fafb; border:1px solid var(--tip-border, #d0d5dd); border-radius:8px; padding:16px; font-size:12px; overflow-x:auto; white-space:pre-wrap; word-break:break-all; margin-top:8px; }
  .tip-diagnostics table { width:100%; border-collapse:collapse; font-size:13px; margin-top:8px; }
  .tip-diagnostics th, .tip-diagnostics td { padding:6px 10px; border-bottom:1px solid var(--tip-border, #d0d5dd); text-align:left; }
  .tip-diagnostics th { font-weight:600; color:var(--tip-text-secondary, #667085); font-size:11px; text-transform:uppercase; }
  .hidden { display:none !important; }
  .tag-patented { background:#ecfdf3; color:#067a4e; }
  .tag-pending { background:#fef9c3; color:#92600a; }
  .tag-abandoned { background:#fef2f2; color:#b42318; }
  .tag-expired { background:#f3f4f6; color:#475467; }
  .tag-default { background:#f3f4f6; color:#475467; }
</style>
</head>
<body>
<div class="tip-page">

  <nav class="tip-navbar">
    <a class="tip-navbar-brand" href="/">TriangleIP</a>
  </nav>

  <h1 class="tip-page-title">Patent Detail</h1>

  <!-- Search -->
  <div class="tip-card" style="margin-bottom:24px;">
    <div class="tip-search-row">
      <input type="text" id="searchInput" placeholder="Enter US application number (e.g. 16/687,273)" autocomplete="off" />
      <button class="tip-btn tip-btn-primary" id="searchBtn" onclick="doSearch()">Search</button>
    </div>
    <div id="suggestions" style="margin-top:8px;"></div>
  </div>

  <!-- Placeholder -->
  <div id="placeholder" class="tip-placeholder">
    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>
    <p style="font-size:16px;">Enter a US application number above to view patent details and cost estimates.</p>
  </div>

  <!-- Error -->
  <div id="errorCard" class="tip-card tip-error-card hidden" style="margin-bottom:24px;">
    <div class="tip-card-title">Error</div>
    <div id="errorMsg" style="color:var(--tip-text-secondary); margin-top:8px;"></div>
  </div>

  <!-- Patent Info -->
  <div id="patentSection" class="hidden">
    <h2 class="tip-section-title">Patent Information</h2>
    <div class="tip-card" style="margin-bottom:8px;">
      <div id="patentTitle" style="font-size:20px; font-weight:700; line-height:1.4; margin-bottom:16px;"></div>
      <div class="tip-stats-row" id="patentStats"></div>
    </div>
  </div>

  <!-- Cost Details -->
  <div id="costSection" class="hidden">
    <h2 class="tip-section-title">Cost Details</h2>
    <div class="tip-card" style="margin-bottom:16px;">
      <div class="tip-cost-grid" id="costStats"></div>
    </div>
    <div class="tip-card">
      <div style="font-weight:600; margin-bottom:12px;">Maintenance Fee Breakdown</div>
      <div class="tip-table-wrap">
        <table class="tip-table tip-maint-table" id="maintTable">
          <thead><tr><th>Period</th><th>Fee</th></tr></thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- Diagnostics -->
  <div class="tip-card tip-diagnostics" style="margin-top:40px;">
    <details>
      <summary>Diagnostics</summary>
      <div id="diagContent">
        <p style="color:var(--tip-text-secondary); margin-top:8px;">No API calls made yet.</p>
      </div>
    </details>
  </div>

</div>

<script>
const USER_REQUEST = "Build a patent detail page. Type a US application number and submit. Call patent-lookup search API and show patent title, patent number, status, filing date, grant date, examiner, and group art unit in cards. Then call the prosecution cost-estimate endpoint and show Cost Details: predicted cost, cost with maintenance, next cost, and maintenance-fee breakdown by year. Show placeholder before searching and error card on failure. Include diagnostics panel.";

let diagCalls = [];

function addDiag(method, path, inputParams, outputParams, fieldMapping) {
  diagCalls.push({ method, path, inputParams, outputParams, fieldMapping });
}

function renderDiagnostics() {
  const el = document.getElementById('diagContent');
  if (!diagCalls.length) {
    el.innerHTML = '<p style="color:var(--tip-text-secondary); margin-top:8px;">No API calls made yet.</p>';
    return;
  }
  let html = '<div style="margin-top:12px;"><strong>Request:</strong> ' + escHtml(USER_REQUEST) + '</div>';
  html += '<table><thead><tr><th>#</th><th>Method</th><th>Endpoint</th><th>Input</th><th>Output</th></tr></thead><tbody>';
  diagCalls.forEach((c, i) => {
    html += '<tr><td>' + (i+1) + '</td><td>' + c.method + '</td><td>' + escHtml(c.path) + '</td><td><pre style="margin:0;white-space:pre-wrap;font-size:11px;">' + escHtml(JSON.stringify(c.inputParams, null, 2)) + '</pre></td><td><pre style="margin:0;white-space:pre-wrap;font-size:11px;">' + escHtml(JSON.stringify(c.outputParams, null, 2)) + '</pre></td></tr>';
  });
  html += '</tbody></table>';

  if (diagCalls.length) {
    html += '<div style="margin-top:16px;"><strong>Field Mapping</strong><table><thead><tr><th>Response Path</th><th>UI Element</th></tr></thead><tbody>';
    diagCalls.forEach(c => {
      Object.entries(c.fieldMapping).forEach(([k, v]) => {
        html += '<tr><td><code>' + escHtml(k) + '</code></td><td>' + escHtml(v) + '</td></tr>';
      });
    });
    html += '</tbody></table></div>';
  }
  el.innerHTML = html;
}

function escHtml(s) {
  if (s == null) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function statusTag(status) {
  const s = (status || '').toLowerCase();
  let cls = 'tag-default';
  if (s.includes('patent')) cls = 'tag-patented';
  else if (s.includes('pend')) cls = 'tag-pending';
  else if (s.includes('abandon')) cls = 'tag-abandoned';
  else if (s.includes('expir')) cls = 'tag-expired';
  return '<span class="tip-tag ' + cls + '">' + escHtml(status) + '</span>';
}

function show(id) { document.getElementById(id).classList.remove('hidden'); }
function hide(id) { document.getElementById(id).classList.add('hidden'); }

function showError(msg) {
  document.getElementById('errorMsg').textContent = msg;
  show('errorCard');
  hide('placeholder');
}

function clearResults() {
  hide('patentSection');
  hide('costSection');
  hide('errorCard');
  show('placeholder');
  diagCalls = [];
  renderDiagnostics();
}

// Suggest
let suggestTimer = null;
document.getElementById('searchInput').addEventListener('input', function() {
  const q = this.value.trim();
  clearTimeout(suggestTimer);
  const sugEl = document.getElementById('suggestions');
  if (q.length < 5) { sugEl.innerHTML = ''; return; }
  suggestTimer = setTimeout(() => {
    fetch('/tip-api/v1/patent-lookup/suggest?q=' + encodeURIComponent(q))
      .then(r => r.json())
      .then(res => {
        if (!res.status || !res.data || !res.data.results || !res.data.results.length) { sugEl.innerHTML = ''; return; }
        let html = '<div style="display:flex;flex-direction:column;gap:4px;">';
        res.data.results.slice(0, 6).forEach(item => {
          html += '<div class="tip-tag tip-tag-default" style="cursor:pointer;padding:6px 12px;font-size:13px;" onclick="pickSuggestion(\\'' + escHtml(item.display).replace(/'/g, "\\\\'") + '\\')">' + escHtml(item.display) + ' — ' + escHtml(item.title) + '</div>';
        });
        html += '</div>';
        sugEl.innerHTML = html;
      })
      .catch(() => { sugEl.innerHTML = ''; });
  }, 300);
});

function pickSuggestion(val) {
  document.getElementById('searchInput').value = val;
  document.getElementById('suggestions').innerHTML = '';
  doSearch();
}

async function doSearch() {
  const query = document.getElementById('searchInput').value.trim();
  if (!query) { showError('Please enter an application number.'); return; }

  clearResults();
  hide('placeholder');
  document.getElementById('searchBtn').disabled = true;
  document.getElementById('searchBtn').textContent = 'Searching…';

  try {
    // 1. Patent Lookup
    const searchResp = await fetch('/tip-api/v1/patent-lookup/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query })
    });
    const searchData = await searchResp.json();

    if (!searchResp.ok || !searchData.status) {
      const msg = searchData.message || ('HTTP ' + searchResp.status);
      showError('Patent lookup failed: ' + msg);
      addDiag('POST', '/tip-api/v1/patent-lookup/search', { query }, { error: msg }, {});
      renderDiagnostics();
      return;
    }

    const summary = searchData.data.result.summary;
    const fieldMap = {
      'data.result.summary.title': 'Patent Title',
      'data.result.summary.patent_number': 'Patent Number card',
      'data.result.summary.application_number': 'Application Number card',
      'data.result.summary.status': 'Status card',
      'data.result.summary.filing_date': 'Filing Date card',
      'data.result.summary.grant_date': 'Grant Date card',
      'data.result.summary.examiner_name': 'Examiner card',
      'data.result.summary.group_art_unit': 'Group Art Unit card',
      'data.result.summary.application_type': 'Application Type card',
      'data.result.summary.entity_status': 'Entity Status card',
      'data.result.summary.first_inventor_name': 'First Inventor card',
      'data.result.summary.first_applicant_name': 'Applicant card',
    };
    addDiag('POST', '/tip-api/v1/patent-lookup/search', { query }, {
      title: summary.title,
      patent_number: summary.patent_number,
      status: summary.status,
      filing_date: summary.filing_date,
      grant_date: summary.grant_date,
      examiner_name: summary.examiner_name,
      group_art_unit: summary.group_art_unit,
    }, fieldMap);

    // Render patent info
    document.getElementById('patentTitle').textContent = summary.title || '—';
    const statsHtml = [
      statCard('Patent Number', summary.patent_number || '—'),
      statCard('Application Number', summary.application_number || '—'),
      statCard('Status', statusTag(summary.status)),
      statCard('Filing Date', summary.filing_date || '—'),
      statCard('Grant Date', summary.grant_date || '—'),
      statCard('Examiner', summary.examiner_name || '—'),
      statCard('Group Art Unit', summary.group_art_unit || '—'),
      statCard('Application Type', summary.application_type || '—'),
      statCard('Entity Status', summary.entity_status || '—'),
      statCard('First Inventor', summary.first_inventor_name || '—'),
      statCard('Applicant', summary.first_applicant_name || '—'),
    ].join('');
    document.getElementById('patentStats').innerHTML = statsHtml;
    show('patentSection');

    // 2. Cost Estimate
    const appNum = (summary.application_number || '').replace(/[^0-9]/g, '');
    const rawStatus = (summary.status || '').toLowerCase();
    let costStatus = 'Pending';
    if (rawStatus.includes('patent')) costStatus = 'Patented';
    else if (rawStatus.includes('abandon')) costStatus = 'Abandoned';
    else if (rawStatus.includes('expir')) costStatus = 'Expired';

    const costParams = new URLSearchParams({
      app_num: appNum,
      status: costStatus,
      app_type: 'Private case',
      examiner_name: summary.examiner_name || 'N/A',
      gau: summary.group_art_unit || '-',
      app_category: summary.application_type || 'Utility',
      biblo_id: '0',
    });

    const costResp = await fetch('/tip-api/portfolio/fetch_ea_cost_data?' + costParams.toString());
    const costData = await costResp.json();

    if (!costResp.ok || !costData.status) {
      const msg = costData.message || ('HTTP ' + costResp.status);
      // Show cost section with error note
      document.getElementById('costStats').innerHTML = '<div style="color:var(--tip-text-secondary);">Cost estimate unavailable: ' + escHtml(msg) + '</div>';
      document.getElementById('maintTable').querySelector('tbody').innerHTML = '';
      show('costSection');
      addDiag('GET', '/tip-api/portfolio/fetch_ea_cost_data', Object.fromEntries(costParams), { error: msg }, {});
      renderDiagnostics();
      return;
    }

    const cd = costData.data.cost_dict;
    const costFieldMap = {
      'data.cost_dict.predicted_cost': 'Predicted Cost card',
      'data.cost_dict.cost_with_maintenance': 'Cost with Maintenance card',
      'data.cost_dict.next_cost': 'Next Cost card',
      'data.cost_dict.pending_cost': 'Pending Cost card',
      'data.cost_dict.predicted_oa': 'Predicted OAs card',
      'data.cost_dict.maintenance_cost.4th_year': '4th Year Maintenance row',
      'data.cost_dict.maintenance_cost.8th_year': '8th Year Maintenance row',
      'data.cost_dict.maintenance_cost.12th_year': '12th Year Maintenance row',
    };
    addDiag('GET', '/tip-api/portfolio/fetch_ea_cost_data', Object.fromEntries(costParams), {
      predicted_cost: cd.predicted_cost,
      cost_with_maintenance: cd.cost_with_maintenance,
      next_cost: cd.next_cost,
      pending_cost: cd.pending_cost,
      predicted_oa: cd.predicted_oa,
      maintenance_cost: cd.maintenance_cost,
    }, costFieldMap);

    // Render cost cards
    const costHtml = [
      costCard('Predicted Cost', '$' + fmtNum(cd.predicted_cost)),
      costCard('Cost with Maintenance', '$' + fmtNum(cd.cost_with_maintenance)),
      costCard('Next Cost', '$' + fmtNum(cd.next_cost)),
      costCard('Pending Cost', '$' + fmtNum(cd.pending_cost)),
      costCard('Predicted OAs', cd.predicted_oa),
      costCard('Avg Allowance Time', (cd.avg_allowance_time || '—') + (cd.avg_allowance_time ? ' yrs' : '')),
    ].join('');
    document.getElementById('costStats').innerHTML = costHtml;

    // Render maintenance table
    const mc = cd.maintenance_cost || {};
    const maintRows = [
      { period: '4th Year', fee: mc['4th_year'] },
      { period: '8th Year', fee: mc['8th_year'] },
      { period: '12th Year', fee: mc['12th_year'] },
    ];
    let maintHtml = '';
    maintRows.forEach(r => {
      maintHtml += '<tr><td>' + escHtml(r.period) + '</td><td>' + (r.fee != null ? '$' + fmtNum(r.fee) : '—') + '</td></tr>';
    });
    document.getElementById('maintTable').querySelector('tbody').innerHTML = maintHtml;
    show('costSection');

  } catch (err) {
    showError('Unexpected error: ' + err.message);
    addDiag('—', '—', {}, { error: err.message }, {});
  } finally {
    document.getElementById('searchBtn').disabled = false;
    document.getElementById('searchBtn').textContent = 'Search';
    renderDiagnostics();
  }
}

function statCard(label, value) {
  return '<div class="tip-card" style="padding:16px;"><div class="tip-card-value">' + value + '</div><div class="tip-card-label">' + escHtml(label) + '</div></div>';
}

function costCard(label, value) {
  return '<div class="tip-card" style="padding:16px;"><div class="tip-card-value">' + escHtml(String(value)) + '</div><div class="tip-card-label">' + escHtml(label) + '</div></div>';
}

function fmtNum(n) {
  if (n == null) return '—';
  return Number(n).toLocaleString('en-US');
}

// Allow Enter key to trigger search
document.getElementById('searchInput').addEventListener('keydown', function(e) {
  if (e.key === 'Enter') doSearch();
});
</script>
</body>
</html>
"""
