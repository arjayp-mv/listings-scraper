/**
 * =============================================================================
 * Amazon Reviews Scraper - API Client
 * =============================================================================
 * Purpose: Centralized API calls to the backend
 * Public API: api object with methods for each endpoint
 * =============================================================================
 */

const API_BASE = '/api';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
    const url = API_BASE + endpoint;

    const defaultOptions = {
        headers: {
            'Content-Type': 'application/json',
        },
    };

    const mergedOptions = {
        ...defaultOptions,
        ...options,
        headers: {
            ...defaultOptions.headers,
            ...options.headers,
        },
    };

    try {
        const response = await fetch(url, mergedOptions);

        // Handle no content responses
        if (response.status === 204) {
            return null;
        }

        const data = await response.json();

        if (!response.ok) {
            // Handle Pydantic validation errors (422)
            let errorMessage = 'API request failed';
            if (data.detail) {
                if (typeof data.detail === 'string') {
                    errorMessage = data.detail;
                } else if (Array.isArray(data.detail)) {
                    // Pydantic validation errors are arrays
                    errorMessage = data.detail.map(err => {
                        const loc = err.loc ? err.loc.join('.') : '';
                        return loc ? `${loc}: ${err.msg}` : err.msg;
                    }).join('; ');
                } else {
                    errorMessage = JSON.stringify(data.detail);
                }
            }
            throw new Error(errorMessage);
        }

        return data;
    } catch (error) {
        console.error('API Error:', error);
        throw error;
    }
}

/**
 * API client object
 */
const api = {
    // ===== Dashboard =====
    getDashboardStats: () => fetchAPI('/dashboard/stats'),
    getQueueStatus: () => fetchAPI('/queue/status'),

    // ===== SKUs =====
    listSkus: (page = 1, pageSize = 20, search = null) => {
        let url = '/skus?page=' + page + '&page_size=' + pageSize;
        if (search) url += '&search=' + encodeURIComponent(search);
        return fetchAPI(url);
    },

    listSkusWithChannelSkuStats: (page = 1, pageSize = 20, search = null) => {
        let url = '/skus/with-channel-sku-stats?page=' + page + '&page_size=' + pageSize;
        if (search) url += '&search=' + encodeURIComponent(search);
        return fetchAPI(url);
    },

    searchSkus: (query) =>
        fetchAPI('/skus/search?q=' + encodeURIComponent(query)),

    createSku: (data) =>
        fetchAPI('/skus', {
            method: 'POST',
            body: JSON.stringify(data),
        }),

    getSku: (id) => fetchAPI('/skus/' + id),

    updateSku: (id, data) =>
        fetchAPI('/skus/' + id, {
            method: 'PUT',
            body: JSON.stringify(data),
        }),

    deleteSku: (id) =>
        fetchAPI('/skus/' + id, { method: 'DELETE' }),

    // SKU Reviews
    listSkuReviews: (skuId, page = 1, pageSize = 20, search = null, rating = null) => {
        let url = '/skus/' + skuId + '/reviews?page=' + page + '&page_size=' + pageSize;
        if (search) url += '&search=' + encodeURIComponent(search);
        if (rating) url += '&rating=' + rating;
        return fetchAPI(url);
    },

    getSkuFormattedReviews: (skuId, search = null, rating = null) => {
        let url = '/skus/' + skuId + '/reviews/formatted';
        const params = [];
        if (search) params.push('search=' + encodeURIComponent(search));
        if (rating) params.push('rating=' + rating);
        if (params.length) url += '?' + params.join('&');
        return fetchAPI(url);
    },

    getSkuReviewStats: (skuId) => fetchAPI('/skus/' + skuId + '/reviews/stats'),

    getSkuExcelExportUrl: (skuId) => API_BASE + '/skus/' + skuId + '/reviews/export/excel',

    // ===== Jobs =====
    listJobs: (page = 1, pageSize = 20, status = null, skuId = null) => {
        let url = '/jobs?page=' + page + '&page_size=' + pageSize;
        if (status) url += '&status=' + status;
        if (skuId) url += '&sku_id=' + skuId;
        return fetchAPI(url);
    },

    createJob: (data) =>
        fetchAPI('/jobs', {
            method: 'POST',
            body: JSON.stringify(data),
        }),

    getJob: (id) => fetchAPI('/jobs/' + id),

    deleteJob: (id) =>
        fetchAPI('/jobs/' + id, { method: 'DELETE' }),

    cancelJob: (id) =>
        fetchAPI('/jobs/' + id + '/cancel', { method: 'POST' }),

    retryFailedAsins: (id) =>
        fetchAPI('/jobs/' + id + '/retry-failed', { method: 'POST' }),

    checkAsinHistory: (asins, marketplace) =>
        fetchAPI('/jobs/check-history', {
            method: 'POST',
            body: JSON.stringify({ asins, marketplace }),
        }),

    // ===== Reviews =====
    listReviews: (jobId, page = 1, pageSize = 20, search = null, rating = null, asin = null) => {
        let url = '/jobs/' + jobId + '/reviews?page=' + page + '&page_size=' + pageSize;
        if (search) url += '&search=' + encodeURIComponent(search);
        if (rating) url += '&rating=' + rating;
        if (asin) url += '&asin=' + asin;
        return fetchAPI(url);
    },

    getFormattedReviews: (jobId, search = null, rating = null) => {
        let url = '/jobs/' + jobId + '/reviews/formatted';
        const params = [];
        if (search) params.push('search=' + encodeURIComponent(search));
        if (rating) params.push('rating=' + rating);
        if (params.length) url += '?' + params.join('&');
        return fetchAPI(url);
    },

    getReviewStats: (jobId) => fetchAPI('/jobs/' + jobId + '/reviews/stats'),

    exportReviewsJson: (jobId) => fetchAPI('/jobs/' + jobId + '/reviews/export/json'),

    getExcelExportUrl: (jobId) => API_BASE + '/jobs/' + jobId + '/reviews/export/excel',

    // ===== Channel SKUs =====
    listChannelSkus: (page = 1, pageSize = 20, search = null, marketplace = null, skuCode = null, minRating = null, maxRating = null) => {
        let url = '/channel-skus?page=' + page + '&page_size=' + pageSize;
        if (search) url += '&search=' + encodeURIComponent(search);
        if (marketplace) url += '&marketplace=' + marketplace;
        if (skuCode) url += '&sku_code=' + encodeURIComponent(skuCode);
        if (minRating !== null) url += '&min_rating=' + minRating;
        if (maxRating !== null) url += '&max_rating=' + maxRating;
        return fetchAPI(url);
    },

    createChannelSku: (data) =>
        fetchAPI('/channel-skus', {
            method: 'POST',
            body: JSON.stringify(data),
        }),

    bulkCreateChannelSkus: (items, marketplace) =>
        fetchAPI('/channel-skus/bulk', {
            method: 'POST',
            body: JSON.stringify({ items: items.map(item => ({ ...item, marketplace })) }),
        }),

    getChannelSku: (id) => fetchAPI('/channel-skus/' + id),

    deleteChannelSku: (id) =>
        fetchAPI('/channel-skus/' + id, { method: 'DELETE' }),

    getChannelSkuHistory: (id) => fetchAPI('/channel-skus/' + id + '/history'),

    getChannelSkuScanHistory: (id) => fetchAPI('/channel-skus/' + id + '/scan-history'),

    getChannelSkuStats: () => fetchAPI('/channel-skus/stats/summary'),

    exportChannelSkusCsv: () => API_BASE + '/channel-skus/export/csv',

    // ===== Product Scans =====
    listProductScans: (page = 1, pageSize = 20, status = null, search = null) => {
        let url = '/product-scans?page=' + page + '&page_size=' + pageSize;
        if (status) url += '&status=' + status;
        if (search) url += '&search=' + encodeURIComponent(search);
        return fetchAPI(url);
    },

    createProductScan: (data) =>
        fetchAPI('/product-scans', {
            method: 'POST',
            body: JSON.stringify(data),
        }),

    createProductScanFromChannelSkus: (jobName, marketplace, channelSkuIds) =>
        fetchAPI('/product-scans/from-channel-skus?job_name=' + encodeURIComponent(jobName), {
            method: 'POST',
            body: JSON.stringify({ marketplace, channel_sku_ids: channelSkuIds }),
        }),

    getProductScan: (id) => fetchAPI('/product-scans/' + id),

    getProductScanResults: (id, page = 1, pageSize = 20, status = null) => {
        let url = '/product-scans/' + id + '/results?page=' + page + '&page_size=' + pageSize;
        if (status) url += '&status=' + status;
        return fetchAPI(url);
    },

    getProductScanStats: () => fetchAPI('/product-scans/stats'),

    cancelProductScan: (id) =>
        fetchAPI('/product-scans/' + id + '/cancel', { method: 'POST' }),

    retryFailedProductScanItems: (id) =>
        fetchAPI('/product-scans/' + id + '/retry-failed', { method: 'POST' }),

    deleteProductScan: (id) =>
        fetchAPI('/product-scans/' + id, { method: 'DELETE' }),

    getProductScanCsvUrl: (id) => API_BASE + '/product-scans/' + id + '/export/csv',

    getProductScanExcelUrl: (id) => API_BASE + '/product-scans/' + id + '/export/excel',

    // ===== Competitors =====
    listCompetitors: (page = 1, pageSize = 20, skuId = null, marketplace = null, search = null, includeData = false) => {
        let url = '/competitors?page=' + page + '&per_page=' + pageSize;
        if (skuId) url += '&sku_id=' + skuId;
        if (marketplace) url += '&marketplace=' + marketplace;
        if (search) url += '&search=' + encodeURIComponent(search);
        if (includeData) url += '&include_data=true';
        return fetchAPI(url);
    },

    createCompetitor: (data) =>
        fetchAPI('/competitors', {
            method: 'POST',
            body: JSON.stringify(data),
        }),

    bulkCreateCompetitors: (competitors) =>
        fetchAPI('/competitors/bulk', {
            method: 'POST',
            body: JSON.stringify({ competitors }),
        }),

    getCompetitor: (id) => fetchAPI('/competitors/' + id),

    updateCompetitor: (id, data) =>
        fetchAPI('/competitors/' + id, {
            method: 'PUT',
            body: JSON.stringify(data),
        }),

    deleteCompetitor: (id) =>
        fetchAPI('/competitors/' + id, { method: 'DELETE' }),

    getCompetitorPriceHistory: (id, days = 365) =>
        fetchAPI('/competitors/' + id + '/price-history?days=' + days),

    updateCompetitorSchedule: (id, data) =>
        fetchAPI('/competitors/' + id + '/schedule', {
            method: 'PUT',
            body: JSON.stringify(data),
        }),

    // ===== Competitor Keywords =====
    listCompetitorKeywords: (page = 1, pageSize = 20, skuId = null, search = null) => {
        let url = '/competitors/keywords?page=' + page + '&per_page=' + pageSize;
        if (skuId) url += '&sku_id=' + skuId;
        if (search) url += '&search=' + encodeURIComponent(search);
        return fetchAPI(url);
    },

    createCompetitorKeyword: (data) =>
        fetchAPI('/competitors/keywords', {
            method: 'POST',
            body: JSON.stringify(data),
        }),

    getCompetitorKeyword: (id) => fetchAPI('/competitors/keywords/' + id),

    updateCompetitorKeyword: (id, data) =>
        fetchAPI('/competitors/keywords/' + id, {
            method: 'PUT',
            body: JSON.stringify(data),
        }),

    deleteCompetitorKeyword: (id) =>
        fetchAPI('/competitors/keywords/' + id, { method: 'DELETE' }),

    linkChannelSkuToKeyword: (keywordId, channelSkuId) =>
        fetchAPI('/competitors/keywords/' + keywordId + '/channel-skus/' + channelSkuId, {
            method: 'POST',
        }),

    unlinkChannelSkuFromKeyword: (keywordId, channelSkuId) =>
        fetchAPI('/competitors/keywords/' + keywordId + '/channel-skus/' + channelSkuId, {
            method: 'DELETE',
        }),

    linkCompetitorToKeyword: (keywordId, competitorId) =>
        fetchAPI('/competitors/keywords/' + keywordId + '/competitors/' + competitorId, {
            method: 'POST',
        }),

    unlinkCompetitorFromKeyword: (keywordId, competitorId) =>
        fetchAPI('/competitors/keywords/' + keywordId + '/competitors/' + competitorId, {
            method: 'DELETE',
        }),

    // ===== Competitor Scrape Jobs =====
    listCompetitorScrapeJobs: (page = 1, pageSize = 20, status = null) => {
        let url = '/competitors/scrape-jobs?page=' + page + '&per_page=' + pageSize;
        if (status) url += '&status=' + status;
        return fetchAPI(url);
    },

    createCompetitorScrapeJob: (data) =>
        fetchAPI('/competitors/scrape-jobs', {
            method: 'POST',
            body: JSON.stringify(data),
        }),

    getCompetitorScrapeJob: (id) => fetchAPI('/competitors/scrape-jobs/' + id),

    // ===== Competitor Dashboard =====
    getCompetitorDashboardStats: () => fetchAPI('/competitors/dashboard/stats'),

    getCompetitorStatsBySku: (skuId) => fetchAPI('/competitors/dashboard/by-sku/' + skuId),

    listParentSkusWithCompetitorStats: (page = 1, pageSize = 20, search = null) => {
        let url = '/competitors/parent-skus?page=' + page + '&per_page=' + pageSize;
        if (search) url += '&search=' + encodeURIComponent(search);
        return fetchAPI(url);
    },

    // ===== Competitor Exports =====
    getCompetitorExportCsvUrl: (skuId = null) => {
        let url = API_BASE + '/competitors/export/csv';
        if (skuId) url += '?sku_id=' + skuId;
        return url;
    },

    getCompetitorPriceChangerExportUrl: (skuId = null) => {
        let url = API_BASE + '/competitors/export/price-changer';
        if (skuId) url += '?sku_id=' + skuId;
        return url;
    },
};

// Export for use in other scripts
window.api = api;
