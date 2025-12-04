/**
 * =============================================================================
 * Amazon Reviews Scraper - Competitor Monitoring Page
 * =============================================================================
 */

let scheduledPage = 1;
let jobsPage = 1;
let unscheduledPage = 1;
const pageSize = 20;
let currentScheduleFilter = '';
let currentJobStatusFilter = '';
let currentAddSkuFilter = '';
let currentSearchQuery = '';
let searchDebounceTimer = null;
let scheduleModalIds = [];  // Competitor IDs for modal

document.addEventListener('DOMContentLoaded', () => {
    loadStats();
    loadScheduledCompetitors();
    setupEventListeners();

    // Auto-refresh every 30 seconds
    setInterval(() => {
        loadStats();
        if (document.querySelector('#tab-jobs.active')) {
            loadJobs();
        }
    }, 30000);
});

function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            switchTab(btn.dataset.tab);
        });
    });

    // Schedule filter
    document.getElementById('schedule-filter').addEventListener('change', (e) => {
        currentScheduleFilter = e.target.value;
        scheduledPage = 1;
        loadScheduledCompetitors();
    });

    // Job status filter
    document.getElementById('job-status-filter').addEventListener('change', (e) => {
        currentJobStatusFilter = e.target.value;
        jobsPage = 1;
        loadJobs();
    });

    // Scrape all button
    document.getElementById('scrape-all-btn').addEventListener('click', scrapeAllScheduled);

    // Bulk schedule button
    document.getElementById('bulk-schedule-btn').addEventListener('click', bulkSetSchedule);

    // Apply schedule button
    document.getElementById('apply-schedule-btn').addEventListener('click', applyScheduleToSelected);

    // Schedule modal save button
    document.getElementById('schedule-modal-save').addEventListener('click', saveScheduleModal);
}

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === 'tab-' + tab);
    });

    if (tab === 'jobs') {
        loadJobs();
    } else if (tab === 'add') {
        setupSearchInput();
        loadUnscheduledCompetitors();
    } else {
        loadScheduledCompetitors();
    }
}

async function loadStats() {
    try {
        const stats = await api.getCompetitorDashboardStats();

        document.getElementById('stat-scheduled').textContent = stats.scheduled_count || 0;
        document.getElementById('stat-due').textContent = stats.due_for_scrape || 0;
        document.getElementById('stat-jobs-running').textContent = stats.jobs_running || 0;
        document.getElementById('stat-jobs-queued').textContent = stats.jobs_queued || 0;
    } catch (error) {
        console.error('Failed to load stats:', error);
    }
}

async function loadScheduledCompetitors() {
    const tbody = document.getElementById('scheduled-body');
    tbody.innerHTML = '<tr><td colspan="9" class="loading"><div class="spinner"></div> Loading...</td></tr>';

    try {
        // Get all scheduled competitors with data to show last scraped date
        const result = await api.listCompetitors(scheduledPage, pageSize, null, null, null, true);
        const scheduled = (result.items || []).filter(c => c.schedule && c.schedule !== 'none');

        renderScheduledCompetitors(scheduled);
        renderPagination('scheduled', result.total || 0, result.page || 1, result.per_page || pageSize);
    } catch (error) {
        console.error('Failed to load scheduled competitors:', error);
        tbody.innerHTML = '<tr><td colspan="9" class="empty-state">Failed to load data</td></tr>';
    }
}

function renderScheduledCompetitors(competitors) {
    const tbody = document.getElementById('scheduled-body');

    // Filter by schedule if filter is set
    let filtered = competitors;
    if (currentScheduleFilter) {
        filtered = competitors.filter(c => c.schedule === currentScheduleFilter);
    }

    if (!filtered || filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="empty-state">No scheduled competitors found</td></tr>';
        return;
    }

    const now = new Date();
    let html = '';

    for (const comp of filtered) {
        const nextScrape = comp.next_scrape_at ? new Date(comp.next_scrape_at) : null;
        const isDue = nextScrape && nextScrape <= now;
        const statusClass = isDue ? 'pending' : 'completed';
        const statusText = isDue ? 'Due' : 'Scheduled';

        html += '<tr>' +
            '<td>' +
                '<input type="checkbox" class="scheduled-checkbox" data-competitor-id="' + comp.id + '" onchange="updateSelectedCount()">' +
            '</td>' +
            '<td>' +
                '<a href="competitor-detail.html?id=' + comp.id + '" class="text-link font-medium">' +
                    escapeHtml(comp.asin) +
                '</a>' +
            '</td>' +
            '<td>' + escapeHtml(comp.sku_code || '-') + '</td>' +
            '<td>amazon.' + comp.marketplace + '</td>' +
            '<td>' + formatSchedule(comp.schedule) + '</td>' +
            '<td>' + formatDateTime(comp.data?.scraped_at) + '</td>' +
            '<td>' + formatDateTime(comp.next_scrape_at) + '</td>' +
            '<td><span class="status-badge ' + statusClass + '">' + statusText + '</span></td>' +
            '<td>' +
                '<button class="btn btn-secondary btn-sm" onclick="scrapeCompetitor(' + comp.id + ')">Scrape Now</button> ' +
                '<button class="btn btn-secondary btn-sm" onclick="editSchedule(' + comp.id + ', \'' + (comp.schedule || '') + '\')">Edit</button>' +
            '</td>' +
        '</tr>';
    }
    tbody.innerHTML = html;
    // Reset select-all checkbox
    document.getElementById('select-all-scheduled').checked = false;
    updateSelectedCount();
}

async function loadJobs() {
    const tbody = document.getElementById('jobs-body');
    tbody.innerHTML = '<tr><td colspan="6" class="loading"><div class="spinner"></div> Loading...</td></tr>';

    try {
        const result = await api.listCompetitorScrapeJobs(jobsPage, pageSize, currentJobStatusFilter || null);
        renderJobs(result.items || []);
        renderPagination('jobs', result.total || 0, result.page || 1, result.per_page || pageSize);
    } catch (error) {
        console.error('Failed to load jobs:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Failed to load data</td></tr>';
    }
}

function renderJobs(jobs) {
    const tbody = document.getElementById('jobs-body');

    if (!jobs || jobs.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No jobs found</td></tr>';
        return;
    }

    let html = '';
    for (const job of jobs) {
        html += '<tr>' +
            '<td class="font-medium">' + escapeHtml(job.job_name || 'Unnamed Job') + '</td>' +
            '<td>' + formatJobType(job.job_type) + '</td>' +
            '<td><span class="status-badge ' + getStatusClass(job.status) + '">' + formatStatus(job.status) + '</span></td>' +
            '<td>' + (job.completed_competitors || 0) + ' / ' + (job.total_competitors || 0) + '</td>' +
            '<td>' + formatDateTime(job.created_at) + '</td>' +
            '<td>' + formatDateTime(job.completed_at) + '</td>' +
        '</tr>';
    }
    tbody.innerHTML = html;
}

async function scrapeAllScheduled() {
    if (!confirm('Start scraping all scheduled competitors that are due?')) {
        return;
    }

    try {
        await api.createCompetitorScrapeJob({
            job_name: 'Scheduled Scrape - ' + new Date().toLocaleDateString(),
            job_type: 'scheduled'
        });
        alert('Scheduled scrape job created');
        loadStats();
    } catch (error) {
        console.error('Failed to create scrape job:', error);
        alert('Failed to create scrape job: ' + error.message);
    }
}

async function scrapeCompetitor(id) {
    try {
        await api.createCompetitorScrapeJob({
            job_name: 'Manual Scrape - Competitor ' + id,
            competitor_ids: [id],
            job_type: 'manual'
        });
        alert('Scrape job created');
        loadStats();
    } catch (error) {
        console.error('Failed to create scrape job:', error);
        alert('Failed to create scrape job: ' + error.message);
    }
}

function editSchedule(id, currentSchedule) {
    openScheduleModal([id], currentSchedule, 'Edit Schedule');
}

// ===== Schedule Modal Functions =====

function openScheduleModal(ids, currentSchedule, title) {
    scheduleModalIds = ids;
    document.getElementById('schedule-modal-title').textContent = title || 'Set Schedule';
    document.getElementById('schedule-modal-select').value = currentSchedule || '';
    document.getElementById('schedule-modal').classList.add('active');
}

function closeScheduleModal() {
    document.getElementById('schedule-modal').classList.remove('active');
    scheduleModalIds = [];
}

async function saveScheduleModal() {
    const schedule = document.getElementById('schedule-modal-select').value;

    try {
        for (const id of scheduleModalIds) {
            await api.updateCompetitorSchedule(id, { schedule: schedule || 'none' });
        }
        closeScheduleModal();
        loadScheduledCompetitors();
        loadStats();
    } catch (error) {
        console.error('Failed to update schedule:', error);
        alert('Failed to update schedule: ' + error.message);
    }
}

function renderPagination(type, total, page, size) {
    const pagination = document.getElementById(type + '-pagination');
    const totalPages = Math.ceil(total / size);

    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    const goFuncs = {
        scheduled: 'goToScheduledPage',
        jobs: 'goToJobsPage',
        unscheduled: 'goToUnscheduledPage'
    };
    const goFunc = goFuncs[type] || 'goToScheduledPage';

    let html = '';
    if (page > 1) {
        html += '<button class="btn btn-secondary btn-sm" onclick="' + goFunc + '(' + (page - 1) + ')">Previous</button>';
    }
    html += '<span class="pagination-info">Page ' + page + ' of ' + totalPages + '</span>';
    if (page < totalPages) {
        html += '<button class="btn btn-secondary btn-sm" onclick="' + goFunc + '(' + (page + 1) + ')">Next</button>';
    }
    pagination.innerHTML = html;
}

function goToScheduledPage(page) {
    scheduledPage = page;
    loadScheduledCompetitors();
}

function goToJobsPage(page) {
    jobsPage = page;
    loadJobs();
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

function formatJobType(type) {
    const types = {
        manual: 'Manual',
        scheduled: 'Scheduled',
        keyword_research: 'Keyword Research'
    };
    return types[type] || type;
}

function getStatusClass(status) {
    const classes = {
        queued: 'pending',
        running: 'running',
        completed: 'completed',
        failed: 'failed'
    };
    return classes[status] || 'pending';
}

function formatStatus(status) {
    return status.charAt(0).toUpperCase() + status.slice(1);
}

function formatDateTime(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// ===== Selection Functions =====

function toggleSelectAll(checkbox) {
    document.querySelectorAll('.scheduled-checkbox').forEach(cb => {
        cb.checked = checkbox.checked;
    });
    updateSelectedCount();
}

function updateSelectedCount() {
    const checkboxes = document.querySelectorAll('.scheduled-checkbox:checked');
    const count = checkboxes.length;
    document.getElementById('selected-count').textContent = count;
    document.getElementById('bulk-schedule-btn').style.display = count > 0 ? 'inline-flex' : 'none';
}

function bulkSetSchedule() {
    const checkboxes = document.querySelectorAll('.scheduled-checkbox:checked');
    const ids = Array.from(checkboxes).map(cb => parseInt(cb.dataset.competitorId));

    if (ids.length === 0) {
        alert('Please select at least one competitor');
        return;
    }

    openScheduleModal(ids, '', 'Set Schedule for ' + ids.length + ' competitor(s)');
}

// ===== Add to Schedule Tab Functions =====

function setupSearchInput() {
    const input = document.getElementById('add-search-filter');
    const suggestions = document.getElementById('search-suggestions');

    // Only setup once
    if (input.dataset.initialized) return;
    input.dataset.initialized = 'true';

    input.addEventListener('input', (e) => {
        const query = e.target.value.trim();

        // Clear previous timer
        if (searchDebounceTimer) {
            clearTimeout(searchDebounceTimer);
        }

        if (query.length < 2) {
            suggestions.classList.remove('show');
            // If cleared, reset to show all
            if (query.length === 0) {
                currentSearchQuery = '';
                currentAddSkuFilter = '';
                unscheduledPage = 1;
                loadUnscheduledCompetitors();
            }
            return;
        }

        // Debounce search - wait 300ms after typing stops
        searchDebounceTimer = setTimeout(() => {
            searchForSuggestions(query);
        }, 300);
    });

    // Hide suggestions when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.form-group')) {
            suggestions.classList.remove('show');
        }
    });
}

async function searchForSuggestions(query) {
    const suggestions = document.getElementById('search-suggestions');

    try {
        // Search competitors by ASIN or title (in parallel)
        const [competitorResult, skuResult] = await Promise.all([
            api.listCompetitors(1, 5, null, null, query, false),
            api.listParentSkusWithCompetitorStats(1, 5, query)
        ]);

        let html = '';

        // Add SKU suggestions
        const skus = skuResult.items || [];
        if (skus.length > 0) {
            html += '<div class="search-suggestion-header">Parent SKUs</div>';
            for (const sku of skus) {
                html += '<div class="search-suggestion" data-type="sku" data-id="' + sku.sku_id + '" data-label="' + escapeHtml(sku.sku_code) + '">' +
                    '<div class="suggestion-primary">' + escapeHtml(sku.sku_code) + '</div>' +
                    '<div class="suggestion-secondary">' + (sku.total_competitors || 0) + ' competitors</div>' +
                '</div>';
            }
        }

        // Add ASIN suggestions (competitors that match)
        const competitors = competitorResult.items || [];
        if (competitors.length > 0) {
            html += '<div class="search-suggestion-header">ASINs</div>';
            for (const comp of competitors) {
                html += '<div class="search-suggestion" data-type="asin" data-asin="' + comp.asin + '" data-label="' + escapeHtml(comp.asin) + '">' +
                    '<div class="suggestion-primary">' + escapeHtml(comp.asin) + '</div>' +
                    '<div class="suggestion-secondary">' + escapeHtml(comp.sku_code || 'No SKU') + ' - amazon.' + comp.marketplace + '</div>' +
                '</div>';
            }
        }

        // Add "Search all" option
        html += '<div class="search-suggestion search-all" data-type="search" data-query="' + escapeHtml(query) + '">' +
            '<div class="suggestion-primary">Search all for "' + escapeHtml(query) + '"</div>' +
        '</div>';

        suggestions.innerHTML = html;
        suggestions.classList.add('show');

        // Add click handlers
        suggestions.querySelectorAll('.search-suggestion').forEach(el => {
            el.addEventListener('click', () => selectSuggestion(el));
        });
    } catch (error) {
        console.error('Search error:', error);
    }
}

function selectSuggestion(el) {
    const type = el.dataset.type;
    const input = document.getElementById('add-search-filter');
    const suggestions = document.getElementById('search-suggestions');

    suggestions.classList.remove('show');

    if (type === 'sku') {
        // Filter by SKU ID
        currentAddSkuFilter = el.dataset.id;
        currentSearchQuery = '';
        input.value = el.dataset.label;
    } else if (type === 'asin') {
        // Search by specific ASIN
        currentAddSkuFilter = '';
        currentSearchQuery = el.dataset.asin;
        input.value = el.dataset.label;
    } else if (type === 'search') {
        // Free text search
        currentAddSkuFilter = '';
        currentSearchQuery = el.dataset.query;
        input.value = el.dataset.query;
    }

    unscheduledPage = 1;
    loadUnscheduledCompetitors();
}

async function loadUnscheduledCompetitors() {
    const tbody = document.getElementById('unscheduled-body');
    tbody.innerHTML = '<tr><td colspan="6" class="loading"><div class="spinner"></div> Loading...</td></tr>';

    try {
        // Get competitors without schedule
        const skuId = currentAddSkuFilter ? parseInt(currentAddSkuFilter) : null;
        const search = currentSearchQuery || null;
        const result = await api.listCompetitors(unscheduledPage, pageSize, skuId, null, search, true);

        // Filter to only show unscheduled (no schedule or schedule = 'none')
        const unscheduled = (result.items || []).filter(c => !c.schedule || c.schedule === 'none');

        renderUnscheduledCompetitors(unscheduled);
        renderPagination('unscheduled', result.total || 0, result.page || 1, result.per_page || pageSize);
    } catch (error) {
        console.error('Failed to load unscheduled competitors:', error);
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">Failed to load data</td></tr>';
    }
}

function renderUnscheduledCompetitors(competitors) {
    const tbody = document.getElementById('unscheduled-body');

    if (!competitors || competitors.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty-state">No unscheduled competitors found</td></tr>';
        return;
    }

    let html = '';
    for (const comp of competitors) {
        const data = comp.data || {};
        html += '<tr>' +
            '<td>' +
                '<input type="checkbox" class="unscheduled-checkbox" data-competitor-id="' + comp.id + '" onchange="updateAddSelectedCount()">' +
            '</td>' +
            '<td>' +
                '<a href="competitor-detail.html?id=' + comp.id + '" class="text-link font-medium">' +
                    escapeHtml(comp.asin) +
                '</a>' +
            '</td>' +
            '<td class="text-truncate" style="max-width: 200px;" title="' + escapeHtml(data.title || '') + '">' +
                escapeHtml(data.title || '-') +
            '</td>' +
            '<td>' + escapeHtml(comp.sku_code || '-') + '</td>' +
            '<td>amazon.' + comp.marketplace + '</td>' +
            '<td>' + formatDateTime(data.scraped_at) + '</td>' +
        '</tr>';
    }
    tbody.innerHTML = html;
    // Reset select-all checkbox
    document.getElementById('select-all-unscheduled').checked = false;
    updateAddSelectedCount();
}

function toggleSelectAllUnscheduled(checkbox) {
    document.querySelectorAll('.unscheduled-checkbox').forEach(cb => {
        cb.checked = checkbox.checked;
    });
    updateAddSelectedCount();
}

function updateAddSelectedCount() {
    const checkboxes = document.querySelectorAll('.unscheduled-checkbox:checked');
    const count = checkboxes.length;
    document.getElementById('add-selected-count').textContent = count;
    document.getElementById('apply-schedule-btn').disabled = count === 0;
}

async function applyScheduleToSelected() {
    const checkboxes = document.querySelectorAll('.unscheduled-checkbox:checked');
    const ids = Array.from(checkboxes).map(cb => parseInt(cb.dataset.competitorId));

    if (ids.length === 0) {
        alert('Please select at least one competitor');
        return;
    }

    const schedule = document.getElementById('add-schedule-select').value;

    try {
        // Update each selected competitor
        for (const id of ids) {
            await api.updateCompetitorSchedule(id, { schedule: schedule });
        }
        alert('Added ' + ids.length + ' competitor(s) to ' + formatSchedule(schedule) + ' schedule');
        loadUnscheduledCompetitors();
        loadScheduledCompetitors();  // Auto-refresh scheduled tab
        loadStats();
    } catch (error) {
        console.error('Failed to apply schedule:', error);
        alert('Failed to apply schedule: ' + error.message);
    }
}

function goToUnscheduledPage(page) {
    unscheduledPage = page;
    loadUnscheduledCompetitors();
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
