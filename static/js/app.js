/**
 * Customer Intelligence — Client-Side Application Controller
 * Handles client routing, API communications, and Plotly.js chart rendering.
 */

// Global State Cache
const APP = {
  activePage: 'overview',
  activeAnalyticsSub: 'overview',
  customersPage: 1,
  customersLimit: 25,
  segmentsData: null,
  analyticsData: null,
  dataLoaded: {}
};

// -------------------------------------------------------------
// Initialization & Client-Side Routing
// -------------------------------------------------------------
document.addEventListener('DOMContentLoaded', () => {
  // Setup Hash Routing
  const hash = window.location.hash.replace('#', '') || 'overview';
  navigateTo(hash);

  // Setup Nav Link Listeners
  document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const target = link.getAttribute('data-page');
      navigateTo(target);
    });
  });

  // Initial Load of Overview Data
  loadOverview();
});

function navigateTo(pageId) {
  const validPages = ['overview', 'customers', 'segments', 'analytics', 'data'];
  if (!validPages.includes(pageId)) pageId = 'overview';

  APP.activePage = pageId;
  window.location.hash = pageId;

  // Update Nav Links
  document.querySelectorAll('.nav-link').forEach(link => {
    if (link.getAttribute('data-page') === pageId) {
      link.classList.add('active');
    } else {
      link.classList.remove('active');
    }
  });

  // Update Page Views
  document.querySelectorAll('.page-view').forEach(view => {
    if (view.id === `page-${pageId}`) {
      view.classList.add('active');
    } else {
      view.classList.remove('active');
    }
  });

  window.scrollTo({ top: 0, behavior: 'smooth' });

  // Trigger page-specific data loading
  if (pageId === 'overview' && !APP.dataLoaded['overview']) loadOverview();
  if (pageId === 'customers' && !APP.dataLoaded['customers']) loadCustomersInitial();
  if (pageId === 'segments' && !APP.dataLoaded['segments']) loadSegments();
  if (pageId === 'analytics' && !APP.dataLoaded['analytics']) loadAnalytics();
  if (pageId === 'data' && !APP.dataLoaded['data']) loadDataManagement();
}

// -------------------------------------------------------------
// 1. OVERVIEW PAGE CONTROLLER
// -------------------------------------------------------------
async function loadOverview() {
  try {
    const res = await fetch('/api/overview');
    const data = await res.json();

    // Update KPIs
    document.getElementById('kpi-customers').textContent = data.kpis.customers.toLocaleString();
    document.getElementById('kpi-transactions').textContent = data.kpis.transactions.toLocaleString();
    document.getElementById('kpi-revenue').textContent = data.kpis.revenue_formatted;
    document.getElementById('kpi-segments').textContent = data.kpis.segments;
    document.getElementById('kpi-silhouette').textContent = `Silhouette ${data.kpis.silhouette}`;

    // Update Insight Callout
    document.getElementById('overview-insight-text').textContent = data.insight.text;

    // Render Segment Preview Cards
    const listEl = document.getElementById('overview-segment-preview-list');
    listEl.innerHTML = '';
    data.top_segments.forEach(seg => {
      const card = document.createElement('div');
      card.className = 'preview-row-card';
      card.style.borderLeft = `4px solid ${seg.color}`;
      card.innerHTML = `
        <div>
          <span class="prev-badge" style="color: ${seg.color}">CLUSTER C${seg.cluster} • ${seg.badge}</span>
          <div class="prev-title">${seg.name}</div>
          <div class="prev-desc">${seg.description}</div>
        </div>
        <div class="prev-stats">
          <div class="prev-count">${seg.customers.toLocaleString()} customers (${seg.share_pct}%)</div>
          <div class="prev-rev">${seg.revenue_pct}% of total revenue</div>
        </div>
      `;
      listEl.appendChild(card);
    });

    APP.dataLoaded['overview'] = true;
  } catch (err) {
    console.error('Error loading overview:', err);
  }
}

// -------------------------------------------------------------
// 2. CUSTOMERS PAGE CONTROLLER
// -------------------------------------------------------------
async function loadCustomersInitial() {
  await lookupCustomer(17850);
  await fetchCustomers(1);
  APP.dataLoaded['customers'] = true;
}

async function lookupCustomer(customId) {
  const inputEl = document.getElementById('cust-search-input');
  const searchId = customId || parseInt(inputEl.value.trim(), 10);
  if (!searchId || isNaN(searchId)) return;

  try {
    const res = await fetch(`/api/customer/${searchId}`);
    const info = await res.json();

    const profileCard = document.getElementById('customer-profile-card');
    if (info.found) {
      profileCard.style.display = 'block';
      profileCard.style.borderLeft = `4px solid ${info.color}`;
      document.getElementById('crm-id-title').textContent = `Customer #${info.customer_id}`;
      
      const badgeEl = document.getElementById('crm-segment-badge');
      badgeEl.textContent = `Cluster C${info.cluster} • ${info.persona_name}`;
      badgeEl.style.color = info.color;
      badgeEl.style.borderColor = `${info.color}40`;
      badgeEl.style.backgroundColor = `${info.color}15`;

      document.getElementById('crm-recency-val').textContent = `${info.recency} days`;
      document.getElementById('crm-frequency-val').textContent = `${info.frequency} orders`;
      document.getElementById('crm-monetary-val').textContent = `£${info.monetary.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

      document.getElementById('crm-behavior-text').textContent = info.description;
      document.getElementById('crm-action-text').textContent = info.recommended_strategy;
    } else {
      alert(`Customer #${searchId} was not found in transaction records.`);
    }
  } catch (err) {
    console.error('Error looking up customer:', err);
  }
}

function selectSampleCustomer(id) {
  document.getElementById('cust-search-input').value = id;
  lookupCustomer(id);
}

function updateRecencySlider(val) {
  document.getElementById('recency-val-label').textContent = val;
}

async function fetchCustomers(page = 1) {
  APP.customersPage = page;
  const search = document.getElementById('cust-search-input').value.trim();
  const segment = document.getElementById('filter-segment').value;
  const recencyMax = document.getElementById('filter-recency-slider').value;
  const monetaryMin = document.getElementById('filter-monetary').value;

  const params = new URLSearchParams({
    page: APP.customersPage,
    limit: APP.customersLimit,
    recency_max: recencyMax,
    monetary_min: monetaryMin
  });
  if (segment && segment !== 'All') params.append('segment', segment);

  try {
    const res = await fetch(`/api/customers?${params.toString()}`);
    const data = await res.json();

    // Populate Segment Dropdown once
    const segSelect = document.getElementById('filter-segment');
    if (segSelect.options.length <= 1 && data.segments) {
      data.segments.forEach(s => {
        const opt = document.createElement('option');
        opt.value = s;
        opt.textContent = s;
        segSelect.appendChild(opt);
      });
      document.getElementById('filter-recency-slider').max = data.max_recency;
      document.getElementById('filter-recency-slider').value = data.max_recency;
      document.getElementById('recency-val-label').textContent = data.max_recency;
    }

    // Render Table Rows
    const tbody = document.getElementById('customers-table-body');
    tbody.innerHTML = '';
    data.customers.forEach(c => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>#${c.customer_id}</strong></td>
        <td><span style="color: ${c.color}; font-weight: 600;">${c.segment}</span></td>
        <td>${c.cluster}</td>
        <td>${c.recency}d</td>
        <td>${c.frequency}</td>
        <td>£${c.monetary.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
        <td><button class="btn btn-secondary btn-sm" onclick="selectSampleCustomer(${c.customer_id})">View Profile</button></td>
      `;
      tbody.appendChild(tr);
    });

    // Update Counts & Pagination
    document.getElementById('directory-record-count').textContent = `Showing ${data.customers.length} of ${data.total.toLocaleString()} customers`;
    document.getElementById('pagination-info').textContent = `Page ${data.page} of ${data.max_pages}`;
    document.getElementById('btn-prev-page').disabled = (data.page <= 1);
    document.getElementById('btn-next-page').disabled = (data.page >= data.max_pages);

  } catch (err) {
    console.error('Error fetching customers:', err);
  }
}

function changeCustomerPage(delta) {
  fetchCustomers(APP.customersPage + delta);
}

function exportCustomerCSV() {
  window.location.href = '/api/export-csv';
}

// -------------------------------------------------------------
// 3. SEGMENTS PAGE CONTROLLER
// -------------------------------------------------------------
async function loadSegments() {
  try {
    const res = await fetch('/api/segments');
    const data = await res.json();
    APP.segmentsData = data;

    // Render Grid of Segment Product Cards
    const gridEl = document.getElementById('segments-grid');
    gridEl.innerHTML = '';

    const selectEl = document.getElementById('benchmark-cluster-select');
    selectEl.innerHTML = '';

    data.segments.forEach(seg => {
      // Add option to dropdown
      const opt = document.createElement('option');
      opt.value = seg.id;
      opt.textContent = `Cluster C${seg.id}: ${seg.name}`;
      selectEl.appendChild(opt);

      // Card
      const card = document.createElement('div');
      card.className = 'segment-product-card';
      card.style.borderTop = `4px solid ${seg.color}`;
      card.innerHTML = `
        <div>
          <div class="card-top-row">
            <div>
              <span class="prev-badge" style="color: ${seg.color}">CLUSTER C${seg.id}</span>
              <div class="card-cluster-name">${seg.name}</div>
            </div>
            <span class="crm-badge" style="color: ${seg.color}; background: ${seg.color}15; border-color: ${seg.color}30;">${seg.badge}</span>
          </div>

          <p class="card-desc">${seg.description}</p>
          <div class="card-volume-meta">
            <strong>${seg.customers.toLocaleString()}</strong> customers • <strong>${seg.share_pct}%</strong> customer base • <strong>${seg.revenue_pct}%</strong> revenue
          </div>

          <div class="card-rfm-grid">
            <div>
              <span class="card-rfm-label">Recency</span>
              <div class="card-rfm-val">${seg.recency_mean}d</div>
            </div>
            <div>
              <span class="card-rfm-label">Frequency</span>
              <div class="card-rfm-val">${seg.frequency_mean}</div>
            </div>
            <div>
              <span class="card-rfm-label">Monetary</span>
              <div class="card-rfm-val">£${seg.monetary_mean.toLocaleString('en-US', { maximumFractionDigits: 0 })}</div>
            </div>
          </div>

          <div class="card-action-title">RECOMMENDED ACTION</div>
          <div class="card-action-text">${seg.strategy}</div>
        </div>

        <div class="card-justification-box">
          <div style="font-weight: 700; text-transform: uppercase; margin-bottom: 0.15rem;">RFM Statistical Justification</div>
          <div>${seg.justification}</div>
        </div>
      `;
      gridEl.appendChild(card);
    });

    renderBenchmarkChart();
    APP.dataLoaded['segments'] = true;
  } catch (err) {
    console.error('Error loading segments:', err);
  }
}

function renderBenchmarkChart() {
  if (!APP.segmentsData) return;
  const clusterId = parseInt(document.getElementById('benchmark-cluster-select').value, 10);
  const seg = APP.segmentsData.segments.find(s => s.id === clusterId) || APP.segmentsData.segments[0];
  const b = APP.segmentsData.baseline;

  // Update summary box
  const sumBox = document.getElementById('benchmark-summary-card');
  sumBox.style.borderLeft = `4px solid ${seg.color}`;
  sumBox.innerHTML = `
    <span class="prev-badge" style="color: ${seg.color}">OVERVIEW • CLUSTER C${seg.id}</span>
    <h3 style="font-size: 1.15rem; font-weight: 800; margin: 0.25rem 0;">${seg.name}</h3>
    <p style="font-size: 0.8rem; color: #64748B; margin-bottom: 0.75rem;">${seg.description}</p>
    <div style="font-size: 0.8rem; line-height: 1.5;">
      <div>• <strong>Customer Volume:</strong> ${seg.customers.toLocaleString()} (${seg.share_pct}%)</div>
      <div>• <strong>Revenue Contribution:</strong> £${seg.total_revenue.toLocaleString('en-US', { minimumFractionDigits: 2 })} (${seg.revenue_pct}%)</div>
      <div style="margin-top: 0.35rem;">• <strong>Marketing Strategy:</strong> ${seg.strategy}</div>
    </div>
  `;

  // Plotly side-by-side comparison
  const rRatio = Math.round((b.recency_avg / Math.max(seg.recency_mean, 1)) * 100) / 100;
  const fRatio = Math.round((seg.frequency_mean / Math.max(b.frequency_avg, 1)) * 100) / 100;
  const mRatio = Math.round((seg.monetary_mean / Math.max(b.monetary_avg, 1)) * 100) / 100;

  const categories = ['Recency Ratio (Lower days is better)', 'Frequency Ratio', 'Monetary Ratio'];
  const clusterVals = [rRatio, fRatio, mRatio];
  const baselineVals = [1.0, 1.0, 1.0];

  const traceCluster = {
    x: categories,
    y: clusterVals,
    name: `Cluster C${seg.id} (${seg.name})`,
    type: 'bar',
    marker: { color: seg.color },
    text: clusterVals.map(v => `${v}x`),
    textposition: 'outside'
  };

  const traceBase = {
    x: categories,
    y: baselineVals,
    name: 'Store Average Baseline (1.0x)',
    type: 'bar',
    marker: { color: '#CBD5E1' }
  };

  const layout = {
    barmode: 'group',
    margin: { t: 30, b: 40, l: 40, r: 20 },
    height: 300,
    font: { family: 'Inter, sans-serif', color: '#0F172A', size: 12 },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    yaxis: { gridcolor: '#F1F5F9', zeroline: false },
    legend: { orientation: 'h', y: 1.15, x: 0 }
  };

  Plotly.newPlot('chart-benchmark', [traceCluster, traceBase], layout, { responsive: true, displayModeBar: false });
}

// -------------------------------------------------------------
// 4. ANALYTICS PAGE CONTROLLER
// -------------------------------------------------------------
function switchAnalyticsSub(subId) {
  APP.activeAnalyticsSub = subId;

  document.querySelectorAll('.subnav-link').forEach(btn => {
    if (btn.getAttribute('data-sub') === subId) {
      btn.classList.add('active');
    } else {
      btn.classList.remove('active');
    }
  });

  document.querySelectorAll('.analytics-sub-view').forEach(view => {
    if (view.id === `analytics-sub-${subId}`) {
      view.classList.add('active');
    } else {
      view.classList.remove('active');
    }
  });

  // Re-trigger layout resize for Plotly charts if hidden
  window.dispatchEvent(new Event('resize'));
}

async function loadAnalytics() {
  try {
    const res = await fetch('/api/analytics');
    const data = await res.json();
    APP.analyticsData = data;

    // Overview silhouette
    document.getElementById('an-sil-score').textContent = data.evaluation.k_eval.find(k => k.selected)?.silhouette || '0.312';

    // 1. RFM Charts
    const commonLayout = {
      font: { family: 'Inter, sans-serif', color: '#0F172A', size: 11 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
      margin: { t: 30, b: 35, l: 35, r: 15 },
      height: 260
    };

    Plotly.newPlot('chart-rfm-recency', [{
      x: data.rfm.distributions.recency,
      type: 'histogram',
      nbinsx: 30,
      marker: { color: '#2563EB', opacity: 0.85 }
    }], { ...commonLayout, title: { text: 'Recency Distribution (Days)', font: { size: 12, weight: 700 } } }, { responsive: true, displayModeBar: false });

    Plotly.newPlot('chart-rfm-frequency', [{
      x: data.rfm.distributions.frequency,
      type: 'histogram',
      nbinsx: 30,
      marker: { color: '#10B981', opacity: 0.85 }
    }], { ...commonLayout, title: { text: 'Frequency Distribution (Orders)', font: { size: 12, weight: 700 } } }, { responsive: true, displayModeBar: false });

    Plotly.newPlot('chart-rfm-monetary', [{
      x: data.rfm.distributions.monetary,
      type: 'histogram',
      nbinsx: 30,
      marker: { color: '#F59E0B', opacity: 0.85 }
    }], { ...commonLayout, title: { text: 'Monetary Spend (£)', font: { size: 12, weight: 700 } } }, { responsive: true, displayModeBar: false });

    // RFM Stats Table
    const rfmTableBody = document.querySelector('#rfm-stats-table tbody');
    rfmTableBody.innerHTML = '';
    data.rfm.summary_stats.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${r.Metric}</strong></td>
        <td>${r.Mean.toLocaleString()}</td>
        <td>${r.Std.toLocaleString()}</td>
        <td>${r.Median.toLocaleString()}</td>
        <td>${r.Min.toLocaleString()}</td>
        <td>${r.Max.toLocaleString()}</td>
        <td>${r.Skewness}</td>
      `;
      rfmTableBody.appendChild(tr);
    });

    // Correlation Heatmap
    Plotly.newPlot('chart-rfm-corr', [{
      z: data.rfm.correlation.z,
      x: data.rfm.correlation.columns,
      y: data.rfm.correlation.columns,
      type: 'heatmap',
      colorscale: 'Blues',
      showscale: false
    }], { ...commonLayout, margin: { t: 15, b: 30, l: 80, r: 15 }, height: 260 }, { responsive: true, displayModeBar: false });

    // 2. Elbow & Silhouette Charts
    const kList = data.evaluation.k_eval.map(e => e.k);
    const inertias = data.evaluation.k_eval.map(e => e.inertia);
    const sils = data.evaluation.k_eval.map(e => e.silhouette);

    Plotly.newPlot('chart-elbow', [{
      x: kList,
      y: inertias,
      mode: 'lines+markers',
      line: { color: '#2563EB', width: 2.5 },
      marker: { size: 8 }
    }], {
      ...commonLayout,
      title: { text: 'Elbow Method (Inertia vs K)', font: { size: 12, weight: 700 } },
      xaxis: { title: 'Number of Clusters (K)', dtick: 1 },
      height: 290
    }, { responsive: true, displayModeBar: false });

    Plotly.newPlot('chart-silhouette', [{
      x: kList,
      y: sils,
      mode: 'lines+markers',
      line: { color: '#10B981', width: 2.5 },
      marker: { size: 8 }
    }], {
      ...commonLayout,
      title: { text: 'Silhouette Score vs K', font: { size: 12, weight: 700 } },
      xaxis: { title: 'Number of Clusters (K)', dtick: 1 },
      height: 290
    }, { responsive: true, displayModeBar: false });

    // Evaluation Table
    const evalTbody = document.querySelector('#cluster-eval-table tbody');
    evalTbody.innerHTML = '';
    data.evaluation.k_eval.forEach(row => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>K = ${row.k}</strong></td>
        <td>${row.inertia.toLocaleString()}</td>
        <td>${row.silhouette.toFixed(4)}</td>
        <td>${row.selected ? '<span style="color:#2563EB; font-weight:700;">● Selected Model (K=6)</span>' : 'Evaluated'}</td>
      `;
      evalTbody.appendChild(tr);
    });

    // K-Means Volume Chart
    Plotly.newPlot('chart-kmeans-volume', [{
      x: data.kmeans.map(k => `C${k.cluster}: ${k.name}`),
      y: data.kmeans.map(k => k.customers),
      type: 'bar',
      marker: { color: data.kmeans.map(k => k.color) },
      text: data.kmeans.map(k => `${k.customers.toLocaleString()} (${k.share_pct}%)`),
      textposition: 'outside'
    }], {
      ...commonLayout,
      height: 300,
      margin: { t: 20, b: 60, l: 40, r: 20 }
    }, { responsive: true, displayModeBar: false });

    // 3. Hierarchical Comparison
    const hAlgs = data.comparison.metrics.map(m => m.Algorithm);
    const hSils = data.comparison.metrics.map(m => m['Silhouette Score']);
    const hDbi = data.comparison.metrics.map(m => m['Davies-Bouldin Index']);

    Plotly.newPlot('chart-hierarchical-comp', [
      { x: hAlgs, y: hSils, name: 'Silhouette Score (Higher is better)', type: 'bar', marker: { color: '#10B981' } },
      { x: hAlgs, y: hDbi, name: 'Davies-Bouldin Index (Lower is better)', type: 'bar', marker: { color: '#6366F1' } }
    ], {
      ...commonLayout,
      barmode: 'group',
      height: 280,
      legend: { orientation: 'h', y: 1.15 }
    }, { responsive: true, displayModeBar: false });

    // Hierarchical Metrics Table
    const hTbody = document.querySelector('#hierarchical-metrics-table tbody');
    hTbody.innerHTML = '';
    data.comparison.metrics.forEach(m => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${m.Algorithm}</strong></td>
        <td>${m['Silhouette Score'].toFixed(4)}</td>
        <td>${m['Davies-Bouldin Index'].toFixed(4)}</td>
        <td>${m['Calinski-Harabasz'].toLocaleString()}</td>
      `;
      hTbody.appendChild(tr);
    });

    // Cross-tab table
    const ctHeader = document.querySelector('#cross-tab-table thead tr');
    ctHeader.innerHTML = '<th>K-Means \\ Hierarchical</th>';
    data.comparison.cross_tab.columns.forEach(col => {
      ctHeader.innerHTML += `<th>${col}</th>`;
    });
    const ctBody = document.querySelector('#cross-tab-table tbody');
    ctBody.innerHTML = '';
    data.comparison.cross_tab.rows.forEach((rowName, rIdx) => {
      let rowHtml = `<td><strong>${rowName}</strong></td>`;
      data.comparison.cross_tab.values[rIdx].forEach(val => {
        rowHtml += `<td>${val}</td>`;
      });
      const tr = document.createElement('tr');
      tr.innerHTML = rowHtml;
      ctBody.appendChild(tr);
    });

    // 4. Large 2D PCA Scatter Plot
    const pcaClusters = [...new Set(data.pca.points.map(p => p.cluster))].sort();
    const pcaTraces = pcaClusters.map(cId => {
      const cPts = data.pca.points.filter(p => p.cluster === cId);
      return {
        x: cPts.map(p => p.x),
        y: cPts.map(p => p.y),
        mode: 'markers',
        name: `C${cId}: ${cPts[0].segment}`,
        marker: { size: 7, color: cPts[0].color, opacity: 0.75 },
        customdata: cPts.map(p => [p.id, p.r, p.f, p.m]),
        hovertemplate: '<b>Customer #%{customdata[0]}</b><br>Recency: %{customdata[1]}d<br>Orders: %{customdata[2]}<br>Spend: £%{customdata[3]:,.2f}<extra></extra>'
      };
    });

    Plotly.newPlot('chart-pca-scatter', pcaTraces, {
      ...commonLayout,
      height: 480,
      margin: { t: 20, b: 40, l: 40, r: 20 },
      xaxis: { title: 'Principal Component 1 (Spending & Volume)', gridcolor: '#F1F5F9' },
      yaxis: { title: 'Principal Component 2 (Recency Timing)', gridcolor: '#F1F5F9' },
      legend: { orientation: 'h', y: 1.15 }
    }, { responsive: true, displayModeBar: false });

    document.getElementById('pca-var-pc1').textContent = `${data.pca.explained_variance.pc1}%`;
    document.getElementById('pca-var-pc2').textContent = `${data.pca.explained_variance.pc2}%`;
    document.getElementById('pca-var-total').textContent = `${data.pca.explained_variance.total}%`;

    APP.dataLoaded['analytics'] = true;
  } catch (err) {
    console.error('Error loading analytics:', err);
  }
}

// -------------------------------------------------------------
// 5. DATA MANAGEMENT CONTROLLER
// -------------------------------------------------------------
async function loadDataManagement() {
  try {
    const res = await fetch('/api/data');
    const data = await res.json();

    document.getElementById('data-raw-rows').textContent = data.status.initial_rows.toLocaleString();
    document.getElementById('data-clean-rows').textContent = data.status.final_rows.toLocaleString();
    document.getElementById('data-retention-rate').textContent = `${data.status.retention_rate_pct}% retention rate`;
    document.getElementById('data-unique-customers').textContent = data.status.unique_customers.toLocaleString();
    document.getElementById('data-unique-invoices').textContent = data.status.unique_invoices.toLocaleString();

    // Audit Trail Table
    const auditTbody = document.querySelector('#audit-trail-table tbody');
    auditTbody.innerHTML = '';
    data.audit_table.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `<td><strong>${r.stage}</strong></td><td>${r.count}</td><td>${r.desc}</td>`;
      auditTbody.appendChild(tr);
    });

    // Preview Table
    const prevTbody = document.querySelector('#data-preview-table tbody');
    prevTbody.innerHTML = '';
    data.preview.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td>${r.InvoiceNo}</td>
        <td>${r.StockCode}</td>
        <td>${r.Description || ''}</td>
        <td>${r.Quantity}</td>
        <td>${r.InvoiceDate}</td>
        <td>£${r.UnitPrice.toFixed(2)}</td>
        <td>£${r.TotalPrice.toFixed(2)}</td>
        <td>#${r.CustomerID}</td>
        <td>${r.Country}</td>
      `;
      prevTbody.appendChild(tr);
    });

    // Numerical Stats Table
    const numTbody = document.querySelector('#numeric-stats-table tbody');
    numTbody.innerHTML = '';
    data.numeric_stats.forEach(r => {
      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><strong>${r.column}</strong></td>
        <td>${r.count.toLocaleString()}</td>
        <td>${r.mean.toFixed(2)}</td>
        <td>${r.std.toFixed(2)}</td>
        <td>${r.min.toFixed(2)}</td>
        <td>${r['25%'].toFixed(2)}</td>
        <td>${r['50%'].toFixed(2)}</td>
        <td>${r['75%'].toFixed(2)}</td>
        <td>${r.max.toFixed(2)}</td>
      `;
      numTbody.appendChild(tr);
    });

    APP.dataLoaded['data'] = true;
  } catch (err) {
    console.error('Error loading data management:', err);
  }
}

async function handleFileSelect(input) {
  const file = input.files[0];
  if (!file) return;

  const statusMsg = document.getElementById('upload-status-msg');
  statusMsg.className = 'upload-status';
  statusMsg.textContent = `Uploading ${file.name} and re-training pipeline...`;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch('/api/upload', {
      method: 'POST',
      body: formData
    });
    const result = await res.json();

    if (result.success) {
      statusMsg.className = 'upload-status success';
      statusMsg.textContent = result.message;
      // Invalidate cache and reload
      APP.dataLoaded = {};
      loadOverview();
      loadDataManagement();
    } else {
      statusMsg.className = 'upload-status error';
      statusMsg.textContent = result.error || 'Upload failed.';
    }
  } catch (err) {
    statusMsg.className = 'upload-status error';
    statusMsg.textContent = 'Upload network error: ' + err.message;
  }
}
