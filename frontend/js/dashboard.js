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

        // Update stats
        document.getElementById('stat-total-jobs').textContent = stats.total_jobs;
        document.getElementById('stat-queued').textContent = stats.queued_jobs;
        document.getElementById('stat-running').textContent = stats.running_jobs;
        document.getElementById('stat-completed').textContent = stats.completed_jobs;
        document.getElementById('stat-reviews').textContent = formatNumber(stats.total_reviews);
        document.getElementById('stat-skus').textContent = stats.total_skus;

        // Update recent jobs
        renderRecentJobs(stats.recent_jobs);

    } catch (error) {
        console.error('Failed to load dashboard:', error);
    }
}

function renderRecentJobs(jobs) {
    const tbody = document.getElementById('recent-jobs-body');

    if (!jobs || jobs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-state">
                    No jobs yet. <a href="new-scrape.html">Start your first scrape</a>
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = jobs.map(job => `
        <tr>
            <td>
                <a href="job-detail.html?id=${job.id}" style="color: var(--primary); text-decoration: none; font-weight: 500;">
                    ${escapeHtml(job.job_name)}
                </a>
            </td>
            <td>
                <span class="badge badge-${job.status}">${job.status}</span>
            </td>
            <td>${formatNumber(job.total_reviews)}</td>
            <td>${formatDate(job.created_at)}</td>
            <td>
                <a href="job-detail.html?id=${job.id}" class="btn btn-secondary btn-sm">
                    View
                </a>
            </td>
        </tr>
    `).join('');
}

function formatNumber(num) {
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
