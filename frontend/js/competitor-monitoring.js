/**
 * =============================================================================
 * Amazon Reviews Scraper - Competitor Monitoring Page
 * =============================================================================
 */

let scheduledPage = 1;
let jobsPage = 1;
const pageSize = 20;
let currentScheduleFilter = '';
let currentJobStatusFilter = '';

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
    tbody.innerHTML = '<tr><td colspan="8" class="loading"><div class="spinner"></div> Loading...</td></tr>';

    try {
        // Get all scheduled competitors with data to show last scraped date
        const result = await api.listCompetitors(scheduledPage, pageSize, null, null, null, true);
        const scheduled = (result.items || []).filter(c => c.schedule && c.schedule !== 'none');

        renderScheduledCompetitors(scheduled);
        renderPagination('scheduled', result.total || 0, result.page || 1, result.per_page || pageSize);
    } catch (error) {
        console.error('Failed to load scheduled competitors:', error);
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state">Failed to load data</td></tr>';
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
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state">No scheduled competitors found</td></tr>';
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

async function editSchedule(id, currentSchedule) {
    const schedules = [
        { value: '', label: 'None (Manual)' },
        { value: 'daily', label: 'Daily' },
        { value: 'every_2_days', label: 'Every 2 Days' },
        { value: 'every_3_days', label: 'Every 3 Days' },
        { value: 'weekly', label: 'Weekly' },
        { value: 'monthly', label: 'Monthly' }
    ];

    const options = schedules.map(s =>
        (s.value === currentSchedule ? '> ' : '  ') + s.label
    ).join('\n');

    const newSchedule = prompt('Select new schedule:\n\n' + options + '\n\nEnter: daily, every_2_days, every_3_days, weekly, monthly, or leave empty for manual:', currentSchedule);

    if (newSchedule === null) return; // Cancelled

    const validSchedules = ['', 'daily', 'every_2_days', 'every_3_days', 'weekly', 'monthly'];
    if (!validSchedules.includes(newSchedule)) {
        alert('Invalid schedule. Please enter one of: daily, every_2_days, every_3_days, weekly, monthly, or leave empty.');
        return;
    }

    try {
        await api.updateCompetitorSchedule(id, {
            schedule: newSchedule || 'none'
        });
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

    const goFunc = type === 'scheduled' ? 'goToScheduledPage' : 'goToJobsPage';

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

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
