/**
 * =============================================================================
 * Amazon Reviews Scraper - Jobs List Page
 * =============================================================================
 */

let currentPage = 1;
const pageSize = 20;

// Get SKU filter from URL params
const urlParams = new URLSearchParams(window.location.search);
let skuIdFilter = urlParams.get('sku_id');

let skuSearchTimeout = null;

document.addEventListener('DOMContentLoaded', async () => {
    // If filtering by SKU from URL, load SKU info and set the search field
    if (skuIdFilter) {
        await loadSkuFromUrl();
    }

    loadJobs();
    // Auto-refresh every 10 seconds for running jobs
    setInterval(loadJobs, 10000);

    // Close autocomplete when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.autocomplete-container')) {
            hideSkuAutocomplete();
        }
    });
});

async function loadSkuFromUrl() {
    try {
        const sku = await api.getSku(skuIdFilter);
        document.getElementById('filter-sku-search').value = sku.sku_code;
        document.getElementById('filter-sku-id').value = sku.id;
        document.getElementById('clear-sku-filter').style.display = 'inline-flex';
    } catch (error) {
        console.error('Failed to load SKU from URL:', error);
    }
}

function onSkuSearchInput() {
    const query = document.getElementById('filter-sku-search').value.trim();

    // Clear existing timeout
    if (skuSearchTimeout) {
        clearTimeout(skuSearchTimeout);
    }

    // If empty, clear filter
    if (!query) {
        document.getElementById('filter-sku-id').value = '';
        document.getElementById('clear-sku-filter').style.display = 'none';
        skuIdFilter = null;
        hideSkuAutocomplete();
        currentPage = 1;
        loadJobs();
        return;
    }

    // Debounce search
    skuSearchTimeout = setTimeout(async () => {
        await searchSkus(query);
    }, 200);
}

function onSkuSearchFocus() {
    const query = document.getElementById('filter-sku-search').value.trim();
    if (query) {
        searchSkus(query);
    }
}

async function searchSkus(query) {
    try {
        const results = await api.searchSkus(query);
        showSkuAutocomplete(results);
    } catch (error) {
        console.error('Failed to search SKUs:', error);
    }
}

function showSkuAutocomplete(skus) {
    const container = document.getElementById('sku-autocomplete-results');

    if (!skus || skus.length === 0) {
        container.innerHTML = '<div class="autocomplete-empty">No SKUs found</div>';
        container.classList.add('active');
        return;
    }

    container.innerHTML = skus.map(sku => `
        <div class="autocomplete-item" onclick="selectSku(${sku.id}, '${escapeHtml(sku.sku_code)}')">
            <div class="sku-code">${escapeHtml(sku.sku_code)}</div>
            ${sku.description ? `<div class="sku-description">${escapeHtml(sku.description)}</div>` : ''}
        </div>
    `).join('');

    container.classList.add('active');
}

function hideSkuAutocomplete() {
    document.getElementById('sku-autocomplete-results').classList.remove('active');
}

function selectSku(id, code) {
    document.getElementById('filter-sku-search').value = code;
    document.getElementById('filter-sku-id').value = id;
    document.getElementById('clear-sku-filter').style.display = 'inline-flex';
    skuIdFilter = id;
    hideSkuAutocomplete();
    currentPage = 1;
    loadJobs();
}

function clearSkuFilter() {
    document.getElementById('filter-sku-search').value = '';
    document.getElementById('filter-sku-id').value = '';
    document.getElementById('clear-sku-filter').style.display = 'none';
    skuIdFilter = null;
    currentPage = 1;
    loadJobs();
}


async function loadJobs() {
    const status = document.getElementById('filter-status').value;

    try {
        const result = await api.listJobs(currentPage, pageSize, status || null, skuIdFilter);
        renderJobs(result.items);
        renderPagination(result);
    } catch (error) {
        console.error('Failed to load jobs:', error);
        document.getElementById('jobs-body').innerHTML = `
            <tr>
                <td colspan="7" class="text-danger">Failed to load jobs: ${escapeHtml(error.message)}</td>
            </tr>
        `;
    }
}

function renderJobs(jobs) {
    const tbody = document.getElementById('jobs-body');

    if (!jobs || jobs.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" class="empty-state">
                    No jobs found. <a href="new-scrape.html">Start your first scrape</a>
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
            <td>${job.sku_code ? escapeHtml(job.sku_code) : '<span class="text-muted">-</span>'}</td>
            <td>
                <span class="badge badge-${job.status}">${job.status}</span>
            </td>
            <td>
                ${job.completed_asins + job.failed_asins}/${job.total_asins} ASINs
                ${job.failed_asins > 0 ? `<span class="text-danger">(${job.failed_asins} failed)</span>` : ''}
            </td>
            <td>${formatNumber(job.total_reviews)}</td>
            <td>${formatDate(job.created_at)}</td>
            <td>
                <div class="flex gap-1">
                    <a href="job-detail.html?id=${job.id}" class="btn btn-secondary btn-sm">View</a>
                    ${job.status === 'queued' || job.status === 'running' ?
                        `<button class="btn btn-danger btn-sm" onclick="cancelJob(${job.id})">Cancel</button>` : ''}
                    ${job.status === 'completed' || job.status === 'partial' || job.status === 'failed' ?
                        `<button class="btn btn-danger btn-sm" onclick="deleteJob(${job.id})">Delete</button>` : ''}
                </div>
            </td>
        </tr>
    `).join('');
}

function renderPagination(result) {
    const pagination = document.getElementById('pagination');

    if (result.total_pages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    pagination.innerHTML = `
        <button class="pagination-btn" onclick="goToPage(${currentPage - 1})" ${!result.has_previous ? 'disabled' : ''}>
            Previous
        </button>
        <span class="pagination-info">
            Page ${result.page} of ${result.total_pages}
        </span>
        <button class="pagination-btn" onclick="goToPage(${currentPage + 1})" ${!result.has_next ? 'disabled' : ''}>
            Next
        </button>
    `;
}

function goToPage(page) {
    currentPage = page;
    loadJobs();
}

async function cancelJob(jobId) {
    if (!confirm('Are you sure you want to cancel this job?')) return;

    try {
        await api.cancelJob(jobId);
        loadJobs();
    } catch (error) {
        alert('Failed to cancel job: ' + error.message);
    }
}

async function deleteJob(jobId) {
    if (!confirm('Are you sure you want to delete this job? This will also delete all reviews.')) return;

    try {
        await api.deleteJob(jobId);
        loadJobs();
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
