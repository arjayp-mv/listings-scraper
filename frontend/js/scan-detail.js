/**
 * =============================================================================
 * Scan Detail Page
 * =============================================================================
 * Purpose: Display product scan details and results
 * =============================================================================
 */

// State
let scanId = null;
let scanData = null;
let currentPage = 1;
const pageSize = 20;
let totalPages = 1;
let refreshInterval = null;

// DOM Elements
const resultsBody = document.getElementById('results-body');
const statusFilter = document.getElementById('status-filter');
const paginationContainer = document.getElementById('pagination-container');
const alertContainer = document.getElementById('alert-container');
const progressCard = document.getElementById('progress-card');
const progressBar = document.getElementById('progress-bar');
const progressStatus = document.getElementById('progress-status');
const progressPercent = document.getElementById('progress-percent');
const actionButtons = document.getElementById('action-buttons');

/**
 * Initialize page
 */
async function init() {
    // Get scan ID from URL
    const urlParams = new URLSearchParams(window.location.search);
    scanId = parseInt(urlParams.get('id'));

    if (!scanId) {
        showAlert('Invalid scan ID', 'error');
        return;
    }

    // Load scan details
    await loadScan();

    // Load results
    loadResults();

    // Set up event listeners
    statusFilter.addEventListener('change', () => {
        currentPage = 1;
        loadResults();
    });

    // Auto-refresh if scan is running
    if (scanData && (scanData.status === 'running' || scanData.status === 'queued')) {
        startAutoRefresh();
    }
}

/**
 * Load scan details
 */
async function loadScan() {
    try {
        scanData = await api.getProductScan(scanId);
        renderScanDetails();
    } catch (error) {
        showAlert('Failed to load scan: ' + error.message, 'error');
    }
}

/**
 * Render scan details
 */
function renderScanDetails() {
    // Update page title
    document.getElementById('job-name').textContent = scanData.job_name;
    document.getElementById('breadcrumb-name').textContent = scanData.job_name;
    document.title = scanData.job_name + ' - Amazon Reviews Scraper';

    // Update subtitle with status
    const statusBadge = '<span class="status-badge ' + getStatusClass(scanData.status) + '">' + formatStatus(scanData.status) + '</span>';
    document.getElementById('page-subtitle').innerHTML = statusBadge + ' &middot; ' + formatMarketplace(scanData.marketplace) + ' &middot; Created ' + formatDate(scanData.created_at);

    // Update stats
    document.getElementById('stat-total').textContent = scanData.total_listings || 0;
    document.getElementById('stat-completed').textContent = scanData.completed_listings || 0;
    document.getElementById('stat-failed').textContent = scanData.failed_listings || 0;

    // Calculate aggregates if available
    if (scanData.avg_rating) {
        document.getElementById('stat-avg-rating').textContent = parseFloat(scanData.avg_rating).toFixed(1);
    }
    if (scanData.total_reviews) {
        document.getElementById('stat-total-reviews').textContent = formatNumber(scanData.total_reviews);
    }

    // Progress bar for running scans
    if (scanData.status === 'running' || scanData.status === 'queued') {
        progressCard.style.display = 'block';
        const progress = scanData.total_listings > 0
            ? Math.round((scanData.completed_listings / scanData.total_listings) * 100)
            : 0;
        progressBar.style.width = progress + '%';
        progressPercent.textContent = progress + '%';
        progressStatus.textContent = scanData.status === 'queued' ? 'Waiting to start...' : 'Processing items...';
    } else {
        progressCard.style.display = 'none';
    }

    // Action buttons
    renderActionButtons();
}

/**
 * Render action buttons based on scan status
 */
function renderActionButtons() {
    let html = '';

    if (scanData.status === 'completed') {
        html += '<a href="' + api.getProductScanCsvUrl(scanId) + '" class="btn btn-primary">' +
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>' +
            ' Download CSV' +
        '</a>';
        html += '<a href="' + api.getProductScanExcelUrl(scanId) + '" class="btn btn-secondary">' +
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>' +
            ' Download Excel' +
        '</a>';
    }

    if (scanData.failed_listings > 0 && (scanData.status === 'completed' || scanData.status === 'failed')) {
        html += '<button class="btn btn-secondary" onclick="retryFailed()">' +
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>' +
            ' Retry Failed' +
        '</button>';
    }

    if (scanData.status === 'running' || scanData.status === 'queued') {
        html += '<button class="btn btn-danger" onclick="cancelScan()">' +
            '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>' +
            ' Cancel' +
        '</button>';
    }

    actionButtons.innerHTML = html;
}

/**
 * Load scan results
 */
async function loadResults() {
    const status = statusFilter.value || null;

    try {
        const result = await api.getProductScanResults(scanId, currentPage, pageSize, status);
        renderResults(result.items || []);
        totalPages = result.total_pages || 1;
        renderPagination();
    } catch (error) {
        resultsBody.innerHTML = '<tr><td colspan="6" class="empty-state">Failed to load results: ' + escapeHtml(error.message) + '</td></tr>';
    }
}

/**
 * Render results table
 */
function renderResults(items) {
    if (items.length === 0) {
        resultsBody.innerHTML = '<tr><td colspan="6" class="empty-state">No results found</td></tr>';
        return;
    }

    let html = '';
    for (const item of items) {
        const statusClass = getItemStatusClass(item.status);
        const title = item.scraped_title || item.input_asin;
        const truncatedTitle = title.length > 60 ? title.substring(0, 60) + '...' : title;

        html += '<tr>' +
            '<td>' +
                '<div class="product-cell">' +
                    '<div class="product-info">' +
                        '<div class="product-title" title="' + escapeHtml(title) + '">' + escapeHtml(truncatedTitle) + '</div>' +
                        (item.channel_sku_code ? '<div class="product-sku">' + escapeHtml(item.channel_sku_code) + '</div>' : '') +
                    '</div>' +
                '</div>' +
            '</td>' +
            '<td><a href="https://www.amazon.' + scanData.marketplace + '/dp/' + item.input_asin + '" target="_blank" class="link">' + item.input_asin + '</a></td>' +
            '<td><span class="status-badge ' + statusClass + '">' + formatStatus(item.status) + '</span></td>' +
            '<td>' + (item.scraped_rating ? renderStars(parseFloat(item.scraped_rating)) : '-') + '</td>' +
            '<td>' + (item.scraped_review_count !== null ? formatNumber(item.scraped_review_count) : '-') + '</td>' +
            '<td>-</td>' +
        '</tr>';
    }

    resultsBody.innerHTML = html;
}

/**
 * Render star rating
 */
function renderStars(rating) {
    // Convert to number in case it's a string from JSON serialization
    const numRating = parseFloat(rating);
    const fullStars = Math.floor(numRating);
    const hasHalf = numRating % 1 >= 0.5;
    let html = '<span class="star-rating" title="' + numRating.toFixed(1) + '">';

    for (let i = 0; i < 5; i++) {
        if (i < fullStars) {
            html += '<span class="star full">★</span>';
        } else if (i === fullStars && hasHalf) {
            html += '<span class="star half">★</span>';
        } else {
            html += '<span class="star empty">☆</span>';
        }
    }

    html += ' <span class="rating-value">' + numRating.toFixed(1) + '</span></span>';
    return html;
}

/**
 * Render pagination
 */
function renderPagination() {
    if (totalPages <= 1) {
        paginationContainer.innerHTML = '';
        return;
    }

    let html = '<div class="pagination">';

    // Previous button
    html += '<button class="btn btn-secondary btn-sm" ' + (currentPage === 1 ? 'disabled' : '') + ' onclick="goToPage(' + (currentPage - 1) + ')">&laquo; Prev</button>';

    // Page numbers
    const maxVisible = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
    let endPage = Math.min(totalPages, startPage + maxVisible - 1);

    if (endPage - startPage + 1 < maxVisible) {
        startPage = Math.max(1, endPage - maxVisible + 1);
    }

    if (startPage > 1) {
        html += '<button class="btn btn-secondary btn-sm" onclick="goToPage(1)">1</button>';
        if (startPage > 2) html += '<span class="pagination-ellipsis">...</span>';
    }

    for (let i = startPage; i <= endPage; i++) {
        html += '<button class="btn btn-' + (i === currentPage ? 'primary' : 'secondary') + ' btn-sm" onclick="goToPage(' + i + ')">' + i + '</button>';
    }

    if (endPage < totalPages) {
        if (endPage < totalPages - 1) html += '<span class="pagination-ellipsis">...</span>';
        html += '<button class="btn btn-secondary btn-sm" onclick="goToPage(' + totalPages + ')">' + totalPages + '</button>';
    }

    // Next button
    html += '<button class="btn btn-secondary btn-sm" ' + (currentPage === totalPages ? 'disabled' : '') + ' onclick="goToPage(' + (currentPage + 1) + ')">Next &raquo;</button>';

    html += '</div>';
    paginationContainer.innerHTML = html;
}

/**
 * Go to page
 */
function goToPage(page) {
    currentPage = page;
    loadResults();
}

/**
 * Start auto-refresh for running scans
 */
function startAutoRefresh() {
    refreshInterval = setInterval(async () => {
        await loadScan();
        loadResults();

        if (scanData.status !== 'running' && scanData.status !== 'queued') {
            stopAutoRefresh();
        }
    }, 5000);
}

/**
 * Stop auto-refresh
 */
function stopAutoRefresh() {
    if (refreshInterval) {
        clearInterval(refreshInterval);
        refreshInterval = null;
    }
}

/**
 * Cancel scan
 */
async function cancelScan() {
    if (!confirm('Are you sure you want to cancel this scan?')) return;

    try {
        await api.cancelProductScan(scanId);
        showAlert('Scan cancelled', 'success');
        stopAutoRefresh();
        await loadScan();
        loadResults();
    } catch (error) {
        showAlert('Failed to cancel: ' + error.message, 'error');
    }
}

/**
 * Retry failed items
 */
async function retryFailed() {
    try {
        await api.retryFailedProductScanItems(scanId);
        showAlert('Retrying failed items...', 'success');
        await loadScan();
        loadResults();
        if (scanData.status === 'running') {
            startAutoRefresh();
        }
    } catch (error) {
        showAlert('Failed to retry: ' + error.message, 'error');
    }
}

/**
 * Get status badge class for scan
 */
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

/**
 * Get status badge class for item
 */
function getItemStatusClass(status) {
    const classes = {
        pending: 'pending',
        completed: 'completed',
        failed: 'failed'
    };
    return classes[status] || 'pending';
}

/**
 * Format status for display
 */
function formatStatus(status) {
    return status.charAt(0).toUpperCase() + status.slice(1);
}

/**
 * Format marketplace code for display
 */
function formatMarketplace(code) {
    const markets = {
        'com': 'Amazon.com (US)',
        'co.uk': 'Amazon.co.uk (UK)',
        'de': 'Amazon.de (Germany)',
        'fr': 'Amazon.fr (France)',
        'it': 'Amazon.it (Italy)',
        'es': 'Amazon.es (Spain)',
        'ca': 'Amazon.ca (Canada)',
        'com.au': 'Amazon.com.au (Australia)'
    };
    return markets[code] || 'Amazon.' + code;
}

/**
 * Format date for display
 */
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

/**
 * Format number with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Format price
 */
function formatPrice(price, currency) {
    const symbols = {
        'USD': '$',
        'GBP': '£',
        'EUR': '€',
        'CAD': 'C$',
        'AUD': 'A$'
    };
    const symbol = symbols[currency] || currency + ' ';
    return symbol + price.toFixed(2);
}

/**
 * Show alert message
 */
function showAlert(message, type) {
    const alertClass = type === 'error' ? 'alert-error' : 'alert-success';
    alertContainer.innerHTML = '<div class="alert ' + alertClass + '">' + escapeHtml(message) + '</div>';

    setTimeout(() => {
        alertContainer.innerHTML = '';
    }, 5000);
}

/**
 * Escape HTML special characters
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
