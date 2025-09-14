/* QuantMini Dashboard wiring (Pattern A: query-param driven) */

(function () {
  const $ = (sel) => document.querySelector(sel);
  const $$ = (sel) => Array.from(document.querySelectorAll(sel));

  const els = {
    ticker: $('#ticker'),
    start: $('#start'),
    end: $('#end'),
    btnRaw: $('#btn-raw-prices'),
    btnFactors: $('#btn-factors-api'),
    btnChart: $('#btn-show-chart'),
    btnTable: $('#btn-show-table'),
    status: $('#status'),
    chartPanel: $('#chart-panel'),
    tablePanel: $('#table-panel'),
    table: $('#factors-table'),
    chartCanvas: $('#priceChart'),
  };

  let chart; // Chart.js instance

  // ---------- Utilities ----------
  function setStatus(msg, isError = false) {
    els.status.textContent = msg || '';
    els.status.style.color = isError ? '#fca5a5' : '#9aa4b2';
  }

  function getInputs() {
    const ticker = (els.ticker.value || '').trim().toUpperCase();
    const start = (els.start.value || '').trim();
    const end = (els.end.value || '').trim();
    return { ticker, start, end };
  }

  function assertInputs({ ticker, start, end }, { requireDates = false } = {}) {
    if (!ticker) throw new Error('Enter a ticker.');
    if (requireDates) {
      if (!start) throw new Error('Select a start date.');
      if (!end) throw new Error('Select an end date.');
      if (start > end) throw new Error('Start must be on or before End.');
    }
  }

  function updateURL(params) {
    const url = new URL(window.location.href);
    Object.entries(params).forEach(([k, v]) => {
      if (v === null || v === undefined || v === '') url.searchParams.delete(k);
      else url.searchParams.set(k, v);
    });
    history.replaceState(null, '', url);
  }

  function prefillFromURL() {
    const sp = new URLSearchParams(window.location.search);
    const ticker = sp.get('ticker') || '';
    const start = sp.get('start') || '';
    const end = sp.get('end') || '';
    const panel = sp.get('panel') || '';

    if (ticker) els.ticker.value = ticker.toUpperCase();
    if (start) els.start.value = start;
    if (end) els.end.value = end;

    // If panel query present, try to load it
    if (panel === 'chart') {
      showChart().catch(() => {});
    } else if (panel === 'table') {
      showTable().catch(() => {});
    }
  }

  function apiUrlRaw(ticker) {
    // Raw endpoint without explicit dates
    return `/api/prices/${encodeURIComponent(ticker)}`;
  }

  function apiUrlFactors({ ticker, start, end }) {
    // Uses date range; backend already expects YYYY-MM-DD
    const u = new URL(window.location.origin + `/api/factors/${encodeURIComponent(ticker)}`);
    if (start) u.searchParams.set('start', start);
    if (end) u.searchParams.set('end', end);
    // Ask backend for time-series records format if supported
    u.searchParams.set('as', 'series');
    return u.pathname + u.search;
  }

  function isoToLocalShort(iso) {
    // Render like 2024-08-12 09:30
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return String(iso);
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const da = String(d.getDate()).padStart(2, '0');
    const hh = String(d.getHours()).padStart(2, '0');
    const mm = String(d.getMinutes()).padStart(2, '0');
    return `${y}-${m}-${da} ${hh}:${mm}`;
  }

  // ---------- Table ----------
  function renderTable(records) {
    const thead = els.table.querySelector('thead');
    const tbody = els.table.querySelector('tbody');
    thead.innerHTML = '';
    tbody.innerHTML = '';

    if (!Array.isArray(records) || records.length === 0) {
      thead.innerHTML = '<tr><th>No data</th></tr>';
      return;
    }

    // Prefer a stable, readable column order; include available ones only
    const preferred = [
      't', 'open', 'high', 'low', 'close', 'volume',
      'return_pct_1d', 'log_return_1d', 'cum_return', 'drawdown'
    ];
    const available = preferred.filter(k => k in records[0]);
    const extra = Object.keys(records[0]).filter(k => !available.includes(k));
    const cols = [...available, ...extra];

    // Header
    const trH = document.createElement('tr');
    for (const c of cols) {
      const th = document.createElement('th');
      th.textContent = c;
      trH.appendChild(th);
    }
    thead.appendChild(trH);

    // Rows
    const frag = document.createDocumentFragment();
    for (const r of records) {
      const tr = document.createElement('tr');
      for (const c of cols) {
        const td = document.createElement('td');
        let v = r[c];
        if (c === 't') v = isoToLocalShort(v);
        if (typeof v === 'number') {
          // compact numeric formatting
          if (Math.abs(v) >= 1000 && Number.isFinite(v)) {
            v = Intl.NumberFormat(undefined, { notation: 'compact', maximumFractionDigits: 2 }).format(v);
          } else {
            v = Number(v).toFixed(Math.abs(v) < 1 ? 6 : 4);
          }
        }
        td.textContent = v === null || v === undefined ? '' : v;
        tr.appendChild(td);
      }
      frag.appendChild(tr);
    }
    tbody.appendChild(frag);
  }

  // ---------- Chart ----------
  function renderChart(records) {
    if (!Array.isArray(records) || records.length === 0) {
      throw new Error('No data to plot.');
    }

    const labels = records.map(r => isoToLocalShort(r.t ?? r.timestamp ?? r.time ?? r.date ?? ''));
    const close = records.map(r => Number(r.close ?? r.c));
    // Optional: cumulative return if present
    const cum = records.map(r => (r.cum_return !== undefined ? Number(r.cum_return) : null));
    const hasCum = cum.some(v => v !== null && Number.isFinite(v));

    // Destroy existing chart
    if (chart) {
      chart.destroy();
      chart = null;
    }

    const datasets = [
      {
        label: 'Close',
        data: close,
        borderWidth: 2,
        tension: 0.15,
        pointRadius: 0
      }
    ];

    if (hasCum) {
      datasets.push({
        label: 'Cum Return',
        data: cum,
        yAxisID: 'y1',
        borderWidth: 2,
        tension: 0.15,
        pointRadius: 0
      });
    }

    chart = new Chart(els.chartCanvas.getContext('2d'), {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        animation: false,
        interaction: { mode: 'index', intersect: false },
        scales: {
          y: { title: { display: true, text: 'Price' } },
          ...(hasCum ? { y1: { position: 'right', title: { display: true, text: 'Cum Return' } } } : {})
        },
        plugins: {
          legend: { display: true },
          tooltip: {
            callbacks: {
              // Pretty timestamp in tooltip
              title(items) { return items[0]?.label || ''; }
            }
          }
        }
      }
    });
  }

  // ---------- Fetchers ----------
  async function fetchFactors(params) {
    const url = apiUrlFactors(params);
    const res = await fetch(url, { headers: { 'Accept': 'application/json' } });
    if (!res.ok) {
      const txt = await res.text();
      throw new Error(`HTTP ${res.status} — ${txt.slice(0, 200)}`);
    }
    const data = await res.json();
    // Accept either {data:[...]} or [...]
    const records = Array.isArray(data) ? data : (data.data || data.series || data.records || []);
    if (!Array.isArray(records)) {
      throw new Error('Unexpected response shape from /api/factors.');
    }
    return records;
  }

  // ---------- Panel actions ----------
  async function showChart() {
    const params = getInputs();
    assertInputs(params, { requireDates: true });
    setStatus('Loading chart…');
    updateURL({ ticker: params.ticker, start: params.start, end: params.end, panel: 'chart' });
    const records = await fetchFactors(params);
    renderChart(records);
    els.chartPanel.classList.remove('hidden');
    setStatus('Chart loaded.');
  }

  async function showTable() {
    const params = getInputs();
    assertInputs(params, { requireDates: true });
    setStatus('Loading table…');
    updateURL({ ticker: params.ticker, start: params.start, end: params.end, panel: 'table' });
    const records = await fetchFactors(params);
    renderTable(records);
    els.tablePanel.classList.remove('hidden');
    setStatus(`Loaded ${records.length} rows.`);
  }

  // ---------- Event wiring ----------
  function bindEvents() {
    // Open raw prices JSON in a new tab
    els.btnRaw.addEventListener('click', () => {
      try {
        const { ticker } = getInputs();
        assertInputs({ ticker }, { requireDates: false });
        const url = apiUrlRaw(ticker);
        updateURL({ ticker, panel: '' });
        window.open(url, '_blank', 'noopener');
      } catch (err) {
        setStatus(err.message, true);
      }
    });

    // Open factors JSON in a new tab (requires dates)
    els.btnFactors.addEventListener('click', () => {
      try {
        const params = getInputs();
        assertInputs(params, { requireDates: true });
        const url = apiUrlFactors(params);
        updateURL({ ticker: params.ticker, start: params.start, end: params.end, panel: '' });
        window.open(url, '_blank', 'noopener');
      } catch (err) {
        setStatus(err.message, true);
      }
    });

    // Show chart / table panels
    els.btnChart.addEventListener('click', () => {
      showChart().catch(err => setStatus(err.message, true));
    });
    els.btnTable.addEventListener('click', () => {
      showTable().catch(err => setStatus(err.message, true));
    });

    // Hide panel buttons
    $$('#chart-panel [data-collapse], #table-panel [data-collapse]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const target = e.currentTarget.getAttribute('data-collapse');
        const node = document.querySelector(target);
        if (node) node.classList.add('hidden');
      });
    });

    // Enter key runs "Show Chart"
    [els.ticker, els.start, els.end].forEach(inp => {
      inp.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
          showChart().catch(err => setStatus(err.message, true));
        }
      });
    });
  }

  // ---------- Init ----------
  function init() {
    bindEvents();
    prefillFromURL();
    setStatus('Ready.');
  }

  document.addEventListener('DOMContentLoaded', init);
})();
