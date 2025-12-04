/**
 * =============================================================================
 * Amazon Reviews Scraper - Competitor Detail Page
 * =============================================================================
 */

let competitorId = null;
let competitorData = null;

document.addEventListener('DOMContentLoaded', () => {
    const params = new URLSearchParams(window.location.search);
    competitorId = params.get('id');

    if (!competitorId) {
        alert('No competitor ID provided');
        window.location.href = 'competitor-parent-skus.html';
        return;
    }

    loadCompetitorData();
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

    // Edit button
    document.getElementById('edit-btn').addEventListener('click', showEditModal);
    document.getElementById('close-modal').addEventListener('click', hideEditModal);
    document.getElementById('cancel-edit').addEventListener('click', hideEditModal);
    document.getElementById('save-edit').addEventListener('click', saveEdit);
    document.querySelector('.modal-overlay').addEventListener('click', hideEditModal);

    // Scrape button
    document.getElementById('scrape-btn').addEventListener('click', scrapeCompetitor);

    // Copy buttons
    document.getElementById('copy-bullets-btn').addEventListener('click', copyBullets);
    document.getElementById('copy-desc-btn').addEventListener('click', copyDescription);

    // History days filter
    document.getElementById('history-days').addEventListener('change', loadPriceHistory);
}

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === 'tab-' + tab);
    });

    if (tab === 'history') {
        loadPriceHistory();
    }
}

async function loadCompetitorData() {
    try {
        const competitor = await api.getCompetitor(competitorId);
        competitorData = competitor;

        // Update breadcrumb
        document.getElementById('breadcrumb-sku').textContent = competitor.sku_code || competitor.sku_display_name || 'Unknown SKU';
        document.getElementById('breadcrumb-sku').href = 'competitor-parent-sku-detail.html?id=' + competitor.sku_id;
        document.getElementById('breadcrumb-asin').textContent = competitor.asin;

        // Update page title
        document.getElementById('page-title').textContent = competitor.asin + ' - amazon.' + competitor.marketplace;

        // Update product info
        const data = competitor.data || {};

        document.getElementById('main-image').src = data.main_image_url || '';
        document.getElementById('product-title').textContent = data.title || 'No data - Click "Refresh Data" to scrape';
        document.getElementById('product-brand').textContent = data.brand ? 'Brand: ' + data.brand : '';
        document.getElementById('product-marketplace').textContent = 'amazon.' + competitor.marketplace;
        document.getElementById('product-price').textContent = formatCurrency(data.price, data.currency);

        if (data.unit_price) {
            document.getElementById('product-unit-price').textContent = '(' + formatCurrency(data.unit_price, data.currency) + '/unit)';
        }

        document.getElementById('product-rating').textContent = formatRating(data.rating);
        document.getElementById('product-reviews').textContent = data.review_count ? formatNumber(data.review_count) + ' reviews' : '';
        document.getElementById('product-schedule').textContent = formatSchedule(competitor.schedule);
        document.getElementById('product-last-scraped').textContent = formatDateTime(data.scraped_at);

        // Render images
        renderImages(data.images || []);

        // Render bullet points
        renderBullets(data.features || []);

        // Render description
        document.getElementById('description-text').textContent = data.product_description || 'No description available';

    } catch (error) {
        console.error('Failed to load competitor data:', error);
        alert('Failed to load competitor data');
    }
}

function renderImages(images) {
    const gallery = document.getElementById('image-gallery');

    if (!images || images.length === 0) {
        gallery.innerHTML = '<p class="text-muted">No images available</p>';
        return;
    }

    let html = '';
    for (const img of images) {
        const url = typeof img === 'string' ? img : img.url;
        if (url) {
            html += '<img src="' + url + '" class="gallery-image" onclick="window.open(\'' + url + '\', \'_blank\')" alt="Product Image">';
        }
    }
    gallery.innerHTML = html || '<p class="text-muted">No images available</p>';
}

function renderBullets(features) {
    const list = document.getElementById('bullet-list');

    if (!features || features.length === 0) {
        list.innerHTML = '<li class="text-muted">No bullet points available</li>';
        return;
    }

    let html = '';
    for (const feature of features) {
        const text = typeof feature === 'string' ? feature : feature.text;
        if (text) {
            html += '<li>' + escapeHtml(text) + '</li>';
        }
    }
    list.innerHTML = html || '<li class="text-muted">No bullet points available</li>';
}

async function loadPriceHistory() {
    const tbody = document.getElementById('history-body');
    tbody.innerHTML = '<tr><td colspan="6" class="loading"><div class="spinner"></div> Loading...</td></tr>';

    const days = parseInt(document.getElementById('history-days').value) || 365;

    try {
        const history = await api.getCompetitorPriceHistory(competitorId, days);
        renderPriceHistory(history || []);
    } catch (error) {
        console.error('Failed to load price history:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Failed to load price history</td></tr>';
    }
}

function renderPriceHistory(history) {
    const tbody = document.getElementById('history-body');

    if (!history || history.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No price history available</td></tr>';
        return;
    }

    let html = '';
    let prevPrice = null;

    for (const record of history) {
        let changeHtml = '-';
        if (prevPrice !== null && record.price !== null) {
            const diff = record.price - prevPrice;
            if (diff !== 0) {
                const isDecrease = diff < 0;
                const changeClass = isDecrease ? 'text-success' : 'text-danger';
                const icon = isDecrease ? '&#x25BC;' : '&#x25B2;';
                changeHtml = '<span class="' + changeClass + '">' + icon + ' ' + formatCurrency(Math.abs(diff), record.currency) + '</span>';
            }
        }

        html += '<tr>' +
            '<td>' + formatDate(record.recorded_at) + '</td>' +
            '<td>' + formatCurrency(record.price, record.currency) + '</td>' +
            '<td>' + formatCurrency(record.unit_price, record.currency) + '</td>' +
            '<td>' + formatRating(record.rating) + '</td>' +
            '<td>' + formatNumber(record.review_count) + '</td>' +
            '<td>' + changeHtml + '</td>' +
        '</tr>';

        prevPrice = record.price;
    }
    tbody.innerHTML = html;
}

function showEditModal() {
    const modal = document.getElementById('edit-modal');
    document.getElementById('edit-pack-size').value = competitorData.pack_size || 1;
    document.getElementById('edit-schedule').value = competitorData.schedule || 'none';
    document.getElementById('edit-notes').value = competitorData.notes || '';
    modal.style.display = 'flex';
}

function hideEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
}

async function saveEdit() {
    const packSize = parseInt(document.getElementById('edit-pack-size').value) || 1;
    const schedule = document.getElementById('edit-schedule').value || 'none';
    const notes = document.getElementById('edit-notes').value.trim() || null;

    try {
        await api.updateCompetitor(competitorId, {
            pack_size: packSize,
            schedule: schedule,
            notes: notes
        });

        hideEditModal();
        loadCompetitorData();
    } catch (error) {
        console.error('Failed to update competitor:', error);
        alert('Failed to update competitor: ' + error.message);
    }
}

async function scrapeCompetitor() {
    if (!confirm('Start scraping this competitor?')) {
        return;
    }

    try {
        await api.createCompetitorScrapeJob({
            job_name: 'Scrape ' + competitorData.asin,
            competitor_ids: [parseInt(competitorId)],
            job_type: 'manual'
        });
        alert('Scrape job created. Data will be updated shortly.');
    } catch (error) {
        console.error('Failed to create scrape job:', error);
        alert('Failed to create scrape job: ' + error.message);
    }
}

function copyBullets() {
    const features = competitorData?.data?.features || [];
    const text = features.map(f => typeof f === 'string' ? f : f.text).filter(Boolean).join('\n');

    if (!text) {
        alert('No bullet points to copy');
        return;
    }

    navigator.clipboard.writeText(text).then(() => {
        alert('Bullet points copied to clipboard');
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy to clipboard');
    });
}

function copyDescription() {
    const text = competitorData?.data?.product_description || '';

    if (!text) {
        alert('No description to copy');
        return;
    }

    navigator.clipboard.writeText(text).then(() => {
        alert('Description copied to clipboard');
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy to clipboard');
    });
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

function formatNumber(num) {
    if (num === null || num === undefined) return '-';
    return num.toLocaleString();
}

function formatSchedule(schedule) {
    if (!schedule) return 'Manual';
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
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString();
}

function formatDateTime(dateStr) {
    if (!dateStr) return 'Never';
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
