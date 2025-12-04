/**
 * =============================================================================
 * Amazon Reviews Scraper - Competitor Parent SKUs Page
 * =============================================================================
 */

let currentPage = 1;
const pageSize = 20;
let currentSearch = '';

document.addEventListener('DOMContentLoaded', () => {
    loadParentSkus();
    setupEventListeners();
});

function setupEventListeners() {
    const searchBtn = document.getElementById('search-btn');
    const clearBtn = document.getElementById('clear-btn');
    const searchInput = document.getElementById('search-input');

    searchBtn.addEventListener('click', () => {
        currentSearch = searchInput.value.trim();
        currentPage = 1;
        loadParentSkus();
    });

    clearBtn.addEventListener('click', () => {
        searchInput.value = '';
        currentSearch = '';
        currentPage = 1;
        loadParentSkus();
    });

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            currentSearch = searchInput.value.trim();
            currentPage = 1;
            loadParentSkus();
        }
    });

    // Add Parent SKU modal
    document.getElementById('add-sku-btn').addEventListener('click', showAddSkuModal);
    document.getElementById('close-modal').addEventListener('click', hideAddSkuModal);
    document.getElementById('cancel-modal').addEventListener('click', hideAddSkuModal);
    document.getElementById('save-sku').addEventListener('click', saveNewSku);
    document.querySelector('#add-sku-modal .modal-overlay').addEventListener('click', hideAddSkuModal);
}

function showAddSkuModal() {
    document.getElementById('add-sku-form').reset();
    document.getElementById('add-sku-modal').style.display = 'flex';
}

function hideAddSkuModal() {
    document.getElementById('add-sku-modal').style.display = 'none';
}

async function saveNewSku() {
    const skuCode = document.getElementById('sku-code').value.trim();
    const displayName = document.getElementById('display-name').value.trim() || null;

    if (!skuCode) {
        alert('SKU Code is required');
        return;
    }

    try {
        const newSku = await api.createSku({
            sku_code: skuCode,
            display_name: displayName
        });

        hideAddSkuModal();

        // Redirect to the detail page to add competitors
        window.location.href = 'competitor-parent-sku-detail.html?id=' + newSku.id;
    } catch (error) {
        console.error('Failed to create SKU:', error);
        alert('Failed to create SKU: ' + error.message);
    }
}

async function loadParentSkus() {
    const tbody = document.getElementById('skus-body');
    tbody.innerHTML = '<tr><td colspan="8" class="loading"><div class="spinner"></div> Loading...</td></tr>';

    try {
        const result = await api.listParentSkusWithCompetitorStats(currentPage, pageSize, currentSearch || null);

        renderSkus(result.items || []);
        renderPagination(result.total || 0, result.page || 1, result.per_page || pageSize);

    } catch (error) {
        console.error('Failed to load parent SKUs:', error);
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Failed to load data</td></tr>';
    }
}

function renderSkus(skus) {
    const tbody = document.getElementById('skus-body');

    if (!skus || skus.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state">No parent SKUs with competitors found</td></tr>';
        return;
    }

    let html = '';
    for (const sku of skus) {
        html += '<tr>' +
            '<td>' +
                '<a href="competitor-parent-sku-detail.html?id=' + sku.sku_id + '" class="text-link font-medium">' +
                    escapeHtml(sku.sku_code) +
                '</a>' +
            '</td>' +
            '<td>' + escapeHtml(sku.display_name || '-') + '</td>' +
            '<td>' + (sku.total_competitors || 0) + '</td>' +
            '<td>' + formatCurrency(sku.avg_competitor_price, sku.currency) + '</td>' +
            '<td>' + formatRating(sku.avg_competitor_rating) + '</td>' +
            '<td>' + (sku.total_keywords || 0) + '</td>' +
            '<td>' + formatDate(sku.last_scraped_at) + '</td>' +
            '<td>' +
                '<a href="competitor-parent-sku-detail.html?id=' + sku.sku_id + '" class="btn btn-secondary btn-sm">View</a>' +
            '</td>' +
        '</tr>';
    }
    tbody.innerHTML = html;
}

function renderPagination(total, page, size) {
    const pagination = document.getElementById('pagination');
    const totalPages = Math.ceil(total / size);

    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let html = '';

    // Previous button
    if (page > 1) {
        html += '<button class="btn btn-secondary btn-sm" onclick="goToPage(' + (page - 1) + ')">Previous</button>';
    }

    // Page info
    html += '<span class="pagination-info">Page ' + page + ' of ' + totalPages + '</span>';

    // Next button
    if (page < totalPages) {
        html += '<button class="btn btn-secondary btn-sm" onclick="goToPage(' + (page + 1) + ')">Next</button>';
    }

    pagination.innerHTML = html;
}

function goToPage(page) {
    currentPage = page;
    loadParentSkus();
}

function formatCurrency(amount, currency = 'USD') {
    if (amount === null || amount === undefined) return '-';
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency || 'USD'
    }).format(amount);
}

function formatRating(rating) {
    if (rating === null || rating === undefined) return '-';
    const num = parseFloat(rating);
    if (isNaN(num)) return '-';
    return num.toFixed(1) + ' / 5.0';
}

function formatDate(dateStr) {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    return date.toLocaleDateString();
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
