/**
 * =============================================================================
 * New Product Scan Page
 * =============================================================================
 * Purpose: Handle form submission for creating product scan jobs
 * =============================================================================
 */

// State
let currentMode = 'manual';
let savedListings = [];
let selectedListingIds = new Set();
let filteredListings = [];

// DOM Elements
const manualForm = document.getElementById('manual-form');
const savedForm = document.getElementById('saved-form');
const listingsInput = document.getElementById('listings-input');
const listingsFileInput = document.getElementById('listings-file');
const listingCountSpan = document.getElementById('listing-count');
const listingsContainer = document.getElementById('listings-container');
const selectedCountSpan = document.getElementById('selected-count');
const searchInput = document.getElementById('listing-search');
const alertContainer = document.getElementById('alert-container');

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
 * Initialize page
 */
async function init() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchMode(btn.dataset.mode));
    });

    // Listing counting
    listingsInput.addEventListener('input', updateListingCount);

    // File upload handling
    listingsFileInput.addEventListener('change', handleFileUpload);

    // Form submissions
    manualForm.addEventListener('submit', handleManualSubmit);
    savedForm.addEventListener('submit', handleSavedSubmit);

    // Select/deselect all
    document.getElementById('select-all-btn').addEventListener('click', selectAllListings);
    document.getElementById('deselect-all-btn').addEventListener('click', deselectAllListings);

    // Search
    searchInput.addEventListener('input', debounce(filterListings, 300));

    // Load saved listings for the saved mode
    await loadSavedListings();
}

/**
 * Handle file upload and populate textarea
 */
async function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    try {
        const content = await readFileAsText(file);
        listingsInput.value = content;
        updateListingCount();
    } catch (error) {
        showAlert('Failed to read file: ' + error.message, 'error');
    }
}

/**
 * Switch between manual and saved modes
 */
function switchMode(mode) {
    currentMode = mode;

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.mode === mode);
    });

    manualForm.style.display = mode === 'manual' ? 'block' : 'none';
    savedForm.style.display = mode === 'saved' ? 'block' : 'none';
}

/**
 * Update listing count display
 */
function updateListingCount() {
    const listings = parseListings(listingsInput.value);
    listingCountSpan.textContent = listings.length;
}

/**
 * Parse listings from textarea (3-column format: SKU, Channel SKU, ASIN)
 * Supports both tab and comma separated values
 */
function parseListings(text) {
    const lines = text.split('\n').map(line => line.trim()).filter(line => line.length > 0);
    const listings = [];

    for (const line of lines) {
        // Split by tab first, then by comma if no tabs found
        let parts = line.split('\t');
        if (parts.length < 3) {
            parts = line.split(',').map(p => p.trim());
        }

        if (parts.length >= 3) {
            const sku = parts[0].trim();
            const channelSku = parts[1].trim();
            const asin = parts[2].trim().toUpperCase();

            // Validate ASIN format (10 characters, alphanumeric starting with B usually)
            if (asin.length === 10 && /^[A-Z0-9]+$/.test(asin)) {
                listings.push({
                    sku_code: sku,
                    channel_sku_code: channelSku,
                    asin: asin
                });
            }
        }
    }

    return listings;
}

/**
 * Handle manual form submission
 */
async function handleManualSubmit(e) {
    e.preventDefault();

    const jobName = document.getElementById('job-name').value.trim();
    const marketplace = document.getElementById('marketplace').value;
    const saveListings = document.getElementById('save-listings').checked;
    const listings = parseListings(listingsInput.value);

    if (listings.length === 0) {
        showAlert('Please enter at least one valid listing (SKU, Channel SKU, ASIN format)', 'error');
        return;
    }

    const submitBtn = document.getElementById('submit-btn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<div class="spinner"></div> Creating scan...';

    try {
        // Create the product scan
        // The backend will auto-create parent SKUs and Channel SKUs if needed
        const data = {
            job_name: jobName,
            marketplace: marketplace,
            listings: listings  // Already in {sku_code, channel_sku_code, asin} format
        };

        const result = await api.createProductScan(data);

        showAlert('Scan created successfully! Redirecting...', 'success');
        setTimeout(() => {
            window.location.href = 'scan-detail.html?id=' + result.id;
        }, 1000);
    } catch (error) {
        showAlert('Error: ' + error.message, 'error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Start Scan';
    }
}

/**
 * Load saved channel SKU listings
 */
async function loadSavedListings() {
    try {
        // Load all listings using pagination (max 50 per page)
        savedListings = [];
        let page = 1;
        let hasMore = true;

        while (hasMore) {
            const result = await api.listChannelSkus(page, 50);
            savedListings = savedListings.concat(result.items || []);
            hasMore = result.has_next;
            page++;

            // Safety limit to prevent infinite loops
            if (page > 20) break;
        }

        filteredListings = savedListings;
        renderListings();
    } catch (error) {
        listingsContainer.innerHTML = '<div class="empty-state">Failed to load listings: ' + error.message + '</div>';
    }
}

/**
 * Render listings in the select container
 */
function renderListings() {
    if (filteredListings.length === 0) {
        listingsContainer.innerHTML = '<div class="empty-state">No saved listings found. Add listings using the manual entry mode first.</div>';
        return;
    }

    let html = '';
    for (const listing of filteredListings) {
        const isSelected = selectedListingIds.has(listing.id);
        const title = listing.product_title || listing.current_asin;
        const displaySku = listing.channel_sku_code ? ' (' + listing.channel_sku_code + ')' : '';

        html += '<label class="listing-select-item' + (isSelected ? ' selected' : '') + '" data-id="' + listing.id + '">' +
            '<input type="checkbox" ' + (isSelected ? 'checked' : '') + '>' +
            '<div class="listing-info">' +
                '<div class="listing-title">' + escapeHtml(title) + displaySku + '</div>' +
                '<div class="listing-asin">' + listing.current_asin + ' - ' + listing.marketplace + '</div>' +
            '</div>' +
        '</label>';
    }

    listingsContainer.innerHTML = html;

    // Add event listeners
    listingsContainer.querySelectorAll('.listing-select-item').forEach(item => {
        item.addEventListener('click', (e) => {
            if (e.target.tagName === 'INPUT') return; // Let checkbox handle itself
            const checkbox = item.querySelector('input');
            checkbox.checked = !checkbox.checked;
            toggleListing(parseInt(item.dataset.id), checkbox.checked);
        });

        item.querySelector('input').addEventListener('change', (e) => {
            toggleListing(parseInt(item.dataset.id), e.target.checked);
        });
    });
}

/**
 * Toggle listing selection
 */
function toggleListing(id, selected) {
    const item = listingsContainer.querySelector('[data-id="' + id + '"]');

    if (selected) {
        selectedListingIds.add(id);
        item.classList.add('selected');
    } else {
        selectedListingIds.delete(id);
        item.classList.remove('selected');
    }

    updateSelectedCount();
}

/**
 * Update selected count display
 */
function updateSelectedCount() {
    selectedCountSpan.textContent = selectedListingIds.size;
}

/**
 * Select all visible listings
 */
function selectAllListings() {
    filteredListings.forEach(listing => {
        selectedListingIds.add(listing.id);
    });
    renderListings();
    updateSelectedCount();
}

/**
 * Deselect all listings
 */
function deselectAllListings() {
    selectedListingIds.clear();
    renderListings();
    updateSelectedCount();
}

/**
 * Filter listings by search term
 */
function filterListings() {
    const search = searchInput.value.toLowerCase().trim();

    if (!search) {
        filteredListings = savedListings;
    } else {
        filteredListings = savedListings.filter(listing => {
            const title = (listing.product_title || '').toLowerCase();
            const sku = (listing.channel_sku_code || '').toLowerCase();
            const asin = listing.current_asin.toLowerCase();
            return title.includes(search) || sku.includes(search) || asin.includes(search);
        });
    }

    renderListings();
}

/**
 * Handle saved listings form submission
 */
async function handleSavedSubmit(e) {
    e.preventDefault();

    const jobName = document.getElementById('saved-job-name').value.trim();
    const marketplace = document.getElementById('saved-marketplace').value;

    if (selectedListingIds.size === 0) {
        showAlert('Please select at least one listing', 'error');
        return;
    }

    const submitBtn = document.getElementById('saved-submit-btn');
    submitBtn.disabled = true;
    submitBtn.innerHTML = '<div class="spinner"></div> Creating scan...';

    try {
        const channelSkuIds = Array.from(selectedListingIds);
        const result = await api.createProductScanFromChannelSkus(jobName, marketplace, channelSkuIds);

        showAlert('Scan created successfully! Redirecting...', 'success');
        setTimeout(() => {
            window.location.href = 'scan-detail.html?id=' + result.id;
        }, 1000);
    } catch (error) {
        showAlert('Error: ' + error.message, 'error');
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg> Start Scan';
    }
}

/**
 * Show alert message
 */
function showAlert(message, type) {
    const alertClass = type === 'error' ? 'alert-error' : 'alert-success';
    alertContainer.innerHTML = '<div class="alert ' + alertClass + '">' + escapeHtml(message) + '</div>';

    if (type === 'success') {
        setTimeout(() => {
            alertContainer.innerHTML = '';
        }, 5000);
    }
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
