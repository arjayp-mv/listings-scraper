/**
 * =============================================================================
 * Amazon Reviews Scraper - Competitor Dashboard Page
 * =============================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
    loadDashboard();
    setupEventListeners();
    // Refresh every 60 seconds
    setInterval(loadDashboard, 60000);
});

function setupEventListeners() {
    const exportBtn = document.getElementById('export-csv-btn');
    if (exportBtn) {
        exportBtn.addEventListener('click', (e) => {
            e.preventDefault();
            window.location.href = api.getCompetitorExportCsvUrl();
        });
    }
}

async function loadDashboard() {
    try {
        const [stats, jobs] = await Promise.all([
            api.getCompetitorDashboardStats(),
            api.listCompetitorScrapeJobs(1, 5)
        ]);

        // Update stats
        document.getElementById('stat-total-competitors').textContent = stats.total_competitors || 0;
        document.getElementById('stat-parent-skus').textContent = stats.total_parent_skus || 0;
        document.getElementById('stat-keywords').textContent = stats.total_keywords || 0;
        document.getElementById('stat-scheduled').textContent = stats.scheduled_count || 0;
        document.getElementById('stat-price-drops').textContent = stats.price_drops_7d || 0;
        document.getElementById('stat-price-increases').textContent = stats.price_increases_7d || 0;

        // Render price changes
        renderPriceChanges(stats.recent_price_changes || []);

        // Render scrape jobs
        renderScrapeJobs(jobs.items || []);

    } catch (error) {
        console.error('Failed to load dashboard:', error);
        document.getElementById('price-changes-body').innerHTML =
            '<tr><td colspan="6" class="empty-state">Failed to load data</td></tr>';
        document.getElementById('scrape-jobs-body').innerHTML =
            '<tr><td colspan="5" class="empty-state">Failed to load data</td></tr>';
    }
}

function renderPriceChanges(changes) {
    const tbody = document.getElementById('price-changes-body');

    if (!changes || changes.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No recent price changes</td></tr>';
        return;
    }

    let html = '';
    for (const change of changes) {
        const priceDiff = change.new_price - change.old_price;
        const isDecrease = priceDiff < 0;
        const changeClass = isDecrease ? 'text-success' : 'text-danger';
        const changeIcon = isDecrease ? '&#x25BC;' : '&#x25B2;';
        const percentChange = change.old_price > 0
            ? ((priceDiff / change.old_price) * 100).toFixed(1)
            : 0;

        html += '<tr>' +
            '<td>' +
                '<a href="competitor-detail.html?id=' + change.competitor_id + '" class="text-link">' +
                    escapeHtml(change.competitor_asin || 'N/A') +
                '</a>' +
            '</td>' +
            '<td>' + escapeHtml(change.sku_code || 'N/A') + '</td>' +
            '<td>' + formatCurrency(change.old_price, change.currency) + '</td>' +
            '<td>' + formatCurrency(change.new_price, change.currency) + '</td>' +
            '<td class="' + changeClass + '">' +
                changeIcon + ' ' + formatCurrency(Math.abs(priceDiff), change.currency) +
                ' (' + percentChange + '%)' +
            '</td>' +
            '<td>' + formatDate(change.recorded_at) + '</td>' +
        '</tr>';
    }
    tbody.innerHTML = html;
}

function renderScrapeJobs(jobs) {
    const tbody = document.getElementById('scrape-jobs-body');

    if (!jobs || jobs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="5" class="empty-state">No scrape jobs yet</td></tr>';
        return;
    }

    let html = '';
    for (const job of jobs) {
        html += '<tr>' +
            '<td>' + escapeHtml(job.job_name || 'Unnamed Job') + '</td>' +
            '<td>' + formatJobType(job.job_type) + '</td>' +
            '<td>' +
                '<span class="status-badge ' + getStatusClass(job.status) + '">' +
                    formatStatus(job.status) +
                '</span>' +
            '</td>' +
            '<td>' + (job.completed_items || 0) + ' / ' + (job.total_items || 0) + '</td>' +
            '<td>' + formatDate(job.created_at) + '</td>' +
        '</tr>';
    }
    tbody.innerHTML = html;
}

function formatJobType(type) {
    const types = {
        manual: 'Manual',
        scheduled: 'Scheduled',
        keyword_research: 'Keyword Research'
    };
    return types[type] || type;
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

function formatCurrency(amount, currency = 'USD') {
    if (amount === null || amount === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency || 'USD'
    }).format(amount);
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
