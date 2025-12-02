/**
 * =============================================================================
 * Amazon Reviews Scraper - SKU Reviews Page
 * =============================================================================
 */

let skuId = null;
let skuData = null;
let currentPage = 1;
let pageSize = 20;
let totalPages = 1;
let totalItems = 0;
let searchTimeout = null;

document.addEventListener('DOMContentLoaded', () => {
    // Get SKU ID from URL
    const params = new URLSearchParams(window.location.search);
    skuId = params.get('id');

    if (!skuId) {
        showAlert('error', 'No SKU ID provided');
        return;
    }

    loadSkuData();
    loadStats();
    loadReviews();
    setupEventListeners();
});

function setupEventListeners() {
    // Search input
    document.getElementById('search-input').addEventListener('input', () => {
        if (searchTimeout) clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            currentPage = 1;
            loadReviews();
        }, 300);
    });

    // Rating filter
    document.getElementById('rating-filter').addEventListener('change', () => {
        currentPage = 1;
        loadReviews();
    });

    // Clear filters
    document.getElementById('clear-filters-btn').addEventListener('click', () => {
        document.getElementById('search-input').value = '';
        document.getElementById('rating-filter').value = '';
        currentPage = 1;
        loadReviews();
    });

    // Copy button
    document.getElementById('copy-btn').addEventListener('click', copyAllReviews);
}

async function loadSkuData() {
    try {
        skuData = await api.getSku(skuId);
        document.getElementById('breadcrumb-sku').textContent = skuData.sku_code;
        document.getElementById('page-title-sku').textContent = skuData.sku_code;
        document.title = skuData.sku_code + ' Reviews - Amazon Reviews Scraper';

        // Set export URL
        document.getElementById('export-excel-btn').href = api.getSkuExcelExportUrl(skuId);
    } catch (error) {
        showAlert('error', 'Failed to load SKU: ' + error.message);
    }
}

async function loadStats() {
    try {
        const stats = await api.getSkuReviewStats(skuId);
        document.getElementById('stat-total').textContent = formatNumber(stats.total_reviews);
        document.getElementById('stat-avg').textContent = stats.average_rating ? stats.average_rating.toFixed(1) : '-';
        document.getElementById('stat-5star').textContent = formatNumber(stats.five_star);
        document.getElementById('stat-verified').textContent = formatNumber(stats.verified_count);
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function loadReviews() {
    const container = document.getElementById('reviews-container');
    const search = document.getElementById('search-input').value.trim() || null;
    const rating = document.getElementById('rating-filter').value || null;

    container.innerHTML = '<div class="loading"><div class="spinner"></div> Loading reviews...</div>';

    try {
        const result = await api.listSkuReviews(skuId, currentPage, pageSize, search, rating);
        totalPages = result.total_pages || 1;
        totalItems = result.total || 0;
        renderReviews(result.items || []);
        renderPagination();
    } catch (error) {
        container.innerHTML = '<div class="text-danger">Failed to load reviews: ' + escapeHtml(error.message) + '</div>';
    }
}

function renderReviews(reviews) {
    const container = document.getElementById('reviews-container');

    if (!reviews || reviews.length === 0) {
        container.innerHTML = '<div class="empty-state">No reviews found for this SKU.</div>';
        return;
    }

    container.innerHTML = reviews.map(review => `
        <div class="review-item" style="border-bottom: 1px solid var(--border-color); padding: 16px 0;">
            <div class="flex justify-between align-center mb-2">
                <div class="flex gap-2 align-center">
                    <span class="badge ${getRatingBadgeClass(review.rating)}">${review.rating || '-'}</span>
                    <span class="text-muted">${review.asin}</span>
                    ${review.verified ? '<span class="badge badge-success">Verified</span>' : ''}
                </div>
                <span class="text-muted text-sm">${review.date || ''}</span>
            </div>
            <h4 style="margin: 0 0 8px 0; font-weight: 500;">${escapeHtml(review.title || 'No title')}</h4>
            <p style="margin: 0; color: var(--text-secondary); line-height: 1.6;">${escapeHtml(review.text || 'No review text')}</p>
            <div class="text-muted text-sm mt-2">
                By ${escapeHtml(review.user_name || 'Anonymous')}
                ${review.helpful_count > 0 ? ' • ' + review.helpful_count + ' found helpful' : ''}
            </div>
        </div>
    `).join('');
}

function getRatingBadgeClass(rating) {
    if (!rating) return 'badge-secondary';
    const num = parseFloat(rating);
    if (num >= 4) return 'badge-success';
    if (num >= 3) return 'badge-warning';
    return 'badge-danger';
}

function renderPagination() {
    const container = document.getElementById('pagination-container');

    if (totalItems === 0) {
        container.innerHTML = '';
        return;
    }

    const startItem = (currentPage - 1) * pageSize + 1;
    const endItem = Math.min(currentPage * pageSize, totalItems);

    let html = '<div class="pagination-wrapper">';
    html += '<div class="pagination-info">Showing <strong>' + startItem + '-' + endItem + '</strong> of <strong>' + formatNumber(totalItems) + '</strong></div>';

    if (totalPages > 1) {
        html += '<div class="pagination">';
        html += '<button class="pagination-btn" onclick="goToPage(' + (currentPage - 1) + ')" ' + (currentPage === 1 ? 'disabled' : '') + '>Prev</button>';

        const maxVisible = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxVisible / 2));
        let endPage = Math.min(totalPages, startPage + maxVisible - 1);

        if (endPage - startPage < maxVisible - 1) {
            startPage = Math.max(1, endPage - maxVisible + 1);
        }

        if (startPage > 1) {
            html += '<button class="pagination-btn" onclick="goToPage(1)">1</button>';
            if (startPage > 2) html += '<span class="pagination-ellipsis">...</span>';
        }

        for (let i = startPage; i <= endPage; i++) {
            html += '<button class="pagination-btn' + (i === currentPage ? ' active' : '') + '" onclick="goToPage(' + i + ')">' + i + '</button>';
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) html += '<span class="pagination-ellipsis">...</span>';
            html += '<button class="pagination-btn" onclick="goToPage(' + totalPages + ')">' + totalPages + '</button>';
        }

        html += '<button class="pagination-btn" onclick="goToPage(' + (currentPage + 1) + ')" ' + (currentPage === totalPages ? 'disabled' : '') + '>Next</button>';
        html += '</div>';
    }

    html += '</div>';
    container.innerHTML = html;
}

function goToPage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    loadReviews();
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

async function copyAllReviews() {
    const copyBtn = document.getElementById('copy-btn');
    const originalText = copyBtn.innerHTML;

    try {
        copyBtn.innerHTML = '<div class="spinner" style="width: 16px; height: 16px;"></div> Loading...';
        copyBtn.disabled = true;

        const search = document.getElementById('search-input').value.trim() || null;
        const rating = document.getElementById('rating-filter').value || null;

        const result = await api.getSkuFormattedReviews(skuId, search, rating);

        if (!result.formatted_text) {
            showAlert('info', 'No reviews to copy');
            return;
        }

        await navigator.clipboard.writeText(result.formatted_text);
        showAlert('success', 'Copied ' + result.total + ' reviews to clipboard!');

        copyBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg> Copied!';
        setTimeout(() => {
            copyBtn.innerHTML = originalText;
        }, 2000);

    } catch (error) {
        showAlert('error', 'Failed to copy: ' + error.message);
        copyBtn.innerHTML = originalText;
    } finally {
        copyBtn.disabled = false;
    }
}

function showAlert(type, message) {
    const container = document.getElementById('alert-container');
    container.innerHTML = `
        <div class="alert alert-${type}">
            ${escapeHtml(message)}
        </div>
    `;
    setTimeout(() => {
        container.innerHTML = '';
    }, 3000);
}

function formatNumber(num) {
    if (num === undefined || num === null) return '-';
    return num.toLocaleString();
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
