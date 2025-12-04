/**
 * =============================================================================
 * Amazon Reviews Scraper - Competitor Parent SKU Detail Page
 * =============================================================================
 */

let skuId = null;
let skuData = null;
let currentPage = 1;
const pageSize = 20;
let currentView = 'table';
let competitorsData = []; // Store loaded competitors for view switching

document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    skuId = params.get('id');

    if (!skuId) {
        alert('No SKU ID provided');
        window.location.href = 'competitor-parent-skus.html';
        return;
    }

    loadSkuData();
    setupEventListeners();
});

function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            switchTab(tab);
        });
    });

    // Export button
    document.getElementById('export-btn').addEventListener('click', () => {
        window.location.href = api.getCompetitorExportCsvUrl(skuId);
    });

    // Scrape all button
    document.getElementById('scrape-btn').addEventListener('click', () => {
        scrapeAll();
    });

    // Scrape selected button
    document.getElementById('scrape-selected-btn').addEventListener('click', scrapeSelected);

    // Add competitor form
    document.getElementById('add-competitor-form').addEventListener('submit', (e) => {
        e.preventDefault();
        addCompetitor();
    });

    // Bulk add form
    document.getElementById('bulk-add-form').addEventListener('submit', (e) => {
        e.preventDefault();
        bulkAddCompetitors();
    });

    // View toggle buttons
    document.querySelectorAll('.view-toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const view = btn.dataset.view;
            switchView(view);
        });
    });
}

function switchTab(tab) {
    // Update buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === 'tab-' + tab);
    });

    // Load data for tab
    if (tab === 'competitors') {
        loadCompetitors();
    } else if (tab === 'keywords') {
        loadKeywords();
    }
}

async function loadSkuData() {
    try {
        const [sku, stats] = await Promise.all([
            api.getSku(skuId),
            api.getCompetitorStatsBySku(skuId)
        ]);

        skuData = sku;

        // Update page header
        document.getElementById('breadcrumb-sku').textContent = sku.sku_code;
        document.getElementById('page-title').textContent = sku.display_name || sku.sku_code;
        document.getElementById('page-subtitle').textContent = 'SKU: ' + sku.sku_code;

        // Update stats
        updateStats(stats);

        // Load competitors and keywords in parallel for faster page load
        loadCompetitors();
        loadKeywords();

    } catch (error) {
        console.error('Failed to load SKU data:', error);
        alert('Failed to load SKU data');
    }
}

function updateStats(stats) {
    document.getElementById('stat-competitors').textContent = stats.total_competitors || 0;
    document.getElementById('stat-avg-price').textContent = formatCurrency(stats.avg_competitor_price, stats.currency);
    document.getElementById('stat-avg-rating').textContent = formatRating(stats.avg_competitor_rating);
    document.getElementById('stat-keywords').textContent = stats.total_keywords || 0;
}

async function refreshStats() {
    try {
        const stats = await api.getCompetitorStatsBySku(skuId);
        updateStats(stats);
    } catch (error) {
        console.error('Failed to refresh stats:', error);
    }
}

async function loadCompetitors() {
    // Show loading state for current view
    showLoadingState();

    try {
        // Pass includeData=true to get scraped data with the list
        const result = await api.listCompetitors(currentPage, pageSize, skuId, null, null, true);
        competitorsData = result.items || [];
        renderCurrentView();
        renderPagination(result.total || 0, result.page || 1, result.per_page || pageSize);
    } catch (error) {
        console.error('Failed to load competitors:', error);
        showErrorState();
    }
}

function showLoadingState() {
    const loadingHtml = '<div class="loading"><div class="spinner"></div> Loading...</div>';
    document.getElementById('competitors-body').innerHTML = '<tr><td colspan="11" class="loading"><div class="spinner"></div> Loading...</td></tr>';
    document.querySelector('#view-comparison .comparison-table-wrapper').innerHTML = loadingHtml;
    document.querySelector('#view-images .images-comparison').innerHTML = loadingHtml;
    document.querySelector('#view-content .content-comparison').innerHTML = loadingHtml;
}

function showErrorState() {
    document.getElementById('competitors-body').innerHTML = '<tr><td colspan="11" class="empty-state">Failed to load competitors</td></tr>';
    document.querySelector('#view-comparison .comparison-table-wrapper').innerHTML = '<div class="empty-state">Failed to load competitors</div>';
    document.querySelector('#view-images .images-comparison').innerHTML = '<div class="empty-state">Failed to load competitors</div>';
    document.querySelector('#view-content .content-comparison').innerHTML = '<div class="empty-state">Failed to load competitors</div>';
}

// ===== View Switching =====

function switchView(view) {
    currentView = view;

    // Update toggle button states
    document.querySelectorAll('.view-toggle-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.view === view);
    });

    // Show/hide view containers
    document.querySelectorAll('.competitor-view').forEach(v => {
        v.classList.toggle('active', v.id === 'view-' + view);
    });

    // Re-render the current view
    renderCurrentView();
}

function renderCurrentView() {
    switch (currentView) {
        case 'table':
            renderCompetitors(competitorsData);
            break;
        case 'comparison':
            renderComparisonView(competitorsData);
            break;
        case 'images':
            renderImagesView(competitorsData);
            break;
        case 'content':
            renderContentView(competitorsData);
            break;
    }
}

function renderCompetitors(competitors) {
    const tbody = document.getElementById('competitors-body');

    if (!competitors || competitors.length === 0) {
        tbody.innerHTML = '<tr><td colspan="11" class="empty-state">No competitors found. Add one using the "Add Competitor" tab.</td></tr>';
        return;
    }

    let html = '';
    for (const comp of competitors) {
        const data = comp.data || {};
        const lastScraped = data.scraped_at || null;
        html += '<tr>' +
            '<td>' +
                '<input type="checkbox" class="competitor-checkbox" ' +
                    'data-competitor-id="' + comp.id + '" ' +
                    'onchange="updateSelectedCount()">' +
            '</td>' +
            '<td>' +
                '<a href="competitor-detail.html?id=' + comp.id + '" class="text-link font-medium">' +
                    escapeHtml(comp.asin) +
                '</a>' +
                '<div class="text-muted text-sm">amazon.' + comp.marketplace + '</div>' +
            '</td>' +
            '<td class="text-truncate" style="max-width: 200px;" title="' + escapeHtml(data.title || '') + '">' +
                escapeHtml(data.title || '-') +
            '</td>' +
            '<td>' +
                '<input type="number" class="inline-edit-input" ' +
                    'value="' + (comp.pack_size || 1) + '" ' +
                    'min="1" ' +
                    'data-competitor-id="' + comp.id + '" ' +
                    'onchange="updatePackSize(' + comp.id + ', this.value)">' +
            '</td>' +
            '<td>' + formatCurrency(data.price, data.currency) + '</td>' +
            '<td>' + formatCurrency(data.unit_price, data.currency) + '</td>' +
            '<td>' + formatRating(data.rating) + '</td>' +
            '<td>' + formatNumber(data.review_count) + '</td>' +
            '<td>' + formatSchedule(comp.schedule) + '</td>' +
            '<td>' + formatDate(lastScraped) + '</td>' +
            '<td>' +
                '<a href="competitor-detail.html?id=' + comp.id + '" class="btn btn-secondary btn-sm">View</a> ' +
                '<button class="btn btn-secondary btn-sm btn-icon" onclick="deleteCompetitor(' + comp.id + ')" title="Delete">' +
                    '<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">' +
                        '<polyline points="3 6 5 6 21 6"></polyline>' +
                        '<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>' +
                    '</svg>' +
                '</button>' +
            '</td>' +
        '</tr>';
    }
    tbody.innerHTML = html;
    // Reset select-all checkbox and selection count
    document.getElementById('select-all-competitors').checked = false;
    updateSelectedCount();
}

async function loadKeywords() {
    const tbody = document.getElementById('keywords-body');
    tbody.innerHTML = '<tr><td colspan="4" class="loading"><div class="spinner"></div> Loading...</td></tr>';

    try {
        const result = await api.listCompetitorKeywords(1, 50, skuId);
        renderKeywords(result.items || []);
    } catch (error) {
        console.error('Failed to load keywords:', error);
        tbody.innerHTML = '<tr><td colspan="4" class="empty-state">Failed to load keywords</td></tr>';
    }
}

function renderKeywords(keywords) {
    const tbody = document.getElementById('keywords-body');

    if (!keywords || keywords.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="empty-state">No keywords linked to this Parent SKU</td></tr>';
        return;
    }

    let html = '';
    for (const kw of keywords) {
        html += '<tr>' +
            '<td class="font-medium">' + escapeHtml(kw.keyword) + '</td>' +
            '<td>' + escapeHtml(kw.notes || '-') + '</td>' +
            '<td>' + (kw.linked_competitors_count || 0) + '</td>' +
            '<td>' + formatDate(kw.created_at) + '</td>' +
        '</tr>';
    }
    tbody.innerHTML = html;
}

async function addCompetitor() {
    const asin = document.getElementById('competitor-asin').value.trim();
    const marketplace = document.getElementById('competitor-marketplace').value;
    const packSize = parseInt(document.getElementById('competitor-pack-size').value) || 1;
    const schedule = document.getElementById('competitor-schedule').value || null;
    const notes = document.getElementById('competitor-notes').value.trim() || null;

    if (!asin) {
        alert('ASIN is required');
        return;
    }

    try {
        await api.createCompetitor({
            asin: asin,
            sku_id: parseInt(skuId),
            marketplace: marketplace,
            pack_size: packSize,
            schedule_type: schedule,
            notes: notes
        });

        alert('Competitor added successfully');
        document.getElementById('add-competitor-form').reset();
        switchTab('competitors');
        loadCompetitors();
        refreshStats();
    } catch (error) {
        console.error('Failed to add competitor:', error);
        alert('Failed to add competitor: ' + error.message);
    }
}

async function bulkAddCompetitors() {
    const asinsText = document.getElementById('bulk-asins').value.trim();
    const marketplace = document.getElementById('bulk-marketplace').value;
    const packSize = parseInt(document.getElementById('bulk-pack-size').value) || 1;

    if (!asinsText) {
        alert('Please enter at least one ASIN');
        return;
    }

    const asins = asinsText.split('\n')
        .map(a => a.trim())
        .filter(a => a.length > 0);

    if (asins.length === 0) {
        alert('No valid ASINs found');
        return;
    }

    const items = asins.map(asin => ({
        asin: asin,
        sku_id: parseInt(skuId),
        marketplace: marketplace,
        pack_size: packSize
    }));

    try {
        const result = await api.bulkCreateCompetitors(items);
        alert('Added ' + (result.created || items.length) + ' competitors');
        document.getElementById('bulk-add-form').reset();
        switchTab('competitors');
        loadCompetitors();
        refreshStats();
    } catch (error) {
        console.error('Failed to bulk add competitors:', error);
        alert('Failed to add competitors: ' + error.message);
    }
}

async function scrapeAll() {
    if (!confirm('Start scraping all competitors for this Parent SKU?')) {
        return;
    }

    try {
        await api.createCompetitorScrapeJob({
            job_name: 'Scrape ' + (skuData?.sku_code || 'SKU ' + skuId),
            sku_id: parseInt(skuId),
            job_type: 'manual'
        });
        alert('Scrape job created successfully');
    } catch (error) {
        console.error('Failed to create scrape job:', error);
        alert('Failed to create scrape job: ' + error.message);
    }
}

async function deleteCompetitor(id) {
    if (!confirm('Are you sure you want to delete this competitor?')) {
        return;
    }

    try {
        await api.deleteCompetitor(id);
        loadCompetitors();
        refreshStats();
    } catch (error) {
        console.error('Failed to delete competitor:', error);
        alert('Failed to delete competitor: ' + error.message);
    }
}

function renderPagination(total, page, size) {
    const pagination = document.getElementById('competitors-pagination');
    const totalPages = Math.ceil(total / size);

    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let html = '';
    if (page > 1) {
        html += '<button class="btn btn-secondary btn-sm" onclick="goToPage(' + (page - 1) + ')">Previous</button>';
    }
    html += '<span class="pagination-info">Page ' + page + ' of ' + totalPages + '</span>';
    if (page < totalPages) {
        html += '<button class="btn btn-secondary btn-sm" onclick="goToPage(' + (page + 1) + ')">Next</button>';
    }
    pagination.innerHTML = html;
}

function goToPage(page) {
    currentPage = page;
    loadCompetitors();
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
    return num.toFixed(1);
}

function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    return num.toLocaleString();
}

function formatSchedule(schedule) {
    if (!schedule || schedule === 'none') return 'Manual';
    const schedules = {
        daily: 'Daily',
        every_2_days: 'Every 2 Days',
        every_3_days: 'Every 3 Days',
        weekly: 'Weekly',
        monthly: 'Monthly'
    };
    return schedules[schedule] || schedule;
}

function formatDate(dateStr) {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    return date.toLocaleDateString();
}

// ===== Selection and Pack Size Functions =====

function toggleSelectAll(checkbox) {
    document.querySelectorAll('.competitor-checkbox').forEach(cb => {
        cb.checked = checkbox.checked;
    });
    updateSelectedCount();
}

function updateSelectedCount() {
    const checkboxes = document.querySelectorAll('.competitor-checkbox:checked');
    const count = checkboxes.length;
    document.getElementById('selected-count').textContent = count;
    document.getElementById('scrape-selected-btn').style.display = count > 0 ? 'inline-flex' : 'none';
}

async function scrapeSelected() {
    const checkboxes = document.querySelectorAll('.competitor-checkbox:checked');
    const ids = Array.from(checkboxes).map(cb => parseInt(cb.dataset.competitorId));

    if (ids.length === 0) {
        alert('Please select at least one competitor');
        return;
    }

    if (!confirm('Scrape ' + ids.length + ' selected competitor(s)?')) {
        return;
    }

    try {
        await api.createCompetitorScrapeJob({
            job_name: 'Scrape Selected - ' + (skuData?.sku_code || 'SKU ' + skuId),
            competitor_ids: ids,
            job_type: 'manual'
        });
        alert('Scrape job created for ' + ids.length + ' competitor(s)');
        // Uncheck all after successful scrape
        document.getElementById('select-all-competitors').checked = false;
        toggleSelectAll(document.getElementById('select-all-competitors'));
    } catch (error) {
        console.error('Failed to create scrape job:', error);
        alert('Failed to create scrape job: ' + error.message);
    }
}

async function updatePackSize(competitorId, newPackSize) {
    try {
        await api.updateCompetitor(competitorId, { pack_size: parseInt(newPackSize) });
        // No need to reload - inline update successful
    } catch (error) {
        console.error('Failed to update pack size:', error);
        alert('Failed to update pack size: ' + error.message);
        loadCompetitors(); // Reload to reset value
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// =============================================================================
// Comparison View (Competitors as Columns)
// =============================================================================

function renderComparisonView(competitors) {
    const container = document.querySelector('#view-comparison .comparison-table-wrapper');

    if (!competitors || competitors.length === 0) {
        container.innerHTML = '<div class="empty-state">No competitors to compare. Add one using the "Add Competitor" tab.</div>';
        return;
    }

    // Metrics to display as rows (based on PRD section 4.8)
    const metrics = [
        { key: 'image', label: 'Image', render: (c) => {
            const imgUrl = c.data?.main_image_url || '';
            return imgUrl ? '<img src="' + imgUrl + '" class="comparison-thumb" onclick="openLightbox(\'' + imgUrl + '\')" alt="Product">' : '-';
        }},
        { key: 'brand', label: 'Brand', render: (c) => escapeHtml(c.data?.brand || '-') },
        { key: 'asin', label: 'ASIN', render: (c) => '<a href="https://amazon.' + c.marketplace + '/dp/' + c.asin + '" target="_blank" class="comparison-asin-link">' + c.asin + '</a>' },
        { key: 'title', label: 'Title', render: (c) => '<div class="comparison-title">' + escapeHtml(c.data?.title || '-') + '</div>' },
        { key: 'pack_size', label: 'Pack Size', render: (c) => c.pack_size || 1 },
        { key: 'price', label: 'Price', render: (c) => formatCurrency(c.data?.price, c.data?.currency) },
        { key: 'unit_price', label: 'Unit Price', render: (c) => formatCurrency(c.data?.unit_price, c.data?.currency) },
        { key: 'shipping', label: 'Shipping', render: (c) => c.data?.shipping_price ? formatCurrency(c.data?.shipping_price, c.data?.currency) : 'Free' },
        { key: 'rating', label: 'Rating', render: (c) => formatRating(c.data?.rating) },
        { key: 'reviews', label: 'Reviews', render: (c) => formatNumber(c.data?.review_count) },
        { key: 'sales', label: 'Sales', render: (c) => escapeHtml(c.data?.past_sales || '-') },
        { key: 'seller', label: 'Sold By', render: (c) => escapeHtml(c.data?.sold_by || '-') },
        { key: 'fulfillment', label: 'Fulfillment', render: (c) => escapeHtml(c.data?.fulfilled_by || '-') },
        { key: 'availability', label: 'Availability', render: (c) => escapeHtml(c.data?.availability || 'In Stock') },
        { key: 'variations', label: 'Variations', render: (c) => c.data?.variations_count || 0 },
        { key: 'updated', label: 'Last Updated', render: (c) => formatDate(c.data?.scraped_at) },
    ];

    let html = '<table class="comparison-table">';

    // Header row with competitor ASINs
    html += '<thead><tr><th class="metric-label-col">Metric</th>';
    for (const comp of competitors) {
        html += '<th class="competitor-col">' + comp.asin + '</th>';
    }
    html += '</tr></thead><tbody>';

    // Data rows
    for (const metric of metrics) {
        html += '<tr><td class="metric-label">' + metric.label + '</td>';
        for (const comp of competitors) {
            html += '<td class="metric-value">' + metric.render(comp) + '</td>';
        }
        html += '</tr>';
    }

    html += '</tbody></table>';
    container.innerHTML = html;
}

// =============================================================================
// Images Comparison View
// =============================================================================

function renderImagesView(competitors) {
    const container = document.querySelector('#view-images .images-comparison');

    if (!competitors || competitors.length === 0) {
        container.innerHTML = '<div class="empty-state">No competitors to show. Add one using the "Add Competitor" tab.</div>';
        return;
    }

    let html = '';

    for (const comp of competitors) {
        const data = comp.data || {};
        const mainImage = data.main_image_url || '';
        const images = data.image_urls || [];

        // Combine main image with other images (deduplicated)
        let allImages = [];
        if (mainImage) allImages.push(mainImage);
        for (const img of images) {
            if (img && !allImages.includes(img)) {
                allImages.push(img);
            }
        }

        html += '<div class="images-row">' +
            '<div class="images-row-header">' +
                '<a href="https://amazon.' + comp.marketplace + '/dp/' + comp.asin + '" target="_blank" class="asin-link">' + comp.asin + '</a>' +
                '<div class="images-row-title" title="' + escapeHtml(data.title || '') + '">' + escapeHtml(data.title || '-') + '</div>' +
                '<span class="images-row-price">' + formatCurrency(data.price, data.currency) + '</span>' +
                '<span class="images-row-rating">' + formatRating(data.rating) + '</span>' +
            '</div>' +
            '<div class="images-row-gallery">';

        if (allImages.length > 0) {
            for (const imgUrl of allImages.slice(0, 10)) { // Limit to 10 images per competitor
                html += '<img src="' + imgUrl + '" class="gallery-thumb" onclick="openLightbox(\'' + imgUrl + '\')" alt="Product image">';
            }
        } else {
            html += '<div class="empty-state" style="padding: 20px;">No images available</div>';
        }

        html += '</div></div>';
    }

    container.innerHTML = html;
}

// =============================================================================
// Content Comparison View (Title, Bullets, Description)
// =============================================================================

function renderContentView(competitors) {
    const container = document.querySelector('#view-content .content-comparison');

    if (!competitors || competitors.length === 0) {
        container.innerHTML = '<div class="empty-state">No competitors to compare. Add one using the "Add Competitor" tab.</div>';
        return;
    }

    let html = '';

    for (const comp of competitors) {
        const data = comp.data || {};
        const features = data.features || [];
        const mainImage = data.main_image_url || '';

        html += '<div class="content-card">' +
            '<div class="content-card-header">' +
                (mainImage ? '<img src="' + mainImage + '" class="content-thumb" onclick="openLightbox(\'' + mainImage + '\')" alt="Product">' : '') +
                '<div class="content-card-info">' +
                    '<a href="https://amazon.' + comp.marketplace + '/dp/' + comp.asin + '" target="_blank" class="asin-link">' + comp.asin + '</a>' +
                    '<div class="content-price">' + formatCurrency(data.price, data.currency) + ' | ' + formatRating(data.rating) + ' | ' + formatNumber(data.review_count) + ' reviews</div>' +
                '</div>' +
            '</div>' +
            '<div class="content-section">' +
                '<h4>Title</h4>' +
                '<p class="content-title">' + escapeHtml(data.title || '-') + '</p>' +
            '</div>' +
            '<div class="content-section">' +
                '<h4>Bullet Points (' + features.length + ')</h4>';

        if (features.length > 0) {
            html += '<ul class="content-bullets">';
            for (const feature of features) {
                html += '<li>' + escapeHtml(feature) + '</li>';
            }
            html += '</ul>';
        } else {
            html += '<p class="empty">No bullet points available</p>';
        }

        html += '</div>' +
            '<div class="content-section">' +
                '<h4>Description</h4>' +
                '<div class="content-description">';

        if (data.description) {
            html += escapeHtml(data.description);
        } else {
            html += '<span class="empty">No description available</span>';
        }

        html += '</div></div></div>';
    }

    container.innerHTML = html;
}

// =============================================================================
// Lightbox Functions
// =============================================================================

function openLightbox(imageUrl) {
    const lightbox = document.getElementById('image-lightbox');
    const lightboxImg = document.getElementById('lightbox-image');
    lightboxImg.src = imageUrl;
    lightbox.style.display = 'flex';
}

function closeLightbox() {
    document.getElementById('image-lightbox').style.display = 'none';
}
