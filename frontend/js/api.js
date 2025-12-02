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
    const url = `${API_BASE}${endpoint}`;

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
            throw new Error(data.detail || 'API request failed');
        }

        return data;
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
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
        let url = `/skus?page=${page}&page_size=${pageSize}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        return fetchAPI(url);
    },

    searchSkus: (query) =>
        fetchAPI(`/skus/search?q=${encodeURIComponent(query)}`),

    createSku: (data) =>
        fetchAPI('/skus', {
            method: 'POST',
            body: JSON.stringify(data),
        }),

    getSku: (id) => fetchAPI(`/skus/${id}`),

    updateSku: (id, data) =>
        fetchAPI(`/skus/${id}`, {
            method: 'PUT',
            body: JSON.stringify(data),
        }),

    deleteSku: (id) =>
        fetchAPI(`/skus/${id}`, { method: 'DELETE' }),

    // ===== Jobs =====
    listJobs: (page = 1, pageSize = 20, status = null, skuId = null) => {
        let url = `/jobs?page=${page}&page_size=${pageSize}`;
        if (status) url += `&status=${status}`;
        if (skuId) url += `&sku_id=${skuId}`;
        return fetchAPI(url);
    },

    createJob: (data) =>
        fetchAPI('/jobs', {
            method: 'POST',
            body: JSON.stringify(data),
        }),

    getJob: (id) => fetchAPI(`/jobs/${id}`),

    deleteJob: (id) =>
        fetchAPI(`/jobs/${id}`, { method: 'DELETE' }),

    cancelJob: (id) =>
        fetchAPI(`/jobs/${id}/cancel`, { method: 'POST' }),

    retryFailedAsins: (id) =>
        fetchAPI(`/jobs/${id}/retry-failed`, { method: 'POST' }),

    checkAsinHistory: (asins, marketplace) =>
        fetchAPI('/jobs/check-history', {
            method: 'POST',
            body: JSON.stringify({ asins, marketplace }),
        }),

    // ===== Reviews =====
    listReviews: (jobId, page = 1, pageSize = 20, search = null, rating = null, asin = null) => {
        let url = `/jobs/${jobId}/reviews?page=${page}&page_size=${pageSize}`;
        if (search) url += `&search=${encodeURIComponent(search)}`;
        if (rating) url += `&rating=${encodeURIComponent(rating)}`;
        if (asin) url += `&asin=${encodeURIComponent(asin)}`;
        return fetchAPI(url);
    },

    getFormattedReviews: (jobId, search = null, rating = null) => {
        let url = `/jobs/${jobId}/reviews/formatted`;
        const params = [];
        if (search) params.push(`search=${encodeURIComponent(search)}`);
        if (rating) params.push(`rating=${encodeURIComponent(rating)}`);
        if (params.length) url += `?${params.join('&')}`;
        return fetchAPI(url);
    },

    getReviewStats: (jobId) => fetchAPI(`/jobs/${jobId}/reviews/stats`),

    exportReviewsJson: (jobId) => fetchAPI(`/jobs/${jobId}/reviews/export/json`),

    getExcelExportUrl: (jobId) => `${API_BASE}/jobs/${jobId}/reviews/export/excel`,
};

// Export for use in other scripts
window.api = api;
