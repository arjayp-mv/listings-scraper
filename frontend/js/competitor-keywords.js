/**
 * =============================================================================
 * Amazon Reviews Scraper - Competitor Keywords Page
 * =============================================================================
 */

let currentPage = 1;
const pageSize = 20;
let currentSearch = '';
let currentSkuId = null;
let skuOptions = [];
let currentKeywordId = null;

document.addEventListener('DOMContentLoaded', () => {
    loadSkuOptions();
    loadKeywords();
    setupEventListeners();
});

function setupEventListeners() {
    // Search
    document.getElementById('search-btn').addEventListener('click', doSearch);
    document.getElementById('clear-btn').addEventListener('click', clearSearch);
    document.getElementById('search-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') doSearch();
    });
    document.getElementById('sku-filter').addEventListener('change', doSearch);

    // Add keyword
    document.getElementById('add-keyword-btn').addEventListener('click', () => showKeywordModal());

    // Modal events
    document.getElementById('close-modal').addEventListener('click', hideKeywordModal);
    document.getElementById('cancel-modal').addEventListener('click', hideKeywordModal);
    document.getElementById('save-keyword').addEventListener('click', saveKeyword);
    document.querySelector('#keyword-modal .modal-overlay').addEventListener('click', hideKeywordModal);

    // Link modal events
    document.getElementById('close-link-modal').addEventListener('click', hideLinkModal);
    document.getElementById('close-link-btn').addEventListener('click', hideLinkModal);
    document.querySelector('#link-modal .modal-overlay').addEventListener('click', hideLinkModal);

    // Link tabs
    document.querySelectorAll('[data-link-tab]').forEach(btn => {
        btn.addEventListener('click', () => switchLinkTab(btn.dataset.linkTab));
    });
}

function doSearch() {
    currentSearch = document.getElementById('search-input').value.trim();
    currentSkuId = document.getElementById('sku-filter').value || null;
    currentPage = 1;
    loadKeywords();
}

function clearSearch() {
    document.getElementById('search-input').value = '';
    document.getElementById('sku-filter').value = '';
    currentSearch = '';
    currentSkuId = null;
    currentPage = 1;
    loadKeywords();
}

async function loadSkuOptions() {
    try {
        const result = await api.listSkus(1, 50);
        skuOptions = result.items || [];

        // Populate filter dropdown
        const filterSelect = document.getElementById('sku-filter');
        const formSelect = document.getElementById('keyword-sku');

        for (const sku of skuOptions) {
            const option = document.createElement('option');
            option.value = sku.id;
            option.textContent = sku.display_name || sku.sku_code;

            filterSelect.appendChild(option.cloneNode(true));
            formSelect.appendChild(option);
        }
    } catch (error) {
        console.error('Failed to load SKU options:', error);
    }
}

async function loadKeywords() {
    const tbody = document.getElementById('keywords-body');
    tbody.innerHTML = '<tr><td colspan="7" class="loading"><div class="spinner"></div> Loading...</td></tr>';

    try {
        const result = await api.listCompetitorKeywords(currentPage, pageSize, currentSkuId, currentSearch || null);
        renderKeywords(result.items || []);
        renderPagination(result.total || 0, result.page || 1, result.page_size || pageSize);
    } catch (error) {
        console.error('Failed to load keywords:', error);
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">Failed to load keywords</td></tr>';
    }
}

function renderKeywords(keywords) {
    const tbody = document.getElementById('keywords-body');

    if (!keywords || keywords.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="empty-state">No keywords found. Click "Add Keyword" to create one.</td></tr>';
        return;
    }

    let html = '';
    for (const kw of keywords) {
        html += '<tr>' +
            '<td class="font-medium">' + escapeHtml(kw.keyword) + '</td>' +
            '<td>' + escapeHtml(kw.sku_code || '-') + '</td>' +
            '<td>' + escapeHtml(kw.notes || '-') + '</td>' +
            '<td>' + (kw.linked_channel_skus_count || 0) + '</td>' +
            '<td>' + (kw.linked_competitors_count || 0) + '</td>' +
            '<td>' + formatDate(kw.created_at) + '</td>' +
            '<td>' +
                '<button class="btn btn-secondary btn-sm" onclick="showLinkModal(' + kw.id + ')">Links</button> ' +
                '<button class="btn btn-secondary btn-sm" onclick="editKeyword(' + kw.id + ')">Edit</button> ' +
                '<button class="btn btn-secondary btn-sm" onclick="deleteKeyword(' + kw.id + ')">Delete</button>' +
            '</td>' +
        '</tr>';
    }
    tbody.innerHTML = html;
}

function showKeywordModal(keyword = null) {
    const modal = document.getElementById('keyword-modal');
    const title = document.getElementById('modal-title');

    if (keyword) {
        title.textContent = 'Edit Keyword';
        document.getElementById('keyword-id').value = keyword.id;
        document.getElementById('keyword-text').value = keyword.keyword;
        document.getElementById('keyword-sku').value = keyword.sku_id;
        document.getElementById('keyword-notes').value = keyword.notes || '';
    } else {
        title.textContent = 'Add Keyword';
        document.getElementById('keyword-form').reset();
        document.getElementById('keyword-id').value = '';
    }

    modal.style.display = 'flex';
}

function hideKeywordModal() {
    document.getElementById('keyword-modal').style.display = 'none';
}

async function editKeyword(id) {
    try {
        const keyword = await api.getCompetitorKeyword(id);
        showKeywordModal(keyword);
    } catch (error) {
        console.error('Failed to load keyword:', error);
        alert('Failed to load keyword');
    }
}

async function saveKeyword() {
    const id = document.getElementById('keyword-id').value;
    const keyword = document.getElementById('keyword-text').value.trim();
    const skuId = document.getElementById('keyword-sku').value;
    const notes = document.getElementById('keyword-notes').value.trim() || null;

    if (!keyword || !skuId) {
        alert('Keyword and Parent SKU are required');
        return;
    }

    try {
        if (id) {
            await api.updateCompetitorKeyword(id, { keyword, sku_id: parseInt(skuId), notes });
        } else {
            await api.createCompetitorKeyword({ keyword, sku_id: parseInt(skuId), notes });
        }

        hideKeywordModal();
        loadKeywords();
    } catch (error) {
        console.error('Failed to save keyword:', error);
        alert('Failed to save keyword: ' + error.message);
    }
}

async function deleteKeyword(id) {
    if (!confirm('Are you sure you want to delete this keyword?')) {
        return;
    }

    try {
        await api.deleteCompetitorKeyword(id);
        loadKeywords();
    } catch (error) {
        console.error('Failed to delete keyword:', error);
        alert('Failed to delete keyword: ' + error.message);
    }
}

// Link modal functions
async function showLinkModal(keywordId) {
    currentKeywordId = keywordId;
    const modal = document.getElementById('link-modal');
    modal.style.display = 'flex';

    // Load channel SKUs and competitors for linking
    loadChannelSkusForLinking();
    loadCompetitorsForLinking();
}

function hideLinkModal() {
    document.getElementById('link-modal').style.display = 'none';
    currentKeywordId = null;
    // Refresh keywords list to update counts
    loadKeywords();
}

function switchLinkTab(tab) {
    document.querySelectorAll('[data-link-tab]').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.linkTab === tab);
    });
    document.querySelectorAll('.link-tab-content').forEach(content => {
        content.style.display = content.id === 'link-tab-' + tab ? 'block' : 'none';
    });
}

async function loadChannelSkusForLinking() {
    const container = document.getElementById('channel-sku-list');
    container.innerHTML = '<p class="text-muted">Loading...</p>';

    try {
        // Get keyword with linked channel_skus
        const keyword = await api.getCompetitorKeyword(currentKeywordId);
        const linkedIds = (keyword.linked_channel_skus || []).map(cs => cs.id);

        // Get all channel SKUs for this SKU
        const result = await api.listChannelSkus(1, 50, null, null, keyword.sku_code);
        const channelSkus = result.items || [];

        if (channelSkus.length === 0) {
            container.innerHTML = '<p class="text-muted">No Channel SKUs found for this Parent SKU</p>';
            return;
        }

        let html = '';
        for (const cs of channelSkus) {
            const isLinked = linkedIds.includes(cs.id);
            html += '<div style="padding: 8px 0; border-bottom: 1px solid var(--gray-200);">' +
                '<label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">' +
                    '<input type="checkbox" ' + (isLinked ? 'checked' : '') + ' onchange="toggleChannelSkuLink(' + cs.id + ', this.checked)">' +
                    '<span>' + escapeHtml(cs.channel_sku_code) + ' - ' + escapeHtml(cs.current_asin || 'No ASIN') + '</span>' +
                '</label>' +
            '</div>';
        }
        container.innerHTML = html;
    } catch (error) {
        console.error('Failed to load channel SKUs:', error);
        container.innerHTML = '<p class="text-muted">Failed to load Channel SKUs</p>';
    }
}

async function loadCompetitorsForLinking() {
    const container = document.getElementById('competitor-list');
    container.innerHTML = '<p class="text-muted">Loading...</p>';

    try {
        // Get keyword with linked competitors
        const keyword = await api.getCompetitorKeyword(currentKeywordId);
        const linkedIds = (keyword.linked_competitors || []).map(c => c.id);

        // Get all competitors for this SKU
        const result = await api.listCompetitors(1, 50, keyword.sku_id);
        const competitors = result.items || [];

        if (competitors.length === 0) {
            container.innerHTML = '<p class="text-muted">No Competitors found for this Parent SKU</p>';
            return;
        }

        let html = '';
        for (const comp of competitors) {
            const isLinked = linkedIds.includes(comp.id);
            html += '<div style="padding: 8px 0; border-bottom: 1px solid var(--gray-200);">' +
                '<label style="display: flex; align-items: center; gap: 8px; cursor: pointer;">' +
                    '<input type="checkbox" ' + (isLinked ? 'checked' : '') + ' onchange="toggleCompetitorLink(' + comp.id + ', this.checked)">' +
                    '<span>' + escapeHtml(comp.asin) + ' - ' + escapeHtml(comp.data?.title || 'No title') + '</span>' +
                '</label>' +
            '</div>';
        }
        container.innerHTML = html;
    } catch (error) {
        console.error('Failed to load competitors:', error);
        container.innerHTML = '<p class="text-muted">Failed to load Competitors</p>';
    }
}

async function toggleChannelSkuLink(channelSkuId, isLinked) {
    try {
        if (isLinked) {
            await api.linkChannelSkuToKeyword(currentKeywordId, channelSkuId);
        } else {
            await api.unlinkChannelSkuFromKeyword(currentKeywordId, channelSkuId);
        }
    } catch (error) {
        console.error('Failed to toggle link:', error);
        alert('Failed to update link: ' + error.message);
        // Reload to reset checkbox state
        loadChannelSkusForLinking();
    }
}

async function toggleCompetitorLink(competitorId, isLinked) {
    try {
        if (isLinked) {
            await api.linkCompetitorToKeyword(currentKeywordId, competitorId);
        } else {
            await api.unlinkCompetitorFromKeyword(currentKeywordId, competitorId);
        }
    } catch (error) {
        console.error('Failed to toggle link:', error);
        alert('Failed to update link: ' + error.message);
        // Reload to reset checkbox state
        loadCompetitorsForLinking();
    }
}

function renderPagination(total, page, size) {
    const pagination = document.getElementById('pagination');
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
    loadKeywords();
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString();
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
