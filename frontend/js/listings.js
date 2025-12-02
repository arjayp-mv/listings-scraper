/**
 * =============================================================================
 * All Listings Page
 * =============================================================================
 * Purpose: Manage saved channel SKU listings
 * =============================================================================
 */

// State
let currentPage = 1;
let pageSize = 20;
let totalPages = 1;
let totalItems = 0;
let editingId = null;

// DOM Elements
const listingsBody = document.getElementById('listings-body');
const searchInput = document.getElementById('search-input');
const skuFilter = document.getElementById('sku-filter');
const marketplaceFilter = document.getElementById('marketplace-filter');
const ratingFilter = document.getElementById('rating-filter');
const clearFiltersBtn = document.getElementById('clear-filters-btn');
const paginationContainer = document.getElementById('pagination-container');
const alertContainer = document.getElementById('alert-container');
const modal = document.getElementById('modal');
const importModal = document.getElementById('import-modal');

/**
 * Initialize page
 */
async function init() {
    // Set export link
    document.getElementById('export-link').href = api.exportChannelSkusCsv();

    // Load stats
    loadStats();

    // Load listings
    loadListings();

    // Set up event listeners
    searchInput.addEventListener('input', debounce(() => {
        currentPage = 1;
        loadListings();
    }, 300));

    skuFilter.addEventListener('input', debounce(() => {
        currentPage = 1;
        loadListings();
    }, 300));

    marketplaceFilter.addEventListener('change', () => {
        currentPage = 1;
        loadListings();
    });

    ratingFilter.addEventListener('change', () => {
        currentPage = 1;
        loadListings();
    });

    clearFiltersBtn.addEventListener('click', () => {
        searchInput.value = '';
        skuFilter.value = '';
        marketplaceFilter.value = '';
        ratingFilter.value = '';
        currentPage = 1;
        loadListings();
    });

    document.getElementById('add-btn').addEventListener('click', openAddModal);
    document.getElementById('import-btn').addEventListener('click', openImportModal);
    document.getElementById('listing-form').addEventListener('submit', handleFormSubmit);
    document.getElementById('import-form').addEventListener('submit', handleImportSubmit);
}

/**
 * Load listing statistics
 */
async function loadStats() {
    try {
        const stats = await api.getChannelSkuStats();
        const byMarketplace = stats.by_marketplace || {};
        const usCount = byMarketplace['com'] || 0;
        const total = stats.total || 0;
        const otherCount = total - usCount;

        document.getElementById('stat-total').textContent = total;
        document.getElementById('stat-us').textContent = usCount;
        document.getElementById('stat-other').textContent = otherCount;
        document.getElementById('stat-scanned').textContent = stats.scanned_today || 0;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

/**
 * Load channel SKU listings
 */
async function loadListings() {
    const search = searchInput.value.trim() || null;
    const skuCode = skuFilter.value.trim() || null;
    const marketplace = marketplaceFilter.value || null;
    const minRating = ratingFilter.value ? parseFloat(ratingFilter.value) : null;

    try {
        const result = await api.listChannelSkus(currentPage, pageSize, search, marketplace, skuCode, minRating, null);
        renderListings(result.items || []);
        totalPages = result.total_pages || 1;
        totalItems = result.total || 0;
        renderPagination();
    } catch (error) {
        listingsBody.innerHTML = '<tr><td colspan="8" class="empty-state">Failed to load listings: ' + escapeHtml(error.message) + '</td></tr>';
    }
}

/**
 * Render listings table
 */
function renderListings(listings) {
    if (listings.length === 0) {
        listingsBody.innerHTML = '<tr><td colspan="9" class="empty-state">No listings found. Add some listings to get started.</td></tr>';
        return;
    }

    let html = '';
    for (const listing of listings) {
        const title = listing.product_title || '-';
        const truncatedTitle = title.length > 40 ? title.substring(0, 40) + '...' : title;
        const parentSku = listing.sku_code || '-';

        html += '<tr>' +
            '<td>' +
                '<div class="product-cell">' +
                    '<div class="product-info">' +
                        '<div class="product-title" title="' + escapeHtml(title) + '">' + escapeHtml(truncatedTitle) + '</div>' +
                    '</div>' +
                '</div>' +
            '</td>' +
            '<td><a href="https://www.amazon.' + listing.marketplace + '/dp/' + listing.current_asin + '" target="_blank" class="link">' + listing.current_asin + '</a></td>' +
            '<td>' + (listing.channel_sku_code ? escapeHtml(listing.channel_sku_code) : '-') + '</td>' +
            '<td>' + escapeHtml(parentSku) + '</td>' +
            '<td>' + formatMarketplace(listing.marketplace) + '</td>' +
            '<td>' + (listing.latest_rating ? renderStars(listing.latest_rating) : '-') + '</td>' +
            '<td>' + (listing.latest_review_count !== null ? formatNumber(listing.latest_review_count) : '-') + '</td>' +
            '<td>' + (listing.last_scraped_at ? formatDate(listing.last_scraped_at) : 'Never') + '</td>' +
            '<td>' +
                '<div class="flex gap-1">' +
                    '<button class="btn btn-secondary btn-sm" onclick="viewHistory(' + listing.id + ')" title="View History">' +
                        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>' +
                    '</button>' +
                    '<button class="btn btn-danger btn-sm" onclick="deleteListing(' + listing.id + ')" title="Delete">' +
                        '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>' +
                    '</button>' +
                '</div>' +
            '</td>' +
        '</tr>';
    }

    listingsBody.innerHTML = html;
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
    if (totalItems === 0) {
        paginationContainer.innerHTML = '';
        return;
    }

    // Calculate showing range
    const startItem = (currentPage - 1) * pageSize + 1;
    const endItem = Math.min(currentPage * pageSize, totalItems);

    let html = '<div class="pagination-wrapper">';

    // Left side: Showing X-Y of Z
    html += '<div class="pagination-info">Showing <strong>' + startItem + '-' + endItem + '</strong> of <strong>' + formatNumber(totalItems) + '</strong></div>';

    // Center: Page numbers (only if more than 1 page)
    if (totalPages > 1) {
        html += '<div class="pagination">';

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
    }

    // Right side: Page size selector
    html += '<div class="pagination-size">';
    html += '<label>Per page: </label>';
    html += '<select onchange="changePageSize(this.value)">';
    html += '<option value="20"' + (pageSize === 20 ? ' selected' : '') + '>20</option>';
    html += '<option value="50"' + (pageSize === 50 ? ' selected' : '') + '>50</option>';
    html += '<option value="100"' + (pageSize === 100 ? ' selected' : '') + '>100</option>';
    html += '</select>';
    html += '</div>';

    html += '</div>';
    paginationContainer.innerHTML = html;
}

/**
 * Go to page
 */
function goToPage(page) {
    currentPage = page;
    loadListings();
}

/**
 * Change page size
 */
function changePageSize(size) {
    pageSize = parseInt(size);
    currentPage = 1;  // Reset to first page
    loadListings();
}

/**
 * Open add modal
 */
function openAddModal() {
    editingId = null;
    document.getElementById('modal-title').textContent = 'Add Listing';
    document.getElementById('listing-form').reset();
    modal.style.display = 'flex';
}

/**
 * Close modal
 */
function closeModal() {
    modal.style.display = 'none';
    editingId = null;
}

/**
 * Handle form submit
 */
async function handleFormSubmit(e) {
    e.preventDefault();

    const asin = document.getElementById('form-asin').value.trim().toUpperCase();
    const channelSkuCode = document.getElementById('form-channel-sku').value.trim();
    const skuCode = document.getElementById('form-sku').value.trim();

    const data = {
        current_asin: asin,
        channel_sku_code: channelSkuCode,
        sku_code: skuCode || null,  // Parent SKU code (optional)
        product_title: document.getElementById('form-title').value.trim() || null,
        marketplace: document.getElementById('form-marketplace').value
    };

    const submitBtn = document.getElementById('form-submit');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Saving...';

    try {
        await api.createChannelSku(data);
        showAlert('Listing saved successfully', 'success');
        closeModal();
        loadListings();
        loadStats();
    } catch (error) {
        showAlert('Failed to save: ' + error.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Save Listing';
    }
}

/**
 * Open import modal
 */
function openImportModal() {
    document.getElementById('import-form').reset();
    importModal.style.display = 'flex';
}

/**
 * Close import modal
 */
function closeImportModal() {
    importModal.style.display = 'none';
}

/**
 * Read file as text (helper for file upload)
 */
function readFileAsText(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve(e.target.result);
        reader.onerror = (e) => reject(new Error('Failed to read file'));
        reader.readAsText(file);
    });
}

/**
 * Handle import submit
 */
async function handleImportSubmit(e) {
    e.preventDefault();

    const marketplace = document.getElementById('import-marketplace').value;
    const fileInput = document.getElementById('import-file');

    // Get CSV data from file or textarea
    let csvData;
    if (fileInput.files.length > 0) {
        try {
            csvData = await readFileAsText(fileInput.files[0]);
        } catch (error) {
            showAlert('Failed to read file: ' + error.message, 'error');
            return;
        }
    } else {
        csvData = document.getElementById('import-data').value.trim();
    }

    if (!csvData) {
        showAlert('Please upload a CSV file or paste CSV data', 'error');
        return;
    }

    // Parse CSV - format: sku, channel_sku, asin (matches New Scan format)
    const lines = csvData.split('\n').filter(line => line.trim());
    if (lines.length < 2) {
        showAlert('Please include at least a header row and one data row', 'error');
        return;
    }

    const headers = lines[0].toLowerCase().split(',').map(h => h.trim());
    const skuIndex = headers.indexOf('sku');
    const channelSkuIndex = headers.indexOf('channel_sku');
    const asinIndex = headers.indexOf('asin');

    if (channelSkuIndex === -1) {
        showAlert('CSV must have a "channel_sku" column', 'error');
        return;
    }

    if (asinIndex === -1) {
        showAlert('CSV must have an "asin" column', 'error');
        return;
    }

    const listings = [];
    for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(',').map(v => v.trim());
        const skuCode = skuIndex !== -1 ? values[skuIndex] : null;
        const channelSkuCode = values[channelSkuIndex];
        const asin = values[asinIndex];

        if (asin && asin.match(/^[A-Z0-9]{10}$/i) && channelSkuCode) {
            listings.push({
                current_asin: asin.toUpperCase(),
                channel_sku_code: channelSkuCode,
                sku_code: skuCode || null  // Optional parent SKU
            });
        }
    }

    if (listings.length === 0) {
        showAlert('No valid listings found in CSV (need asin and channel_sku columns)', 'error');
        return;
    }

    const submitBtn = document.getElementById('import-submit');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Importing...';

    try {
        const result = await api.bulkCreateChannelSkus(listings, marketplace);
        showAlert('Imported ' + (result.created || listings.length) + ' listings', 'success');
        closeImportModal();
        loadListings();
        loadStats();
    } catch (error) {
        showAlert('Failed to import: ' + error.message, 'error');
    } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Import';
    }
}

/**
 * View history for a listing (both ASIN changes and scan metrics)
 */
async function viewHistory(id) {
    try {
        // Load both histories in parallel
        const [asinResponse, scanResponse] = await Promise.all([
            api.getChannelSkuHistory(id),
            api.getChannelSkuScanHistory(id)
        ]);

        const asinHistory = asinResponse.history || [];
        const scanHistory = scanResponse.history || [];

        if (asinHistory.length === 0 && scanHistory.length === 0) {
            showAlert('No history for this listing', 'info');
            return;
        }

        // Build message with both histories
        let message = '';

        // Scan History (rating/review changes)
        if (scanHistory.length > 0) {
            message += '=== Scan History ===\n\n';
            for (const entry of scanHistory.slice(0, 10)) {
                const rating = entry.rating ? entry.rating + ' stars' : 'N/A';
                const reviews = entry.review_count !== null ? entry.review_count + ' reviews' : 'N/A';
                const date = entry.scraped_at ? formatDate(entry.scraped_at) : 'Unknown';
                message += date + '\n';
                message += '  ' + rating + ', ' + reviews + '\n';
                message += '  Job: ' + entry.job_name + '\n\n';
            }
        }

        // ASIN History (ASIN changes)
        if (asinHistory.length > 0) {
            if (message) message += '\n';
            message += '=== ASIN History ===\n\n';
            for (const entry of asinHistory.slice(0, 10)) {
                message += formatDate(entry.changed_at) + ': ' + entry.asin + '\n';
            }
        }

        alert(message);
    } catch (error) {
        showAlert('Failed to load history: ' + error.message, 'error');
    }
}

/**
 * Delete a listing
 */
async function deleteListing(id) {
    if (!confirm('Are you sure you want to delete this listing?')) return;

    try {
        await api.deleteChannelSku(id);
        showAlert('Listing deleted', 'success');
        loadListings();
        loadStats();
    } catch (error) {
        showAlert('Failed to delete: ' + error.message, 'error');
    }
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
