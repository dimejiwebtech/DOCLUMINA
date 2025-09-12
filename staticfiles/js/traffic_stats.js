let mainChart;
let currentMainPeriod = 'week';

document.addEventListener('DOMContentLoaded', function () {
  currentMainPeriod = localStorage.getItem('selectedPeriod') || 'week';
  setupMainChart();
  updateChartForPeriod(currentMainPeriod);
  loadMainData();
  setupPeriodToggle();
  setupChartToggles();
  setupDatePicker();
  
  document.addEventListener('click', function (e) {
    if (e.target.hasAttribute('data-tab')) {
      const tabType = e.target.getAttribute('data-tab');
      switchLocationTab(tabType);
    }
  });

   switchLocationTab('countries');

});

function setupPeriodToggle() {
  document.getElementById('period-dropdown').value = currentMainPeriod;
  document
    .getElementById('period-dropdown')
    .addEventListener('change', function () {
      currentMainPeriod = this.value;
      localStorage.setItem('selectedPeriod', this.value);
      updateChartForPeriod(currentMainPeriod);
      loadMainData(); 
    });
}

function setupChartToggles() {
  document
    .getElementById('views-toggle')
    .addEventListener('change', updateMainChart);
  document
    .getElementById('visitors-toggle')
    .addEventListener('change', updateMainChart);
}

function setupMainChart() {
  const ctx = document.getElementById('main-chart').getContext('2d');
  mainChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Views',
          data: [],
          backgroundColor: '#22c55e',
          borderRadius: 4,
          order: 0,
        },
        {
          label: 'Visitors',
          data: [],
          backgroundColor: 'rgba(6, 95, 70, 0.8)',
          borderRadius: 4,
          order: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: true,
      aspectRatio: 3,
      interaction: {
        mode: 'index',
        intersect: false,
      },
      scales: {
        x: {
          stacked: true,
          grid: { display: false },
          barPercentage: 1.0,
          categoryPercentage: 1.0,
        },
        y: {
          stacked: true,
          beginAtZero: true,
        },
      },
      plugins: {
        legend: { display: false },
      },
    },
  });
}

function updateMainChart() {
  const showViews = document.getElementById('views-toggle').checked;
  const showVisitors = document.getElementById('visitors-toggle').checked;

  mainChart.data.datasets[0].hidden = !showViews;
  mainChart.data.datasets[1].hidden = !showVisitors;
  mainChart.update();
}

function updateChartForPeriod(period) {
  let labels, viewsData, visitorsData;

  switch (period) {
    case 'today':
      labels = ['00:00', '04:00', '08:00', '12:00', '16:00', '20:00'];
      viewsData = [50, 80, 120, 200, 150, 90];
      visitorsData = [30, 50, 80, 120, 90, 60];
      break;
    case 'week':
      labels = [
        'Aug 27',
        'Aug 28',
        'Aug 29',
        'Aug 30',
        'Aug 31',
        'Sep 1',
        'Sep 2',
      ];
      viewsData = [290, 180, 100, 80, 110, 140, 130];
      visitorsData = [140, 110, 60, 50, 70, 90, 85];
      break;
    case 'month':
      labels = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep'];
      viewsData = [2500, 3200, 2800, 3500, 4100, 3800, 4200, 3900, 2100];
      visitorsData = [1200, 1600, 1400, 1750, 2050, 1900, 2100, 1950, 1050];
      break;
    case 'year':
      labels = ['2020', '2021', '2022', '2023', '2024', '2025'];
      viewsData = [15000, 25000, 35000, 45000, 52000, 48000];
      visitorsData = [8000, 12000, 18000, 22000, 26000, 24000];
      break;
  }

  mainChart.data.labels = labels;
  mainChart.data.datasets[0].data = viewsData;
  mainChart.data.datasets[1].data = visitorsData;
  mainChart.update();
}

function setupDatePicker() {
  const startDate = document.getElementById('start-date');
  const endDate = document.getElementById('end-date');
  const applyBtn = document.getElementById('apply-date-range');

  // Set default dates (last 7 days)
  const today = new Date();
  const weekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);

  endDate.value = today.toISOString().split('T')[0];
  startDate.value = weekAgo.toISOString().split('T')[0];

  applyBtn.addEventListener('click', function () {
    if (startDate.value && endDate.value) {
      loadCustomDateData(startDate.value, endDate.value);
    }
  });
}

function loadCustomDateData(startDate, endDate) {
  // Calculate the difference in days to determine appropriate labels
  const start = new Date(startDate);
  const end = new Date(endDate);
  const diffTime = Math.abs(end - start);
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  // Generate appropriate labels based on date range
  let labels = [];
  if (diffDays <= 7) {
    // Daily labels for week or less
    for (let d = new Date(start); d <= end; d.setDate(d.getDate() + 1)) {
      labels.push(
        d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
      );
    }
  } else if (diffDays <= 60) {
    // Weekly labels for 2 months or less
    let current = new Date(start);
    while (current <= end) {
      labels.push(
        `Week ${current.toLocaleDateString('en-US', {
          month: 'short',
          day: 'numeric',
        })}`
      );
      current.setDate(current.getDate() + 7);
    }
  } else {
    // Monthly labels for longer periods
    let current = new Date(start);
    while (current <= end) {
      labels.push(
        current.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })
      );
      current.setMonth(current.getMonth() + 1);
    }
  }

  fetch(
    `/dashboard/analytics/traffic-data/?start_date=${startDate}&end_date=${endDate}&custom_range=true`
  )
    .then((response) => response.json())
    .then((data) => {
      // Use backend data if available, otherwise generate placeholder data
      mainChart.data.labels = data.labels || labels;
      mainChart.data.datasets[0].data =
        data.views || generatePlaceholderData(labels.length, 50, 300);
      mainChart.data.datasets[1].data =
        data.visitors || generatePlaceholderData(labels.length, 20, 150);
      mainChart.update();

      updateMainStats(data);
      updateMostViewed(data.top_pages || []);
      updateReferrers(data.traffic_sources || []);
      updateLocations(data);
    })
    .catch((error) => {
      console.error('Error:', error);
      // Fallback: show placeholder data even if backend fails
      mainChart.data.labels = labels;
      mainChart.data.datasets[0].data = generatePlaceholderData(
        labels.length,
        50,
        300
      );
      mainChart.data.datasets[1].data = generatePlaceholderData(
        labels.length,
        20,
        150
      );
      mainChart.update();
    });
}

function generatePlaceholderData(length, min, max) {
  return Array.from(
    { length },
    () => Math.floor(Math.random() * (max - min + 1)) + min
  );
}

function loadMainData() {
  fetch(`/dashboard/analytics/traffic-data/?period=${currentMainPeriod}`)
    .then((response) => response.json())
    .then((data) => {
      

      updateMainStats(data);
      updateMostViewed(data.top_pages);
      updateReferrers(data.traffic_sources);
      updateLocations(data);
    })
    .catch((error) => console.error('Error:', error));
}

// Helper function for fallback labels
function generateDateLabels(period) {
  const labels = [];
  const today = new Date();

  for (let i = 6; i >= 0; i--) {
    const date = new Date(today);
    date.setDate(today.getDate() - i);
    labels.push(
      date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    );
  }

  return labels;
}

function updateMainStats(data) {
  document.getElementById('total-views-stat').textContent =
    data.total_views.toLocaleString();
  document.getElementById('total-visitors-stat').textContent = Math.floor(
    data.total_views * 0.6
  ).toLocaleString();
}

function updateMostViewed(pages) {
  const container = document.getElementById('most-viewed-list');
  container.innerHTML = '';

  pages.slice(0, 8).forEach((page) => {
    container.innerHTML += `
            <div class="flex justify-between items-center py-2">
                <div class="flex-1">
                    <div class="text-sm font-medium text-gray-900">${
                      page.page_title || 'Unknown Page'
                    }</div>
                    <div class="text-xs text-gray-500">${page.page_url}</div>
                </div>
                <div class="text-sm font-semibold text-gray-700 ml-4">${
                  page.views
                }</div>
            </div>
        `;
  });
}

function updateReferrers(sources) {
  const container = document.getElementById('referrers-list');
  container.innerHTML = '';

  sources.forEach((source) => {
    const sourceName =
      source.traffic_source.charAt(0).toUpperCase() +
      source.traffic_source.slice(1);
    container.innerHTML += `
            <div class="flex justify-between items-center py-2">
                <span class="text-sm text-gray-700">${sourceName}</span>
                <span class="text-sm font-semibold text-gray-700">${source.count}</span>
            </div>
        `;
  });
}

function updateLocations(data) {
  const container = document.getElementById('location-data');
  const locations = data.locations || [];

  container.innerHTML = '';
  locations.forEach((location) => {
    container.innerHTML += `
            <div class="flex justify-between items-center py-1">
                <span class="text-sm text-gray-700">${location.name}</span>
                <span class="text-sm font-semibold text-gray-700">${location.count}</span>
            </div>
        `;
  });
}



function switchLocationTab(type) {
  // Remove active classes from all tabs
  document.querySelectorAll('[data-tab]').forEach((tab) => {
    tab.className = 'flex-1 px-3 py-2 text-sm bg-gray-200 text-gray-700';
  });

  // Add active classes to clicked tab
  const activeTab = document.querySelector(`[data-tab="${type}"]`);
  if (type === 'countries') {
    activeTab.className =
      'flex-1 px-3 py-2 text-sm bg-green-600 text-white rounded-l';
  } else {
    activeTab.className =
      'flex-1 px-3 py-2 text-sm bg-green-600 text-white rounded-r';
  }

  // Show/hide map based on tab type
  const mapContainer = document.getElementById('locations-map');
  if (type === 'countries') {
    mapContainer.style.display = 'flex';
  } else {
    mapContainer.style.display = 'none';
  }

  console.log('Switching to:', type);
  loadLocationData(type);
}



function loadLocationData(type) {
  fetch(`/dashboard/analytics/location-data/?type=${type}`)
    .then((response) => response.json())
    .then((data) => updateLocations(data))
    .catch((error) => console.error('Error:', error));
}

