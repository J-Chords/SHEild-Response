(() => {
  const dataEl = document.getElementById('admin-dashboard-data');
  if (!dataEl || typeof Chart === 'undefined') return;

  const data = JSON.parse(dataEl.textContent);

  const palette = {
    plum: '#74234a',
    plumDark: '#3e1029',
    rose: '#c15b69',
    teal: '#28786d',
    amber: '#a35e16',
    danger: '#a52c36',
    blue: '#245c70',
    muted: '#6f676b',
    line: '#ded6d4',
  };
  const categorical = [palette.plum, palette.teal, palette.amber, palette.rose, palette.plumDark, palette.blue, palette.danger, palette.muted];

  Chart.defaults.font.family = "Inter, ui-sans-serif, system-ui, sans-serif";
  Chart.defaults.font.size = 11;
  Chart.defaults.color = '#6f676b';
  Chart.defaults.plugins.legend.labels.boxWidth = 10;
  Chart.defaults.plugins.legend.labels.boxHeight = 10;

  const baseGrid = { color: '#f1ece9', drawBorder: false };

  function makeChart(id, config) {
    const canvas = document.getElementById(id);
    if (!canvas) return;
    new Chart(canvas, config);
  }

  makeChart('chart-category', {
    type: 'bar',
    data: {
      labels: data.category.labels,
      datasets: [{ data: data.category.values, backgroundColor: categorical, borderRadius: 4, maxBarThickness: 28 }],
    },
    options: {
      indexAxis: 'y',
      plugins: { legend: { display: false } },
      scales: { x: { beginAtZero: true, ticks: { precision: 0 }, grid: baseGrid }, y: { grid: { display: false } } },
    },
  });

  makeChart('chart-risk', {
    type: 'doughnut',
    data: {
      labels: data.risk.labels,
      datasets: [{ data: data.risk.values, backgroundColor: [palette.teal, palette.amber, palette.rose, palette.danger] }],
    },
    options: { plugins: { legend: { position: 'bottom' } }, cutout: '62%' },
  });

  makeChart('chart-status', {
    type: 'bar',
    data: {
      labels: data.status.labels,
      datasets: [{ data: data.status.values, backgroundColor: palette.plum, borderRadius: 4, maxBarThickness: 28 }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: { x: { grid: { display: false } }, y: { beginAtZero: true, ticks: { precision: 0 }, grid: baseGrid } },
    },
  });

  makeChart('chart-timeline', {
    type: 'line',
    data: {
      labels: data.timeline.labels,
      datasets: [{
        data: data.timeline.values, borderColor: palette.plum, backgroundColor: 'rgba(116,35,74,.12)',
        fill: true, tension: .3, pointRadius: 3, pointBackgroundColor: palette.plum,
      }],
    },
    options: {
      plugins: { legend: { display: false } },
      scales: { x: { grid: { display: false } }, y: { beginAtZero: true, ticks: { precision: 0 }, grid: baseGrid } },
    },
  });

  makeChart('chart-source', {
    type: 'doughnut',
    data: {
      labels: data.source.labels,
      datasets: [{ data: data.source.values, backgroundColor: [palette.teal, palette.danger] }],
    },
    options: { plugins: { legend: { position: 'bottom' } }, cutout: '62%' },
  });

  makeChart('chart-alert-status', {
    type: 'doughnut',
    data: {
      labels: data.alert_status.labels,
      datasets: [{ data: data.alert_status.values, backgroundColor: [palette.amber, palette.blue, palette.rose, palette.teal] }],
    },
    options: { plugins: { legend: { position: 'bottom' } }, cutout: '62%' },
  });
})();
