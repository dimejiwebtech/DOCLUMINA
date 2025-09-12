let analyticsChart;
let currentPeriod = 'week';

// Initialize widget
document.addEventListener('DOMContentLoaded', function () {
  loadAnalyticsData();
  setupPeriodTabs();
});

function setupPeriodTabs() {
  document.querySelectorAll('.period-btn').forEach((btn) => {
    btn.addEventListener('click', function () {
      // Update active state
      document.querySelectorAll('.period-btn').forEach((b) => {
        b.classList.remove('bg-gray-800', 'text-white', 'active');
        b.classList.add('bg-gray-200', 'text-gray-700');
      });

      this.classList.remove('bg-gray-200', 'text-gray-700');
      this.classList.add('bg-gray-800', 'text-white', 'active');

      currentPeriod = this.getAttribute('data-period');
      loadAnalyticsData();
    });
  });
}

function loadAnalyticsData() {
  fetch(`/dashboard/analytics/dashboard-data/?period=${currentPeriod}`)
    .then((response) => response.json())
    .then((data) => {
      updateStats(data);
      updateChart(data);
      updatePeriodTitle();
    })
    .catch((error) => {
      console.error('Error loading analytics:', error);
      document.getElementById('total-views').textContent = 'Error';
      document.getElementById('top-source').textContent = 'Error';
    });
}

function updateStats(data) {
  document.getElementById('total-views').textContent =
    data.total_views.toLocaleString();

  // Find top traffic source
document.getElementById('total-views').textContent =
  data.total_views.toLocaleString();

const topSource =
  data.traffic_sources.length > 0
    ? data.traffic_sources.reduce((a, b) => (a.count > b.count ? a : b))
    : { traffic_source: 'None', count: 0 };

document.getElementById('top-source').textContent =
  topSource.traffic_source.charAt(0).toUpperCase() +
  topSource.traffic_source.slice(1);

// NEW: Update posts and referrers content
updatePostsContent(data.top_pages);
updateReferrersContent(data.traffic_sources);

}

function updatePostsContent(pages) {
  const container = document.getElementById('posts-content');
  container.innerHTML = '';

  pages.slice(0, 5).forEach((page) => {
    container.innerHTML += `
            <div class="flex justify-between items-center text-sm">
                <span class="text-gray-700 truncate flex-1 mr-2">${
                  page.page_title || 'Unknown Page'
                }</span>
                <span class="text-gray-900 font-medium">${
                  page.views
                } Views</span>
            </div>
        `;
  });
}

function updateReferrersContent(sources) {
  const container = document.getElementById('referrers-content');
  container.innerHTML = '';

  sources.forEach((source) => {
    const sourceName =
      source.traffic_source.charAt(0).toUpperCase() +
      source.traffic_source.slice(1);
    container.innerHTML += `
            <div class="flex justify-between items-center text-sm">
                <span class="text-gray-700">${sourceName}</span>
                <span class="text-gray-900 font-medium">${source.count} visits</span>
            </div>
        `;
  });
}



function updateChart(data) {
  const ctx = document.getElementById('analytics-chart').getContext('2d');

  // Use real data from server - no more mock generation
  let chartData = data.chart_data || [];
  let labels = data.labels || [];

  if (analyticsChart) {
    analyticsChart.destroy();
  }

  analyticsChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [
        {
          data: chartData,
          backgroundColor: '#10b981',
          borderRadius: 4,
          barThickness: 20,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
      },
      scales: {
        y: {
          beginAtZero: true,
          display: false,
        },
        x: {
          display: false,
        },
      },
    },
  });
}

function updatePeriodTitle() {
  const titles = {
    today: 'Last 7 Days', 
    week: 'Weekly Overview',
    month: 'Monthly Overview',
    year: 'Yearly Overview',
  };

  document.getElementById('period-title').textContent = titles[currentPeriod];
}

// Setup tabs
document.addEventListener('DOMContentLoaded', function() {
    setupTabSwitching();
});

function setupTabSwitching() {
    document.getElementById('posts-tab').addEventListener('click', function() {
        showTab('posts');
    });
    
    document.getElementById('referrers-tab').addEventListener('click', function() {
        showTab('referrers');
    });
}

function showTab(tab) {
    // Update tab buttons
    if (tab === 'posts') {
        document.getElementById('posts-tab').classList.add('bg-gray-800', 'text-white');
        document.getElementById('posts-tab').classList.remove('bg-gray-200', 'text-gray-700');
        document.getElementById('referrers-tab').classList.add('bg-gray-200', 'text-gray-700');
        document.getElementById('referrers-tab').classList.remove('bg-gray-800', 'text-white');
        
        document.getElementById('posts-content').classList.remove('hidden');
        document.getElementById('referrers-content').classList.add('hidden');
    } else {
        document.getElementById('referrers-tab').classList.add('bg-gray-800', 'text-white');
        document.getElementById('referrers-tab').classList.remove('bg-gray-200', 'text-gray-700');
        document.getElementById('posts-tab').classList.add('bg-gray-200', 'text-gray-700');
        document.getElementById('posts-tab').classList.remove('bg-gray-800', 'text-white');
        
        document.getElementById('referrers-content').classList.remove('hidden');
        document.getElementById('posts-content').classList.add('hidden');
    }
}