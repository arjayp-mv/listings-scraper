/**
 * =============================================================================
 * Amazon Reviews Scraper - Job Detail Page
 * =============================================================================
 */

let jobId = null;
let jobData = null;
let formattedText = '';

document.addEventListener('DOMContentLoaded', () => {
    // Get job ID from URL
    const params = new URLSearchParams(window.location.search);
    jobId = params.get('id');

    if (!jobId) {
        alert('No job ID provided');
        window.location.href = 'jobs.html';
        return;
    }

    // Initialize tabs
    initTabs();

    // Load data
    loadJob();
    loadFormattedReviews();
    loadReviewStats();

    // Set export link
    document.getElementById('export-excel').href = api.getExcelExportUrl(jobId);

    // Auto-refresh if job is running
    setInterval(() => {
        if (jobData && (jobData.status === 'running' || jobData.status === 'queued')) {
            loadJob();
            loadFormattedReviews();
        }
    }, 5000);
});

function initTabs() {
    const tabs = document.querySelectorAll('.tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Update active tab
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // Show/hide content
            const tabName = tab.dataset.tab;
            document.getElementById('reviews-tab').style.display = tabName === 'reviews' ? 'block' : 'none';
            document.getElementById('asins-tab').style.display = tabName === 'asins' ? 'block' : 'none';
        });
    });
}

async function loadJob() {
    try {
        const job = await api.getJob(jobId);
        jobData = job;

        // Update header
        document.getElementById('job-name').textContent = job.job_name;
        document.getElementById('job-meta').innerHTML = `
            ${job.sku_code ? `SKU: ${escapeHtml(job.sku_code)} &bull; ` : ''}
            Marketplace: amazon.${job.marketplace} &bull;
            Created: ${formatDate(job.created_at)}
        `;

        document.getElementById('job-status').innerHTML = `
            <span class="badge badge-${job.status}" style="font-size: 16px; padding: 8px 16px;">
                ${job.status.toUpperCase()}
            </span>
        `;

        // Update stats
        document.getElementById('stat-asins').textContent = job.total_asins;
        document.getElementById('stat-completed').textContent = job.completed_asins;
        document.getElementById('stat-failed').textContent = job.failed_asins;
        document.getElementById('stat-reviews').textContent = formatNumber(job.total_reviews);

        // Update actions
        renderActions(job);

        // Update ASINs table
        renderAsins(job.asins);

    } catch (error) {
        console.error('Failed to load job:', error);
        document.getElementById('job-name').textContent = 'Error loading job';
    }
}

function renderActions(job) {
    const actions = [];

    if (job.status === 'queued' || job.status === 'running') {
        actions.push(`<button class="btn btn-danger" onclick="cancelJob()">Cancel Job</button>`);
    }

    if ((job.status === 'completed' || job.status === 'partial' || job.status === 'failed') && job.failed_asins > 0) {
        actions.push(`<button class="btn btn-secondary" onclick="retryFailed()">Retry Failed ASINs (${job.failed_asins})</button>`);
    }

    if (job.status !== 'queued' && job.status !== 'running') {
        actions.push(`<button class="btn btn-danger" onclick="deleteJob()">Delete Job</button>`);
    }

    document.getElementById('job-actions').innerHTML = actions.join('');
}

function renderAsins(asins) {
    const tbody = document.getElementById('asins-body');

    if (!asins || asins.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-state">No ASINs</td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = asins.map(asin => `
        <tr>
            <td>
                <a href="https://www.amazon.com/dp/${asin.asin}" target="_blank" style="color: var(--primary);">
                    ${asin.asin}
                </a>
            </td>
            <td>${asin.product_title ? escapeHtml(asin.product_title.substring(0, 60)) + '...' : '<span class="text-muted">-</span>'}</td>
            <td>
                <span class="badge badge-${asin.status}">${asin.status}</span>
            </td>
            <td>${formatNumber(asin.reviews_found)}</td>
            <td class="text-danger">${asin.error_message ? escapeHtml(asin.error_message.substring(0, 50)) : ''}</td>
        </tr>
    `).join('');
}

async function loadFormattedReviews() {
    const search = document.getElementById('review-search').value.trim();
    const rating = document.getElementById('review-rating-filter').value;

    try {
        const result = await api.getFormattedReviews(jobId, search || null, rating || null);
        formattedText = result.formatted_text;

        // Update count
        document.getElementById('copy-count').textContent = `${result.total} reviews`;

        // Update output display
        const output = document.getElementById('review-output');
        if (result.total === 0) {
            output.textContent = 'No reviews found';
        } else {
            output.textContent = formattedText;
        }

    } catch (error) {
        console.error('Failed to load reviews:', error);
        document.getElementById('review-output').textContent = 'Error loading reviews';
    }
}

async function loadReviewStats() {
    try {
        const stats = await api.getReviewStats(jobId);
        if (stats.average_rating) {
            document.getElementById('stat-rating').textContent = stats.average_rating.toFixed(1);
        }
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function copyAllReviews() {
    const btn = document.getElementById('copy-btn');

    try {
        await navigator.clipboard.writeText(formattedText);

        // Show success state
        btn.textContent = 'Copied!';
        btn.classList.add('copied');

        setTimeout(() => {
            btn.textContent = 'Copy All Reviews';
            btn.classList.remove('copied');
        }, 2000);

    } catch (error) {
        // Fallback for older browsers
        const textarea = document.createElement('textarea');
        textarea.value = formattedText;
        document.body.appendChild(textarea);
        textarea.select();
        document.execCommand('copy');
        document.body.removeChild(textarea);

        btn.textContent = 'Copied!';
        btn.classList.add('copied');

        setTimeout(() => {
            btn.textContent = 'Copy All Reviews';
            btn.classList.remove('copied');
        }, 2000);
    }
}

async function exportJson() {
    try {
        const data = await api.exportReviewsJson(jobId);
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);

        const a = document.createElement('a');
        a.href = url;
        a.download = `${jobData.job_name.replace(/[^a-z0-9]/gi, '_')}_reviews.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

    } catch (error) {
        alert('Failed to export: ' + error.message);
    }
}

async function cancelJob() {
    if (!confirm('Are you sure you want to cancel this job?')) return;

    try {
        await api.cancelJob(jobId);
        loadJob();
    } catch (error) {
        alert('Failed to cancel job: ' + error.message);
    }
}

async function retryFailed() {
    try {
        await api.retryFailedAsins(jobId);
        alert('Failed ASINs queued for retry');
        loadJob();
    } catch (error) {
        alert('Failed to retry: ' + error.message);
    }
}

async function deleteJob() {
    if (!confirm('Are you sure you want to delete this job? This will also delete all reviews.')) return;

    try {
        await api.deleteJob(jobId);
        window.location.href = 'jobs.html';
    } catch (error) {
        alert('Failed to delete job: ' + error.message);
    }
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
