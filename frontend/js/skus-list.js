/**
 * =============================================================================
 * Parent SKUs List Page
 * =============================================================================
 * Purpose: Display parent SKUs with aggregated Channel SKU metrics
 * =============================================================================
 */

// State
let currentPage = 1;
const pageSize = 20;
let totalPages = 1;

// DOM Elements
const skusBody = document.getElementById('skus-body');
const searchInput = document.getElementById('search-input');
const paginationContainer = document.getElementById('pagination-container');
const alertContainer = document.getElementById('alert-container');

/**
 * Initialize page
 */
async function init() {
    // Load SKUs
    loadSkus();

    // Set up event listeners
    searchInput.addEventListener('input', debounce(() => {
        currentPage = 1;
        loadSkus();
    }, 300));
}

/**
 * Load SKUs with channel SKU stats
 */
async function loadSkus() {
    const search = searchInput.value.trim() || null;

    try {
        const result = await api.listSkusWithChannelSkuStats(currentPage, pageSize, search);
        renderSkus(result.items || []);
        totalPages = result.total_pages || 1;
        renderPagination();
        updateStats(result.items || []);
    } catch (error) {
        skusBody.innerHTML = '<tr><td colspan="6" class="empty-state">Failed to load SKUs: ' + escapeHtml(error.message) + '</td></tr>';
    }
}

/**
 * Update stats from loaded data
 */
function updateStats(items) {
    // Calculate totals from current page (ideally should come from API)
    let totalChannelSkus = 0;
    let totalRatings = 0;
    let ratingCount = 0;

    for (const item of items) {
        totalChannelSkus += item.channel_sku_count || 0;
        if (item.avg_rating) {
            totalRatings += parseFloat(item.avg_rating);
            ratingCount++;
        }
    }

    document.getElementById('stat-total-skus').textContent = items.length;
    document.getElementById('stat-total-channel-skus').textContent = totalChannelSkus;
    document.getElementById('stat-avg-rating').textContent = ratingCount > 0
        ? (totalRatings / ratingCount).toFixed(1)
        : '-';
}

/**
 * Render SKUs table
 */
function renderSkus(skus) {
    if (skus.length === 0) {
        skusBody.innerHTML = '<tr><td colspan="6" class="empty-state">No SKUs found. Create scans with SKU codes to populate this list.</td></tr>';
        return;
    }

    let html = '';
    for (const sku of skus) {
        const avgRating = sku.avg_rating ? parseFloat(sku.avg_rating).toFixed(1) : '-';
        const totalReviews = sku.total_reviews ? formatNumber(sku.total_reviews) : '-';
        const lastScraped = sku.last_scraped_at ? formatDate(sku.last_scraped_at) : 'Never';

        html += '<tr class="clickable-row" onclick="viewSkuDetail(\'' + escapeHtml(sku.sku_code) + '\')">' +
            '<td>' +
                '<strong>' + escapeHtml(sku.sku_code) + '</strong>' +
            '</td>' +
            '<td>' +
                '<span class="badge badge-info">' + (sku.channel_sku_count || 0) + '</span>' +
            '</td>' +
            '<td>' + (sku.avg_rating ? renderStars(avgRating) : '-') + '</td>' +
            '<td>' + totalReviews + '</td>' +
            '<td>' + lastScraped + '</td>' +
            '<td>' +
                '<button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); viewSkuDetail(\'' + escapeHtml(sku.sku_code) + '\')" title="View Channel SKUs">' +
                    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>' +
                    ' View' +
                '</button>' +
            '</td>' +
        '</tr>';
    }

    skusBody.innerHTML = html;
}

/**
 * Render star rating
 */
function renderStars(rating) {
    const numRating = parseFloat(rating);
    const fullStars = Math.floor(numRating);
    const hasHalf = numRating % 1 >= 0.5;
    let html = '<span class="star-rating" title="' + numRating.toFixed(1) + '">';

    for (let i = 0; i < 5; i++) {
        if (i < fullStars) {
            html += '<span class="star full">&#9733;</span>';
        } else if (i === fullStars && hasHalf) {
            html += '<span class="star half">&#9733;</span>';
        } else {
            html += '<span class="star empty">&#9734;</span>';
        }
    }

    html += ' <span class="rating-value">' + numRating.toFixed(1) + '</span></span>';
    return html;
}

/**
 * Navigate to SKU detail page
 */
function viewSkuDetail(skuCode) {
    window.location.href = 'sku-detail.html?sku=' + encodeURIComponent(skuCode);
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
    loadSkus();
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
