/**
 * =============================================================================
 * Scan History Page
 * =============================================================================
 * Purpose: Display list of product scans with filtering and pagination
 * =============================================================================
 */

// State
let currentPage = 1;
const pageSize = 20;
let totalPages = 1;

// DOM Elements
const scansBody = document.getElementById('scans-body');
const searchInput = document.getElementById('search-input');
const statusFilter = document.getElementById('status-filter');
const paginationContainer = document.getElementById('pagination-container');
const alertContainer = document.getElementById('alert-container');

/**
 * Initialize page
 */
async function init() {
    // Load stats
    loadStats();

    // Load scans
    loadScans();

    // Set up event listeners
    searchInput.addEventListener('input', debounce(() => {
        currentPage = 1;
        loadScans();
    }, 300));

    statusFilter.addEventListener('change', () => {
        currentPage = 1;
        loadScans();
    });

    // Auto-refresh running scans every 10 seconds
    setInterval(() => {
        const hasRunning = document.querySelector('.status-badge.running');
        if (hasRunning) {
            loadScans();
            loadStats();
        }
    }, 10000);
}

/**
 * Load scan statistics
 */
async function loadStats() {
    try {
        const stats = await api.getProductScanStats();
        const byStatus = stats.jobs_by_status || {};
        document.getElementById('stat-total').textContent = stats.total_jobs || 0;
        document.getElementById('stat-running').textContent = byStatus.running || 0;
        document.getElementById('stat-completed').textContent = byStatus.completed || 0;
        document.getElementById('stat-listings').textContent = stats.total_listings_scanned || 0;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

/**
 * Load product scans
 */
async function loadScans() {
    const search = searchInput.value.trim() || null;
    const status = statusFilter.value || null;

    try {
        const result = await api.listProductScans(currentPage, pageSize, status, search);
        renderScans(result.items || []);
        totalPages = result.total_pages || 1;
        renderPagination();
    } catch (error) {
        scansBody.innerHTML = '<tr><td colspan="7" class="empty-state">Failed to load scans: ' + escapeHtml(error.message) + '</td></tr>';
    }
}

/**
 * Render scans table
 */
function renderScans(scans) {
    if (scans.length === 0) {
        scansBody.innerHTML = '<tr><td colspan="7" class="empty-state">No scans found</td></tr>';
        return;
    }

    let html = '';
    for (const scan of scans) {
        const statusClass = getStatusClass(scan.status);
        const progress = scan.total_listings > 0
            ? Math.round((scan.completed_listings / scan.total_listings) * 100)
            : 0;

        html += '<tr>' +
            '<td><a href="scan-detail.html?id=' + scan.id + '" class="link">' + escapeHtml(scan.job_name) + '</a></td>' +
            '<td><span class="status-badge ' + statusClass + '">' + formatStatus(scan.status) + '</span></td>' +
            '<td>' +
                '<div class="progress-bar-container">' +
                    '<div class="progress-bar" style="width: ' + progress + '%"></div>' +
                '</div>' +
                '<span class="progress-text">' + scan.completed_listings + '/' + scan.total_listings + '</span>' +
            '</td>' +
            '<td>' + scan.total_listings + '</td>' +
            '<td>' + formatMarketplace(scan.marketplace) + '</td>' +
            '<td>' + formatDate(scan.created_at) + '</td>' +
            '<td>' +
                '<div class="flex gap-1">' +
                    '<a href="scan-detail.html?id=' + scan.id + '" class="btn btn-secondary btn-sm">View</a>' +
                    (scan.status === 'completed' ?
                        '<a href="' + api.getProductScanCsvUrl(scan.id) + '" class="btn btn-secondary btn-sm" title="Download CSV">' +
                            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>' +
                        '</a>' : '') +
                    (scan.status === 'running' || scan.status === 'queued' ?
                        '<button class="btn btn-danger btn-sm" onclick="cancelScan(' + scan.id + ')" title="Cancel">' +
                            '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>' +
                        '</button>' : '') +
                    '<button class="btn btn-danger btn-sm" onclick="deleteScan(' + scan.id + ')" title="Delete">' +
                        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>' +
                    '</button>' +
                '</div>' +
            '</td>' +
        '</tr>';
    }

    scansBody.innerHTML = html;
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
    loadScans();
}

/**
 * Cancel a scan
 */
async function cancelScan(id) {
    if (!confirm('Are you sure you want to cancel this scan?')) return;

    try {
        await api.cancelProductScan(id);
        showAlert('Scan cancelled', 'success');
        loadScans();
        loadStats();
    } catch (error) {
        showAlert('Failed to cancel: ' + error.message, 'error');
    }
}

/**
 * Delete a scan
 */
async function deleteScan(id) {
    if (!confirm('Are you sure you want to delete this scan? This action cannot be undone.')) return;

    try {
        await api.deleteProductScan(id);
        showAlert('Scan deleted', 'success');
        loadScans();
        loadStats();
    } catch (error) {
        showAlert('Failed to delete: ' + error.message, 'error');
    }
}

/**
 * Get status badge class
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
        'com': 'US',
        'co.uk': 'UK',
        'de': 'DE',
        'fr': 'FR',
        'it': 'IT',
        'es': 'ES',
        'ca': 'CA',
        'com.au': 'AU'
    };
    return markets[code] || code.toUpperCase();
}

/**
 * Format date for display
 */
function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
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

/**
 * Debounce function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', init);
