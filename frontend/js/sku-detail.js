/**
 * =============================================================================
 * SKU Detail Page
 * =============================================================================
 * Purpose: Display Channel SKUs for a specific parent SKU with filtering
 * =============================================================================
 */

// State
let currentPage = 1;
const pageSize = 20;
let totalPages = 1;
let skuCode = null;

// DOM Elements
const channelSkusBody = document.getElementById('channel-skus-body');
const searchInput = document.getElementById('search-input');
const marketplaceFilter = document.getElementById('marketplace-filter');
const ratingFilter = document.getElementById('rating-filter');
const clearFiltersBtn = document.getElementById('clear-filters-btn');
const paginationContainer = document.getElementById('pagination-container');
const alertContainer = document.getElementById('alert-container');

/**
 * Initialize page
 */
async function init() {
    // Get SKU code from URL
    const urlParams = new URLSearchParams(window.location.search);
    skuCode = urlParams.get('sku');

    if (!skuCode) {
        showError('No SKU specified. Please go back and select a SKU.');
        return;
    }

    // Update page title and breadcrumb
    document.getElementById('breadcrumb-sku').textContent = skuCode;
    document.getElementById('page-title-sku').textContent = skuCode;
    document.title = skuCode + ' - Amazon Reviews Scraper';

    // Load Channel SKUs
    loadChannelSkus();

    // Set up event listeners
    searchInput.addEventListener('input', debounce(() => {
        currentPage = 1;
        loadChannelSkus();
    }, 300));

    marketplaceFilter.addEventListener('change', () => {
        currentPage = 1;
        loadChannelSkus();
    });

    ratingFilter.addEventListener('change', () => {
        currentPage = 1;
        loadChannelSkus();
    });

    clearFiltersBtn.addEventListener('click', () => {
        searchInput.value = '';
        marketplaceFilter.value = '';
        ratingFilter.value = '';
        currentPage = 1;
        loadChannelSkus();
    });
}

/**
 * Load Channel SKUs for this parent SKU
 */
async function loadChannelSkus() {
    const search = searchInput.value.trim() || null;
    const marketplace = marketplaceFilter.value || null;
    const minRating = ratingFilter.value ? parseFloat(ratingFilter.value) : null;

    try {
        const result = await api.listChannelSkus(currentPage, pageSize, search, marketplace, skuCode, minRating, null);
        renderChannelSkus(result.items || []);
        totalPages = result.total_pages || 1;
        renderPagination();
        updateStats(result.items || [], result.total || 0);
    } catch (error) {
        channelSkusBody.innerHTML = '<tr><td colspan="8" class="empty-state">Failed to load Channel SKUs: ' + escapeHtml(error.message) + '</td></tr>';
    }
}

/**
 * Update stats from loaded data
 */
function updateStats(items, total) {
    // Calculate stats from current page (ideally should come from API)
    let totalReviews = 0;
    let totalRatings = 0;
    let ratingCount = 0;
    const marketplaces = new Set();

    for (const item of items) {
        if (item.latest_review_count) {
            totalReviews += item.latest_review_count;
        }
        if (item.latest_rating) {
            totalRatings += parseFloat(item.latest_rating);
            ratingCount++;
        }
        if (item.marketplace) {
            marketplaces.add(item.marketplace);
        }
    }

    document.getElementById('stat-total-channel-skus').textContent = total;
    document.getElementById('stat-avg-rating').textContent = ratingCount > 0
        ? (totalRatings / ratingCount).toFixed(1)
        : '-';
    document.getElementById('stat-total-reviews').textContent = formatNumber(totalReviews);
    document.getElementById('stat-marketplaces').textContent = marketplaces.size || '-';
}

/**
 * Render Channel SKUs table
 */
function renderChannelSkus(channelSkus) {
    if (channelSkus.length === 0) {
        channelSkusBody.innerHTML = '<tr><td colspan="8" class="empty-state">No Channel SKUs found for this parent SKU.</td></tr>';
        return;
    }

    let html = '';
    for (const item of channelSkus) {
        const title = item.product_title || '-';
        const truncatedTitle = title.length > 30 ? title.substring(0, 30) + '...' : title;

        html += '<tr>' +
            '<td><strong>' + escapeHtml(item.channel_sku_code || '-') + '</strong></td>' +
            '<td><a href="https://www.amazon.' + item.marketplace + '/dp/' + item.current_asin + '" target="_blank" class="link">' + item.current_asin + '</a></td>' +
            '<td title="' + escapeHtml(title) + '">' + escapeHtml(truncatedTitle) + '</td>' +
            '<td>' + formatMarketplace(item.marketplace) + '</td>' +
            '<td>' + (item.latest_rating ? renderStars(item.latest_rating) : '-') + '</td>' +
            '<td>' + (item.latest_review_count !== null ? formatNumber(item.latest_review_count) : '-') + '</td>' +
            '<td>' + (item.last_scraped_at ? formatDate(item.last_scraped_at) : 'Never') + '</td>' +
            '<td>' +
                '<div class="flex gap-1">' +
                    '<button class="btn btn-secondary btn-sm" onclick="viewHistory(' + item.id + ')" title="View History">' +
                        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>' +
                    '</button>' +
                '</div>' +
            '</td>' +
        '</tr>';
    }

    channelSkusBody.innerHTML = html;
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
 * View history for a Channel SKU
 */
async function viewHistory(id) {
    try {
        const response = await api.getChannelSkuHistory(id);
        const history = response.history || [];

        if (history.length === 0) {
            showAlert('No ASIN history for this Channel SKU', 'info');
            return;
        }

        // Show history in alert for now (could be a modal)
        let message = 'ASIN History:\n';
        for (const entry of history.slice(0, 10)) {
            message += formatDate(entry.changed_at) + ': ' + entry.asin + '\n';
        }
        alert(message);
    } catch (error) {
        showAlert('Failed to load history: ' + error.message, 'error');
    }
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
    loadChannelSkus();
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
 * Format number with commas
 */
function formatNumber(num) {
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Show error message
 */
function showError(message) {
    channelSkusBody.innerHTML = '<tr><td colspan="8" class="empty-state">' + escapeHtml(message) + '</td></tr>';
    document.getElementById('stats-container').style.display = 'none';
    document.querySelector('.card.mb-3').style.display = 'none';
}

/**
 * Show alert message
 */
function showAlert(message, type) {
    const alertClass = type === 'error' ? 'alert-error' : (type === 'info' ? 'alert-info' : 'alert-success');
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
