/**
 * =============================================================================
 * Amazon Reviews Scraper - Dashboard Page
 * =============================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    // Refresh every 30 seconds
    setInterval(loadDashboard, 30000);
});

async function loadDashboard() {
    try {
        const stats = await api.getDashboardStats();

        // Update review scrape stats
        document.getElementById('stat-total-jobs').textContent = stats.total_jobs;
        document.getElementById('stat-running').textContent = (stats.running_jobs || 0) + (stats.product_scan_running || 0);
        document.getElementById('stat-reviews').textContent = formatNumber(stats.total_reviews);
        document.getElementById('stat-skus').textContent = stats.total_skus;

        // Update product scan stats (from dashboard stats which includes these)
        document.getElementById('stat-scans').textContent = stats.total_product_scans || 0;
        document.getElementById('stat-listings').textContent = stats.total_channel_skus || 0;

        // Update recent jobs
        renderRecentJobs(stats.recent_jobs);

    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

function renderRecentJobs(jobs) {
    const tbody = document.getElementById('recent-jobs-body');

    if (!jobs || jobs.length === 0) {
        tbody.innerHTML = '<tr>' +
            '<td colspan="5" class="empty-state">' +
                'No jobs yet. <a href="new-scrape.html">Start your first scrape</a>' +
            '</td>' +
        '</tr>';
        return;
    }

    let html = '';
    for (const job of jobs) {
        html += '<tr>' +
            '<td>' +
                '<a href="job-detail.html?id=' + job.id + '" style="color: var(--primary-500); text-decoration: none; font-weight: 500;">' +
                    escapeHtml(job.job_name) +
                '</a>' +
            '</td>' +
            '<td>' +
                '<span class="status-badge ' + getStatusClass(job.status) + '">' + formatStatus(job.status) + '</span>' +
            '</td>' +
            '<td>' + formatNumber(job.total_reviews) + '</td>' +
            '<td>' + formatDate(job.created_at) + '</td>' +
            '<td>' +
                '<a href="job-detail.html?id=' + job.id + '" class="btn btn-secondary btn-sm">View</a>' +
            '</td>' +
        '</tr>';
    }
    tbody.innerHTML = html;
}

function getStatusClass(status) {
    const classes = {
        queued: 'pending',
        running: 'running',
        completed: 'completed',
        failed: 'failed',
        cancelled: 'cancelled'
    };
    return classes[status] || 'pending';
}

function formatStatus(status) {
    return status.charAt(0).toUpperCase() + status.slice(1);
}

function formatNumber(num) {
    if (num === null || num === undefined) return '0';
    return num.toLocaleString();
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
