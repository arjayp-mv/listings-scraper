/**
 * =============================================================================
 * Amazon Reviews Scraper - New Scrape Page
 * =============================================================================
 */

document.addEventListener('DOMContentLoaded', () => {
    initForm();
});

function initForm() {
    const form = document.getElementById('scrape-form');
    const maxPagesSlider = document.getElementById('max-pages');
    const asinsInput = document.getElementById('asins');
    const marketplaceSelect = document.getElementById('marketplace');

    // Update max pages display
    maxPagesSlider.addEventListener('input', () => {
        const value = maxPagesSlider.value;
        document.getElementById('max-pages-value').textContent = value;
        document.getElementById('reviews-estimate').textContent = value * 10;
    });

    // Check ASIN history on blur
    asinsInput.addEventListener('blur', () => {
        checkAsinHistory();
    });

    marketplaceSelect.addEventListener('change', () => {
        checkAsinHistory();
    });

    // Form submission
    form.addEventListener('submit', handleSubmit);
}

async function checkAsinHistory() {
    const asinsText = document.getElementById('asins').value;
    const marketplace = document.getElementById('marketplace').value;
    const warningsDiv = document.getElementById('asin-warnings');

    const asins = parseAsins(asinsText);
    if (asins.length === 0) {
        warningsDiv.innerHTML = '';
        return;
    }

    try {
        const result = await api.checkAsinHistory(asins, marketplace);
        const previouslyScraped = result.results.filter(r => r.previously_scraped);

        if (previouslyScraped.length > 0) {
            warningsDiv.innerHTML = `
                <div class="alert alert-warning">
                    <strong>Note:</strong> ${previouslyScraped.length} ASIN(s) have been scraped before:
                    <ul style="margin: 8px 0 0 20px;">
                        ${previouslyScraped.map(r => `
                            <li>${r.asin} - Last scraped: ${new Date(r.last_scraped_at).toLocaleDateString()}</li>
                        `).join('')}
                    </ul>
                </div>
            `;
        } else {
            warningsDiv.innerHTML = '';
        }
    } catch (error) {
        console.error('Failed to check ASIN history:', error);
    }
}

function parseAsins(text) {
    // Split by newlines, commas, or spaces
    return text
        .split(/[\n,\s]+/)
        .map(s => s.trim().toUpperCase())
        .filter(s => s.length > 0);
}

async function handleSubmit(event) {
    event.preventDefault();

    const alertContainer = document.getElementById('alert-container');
    const submitBtn = document.getElementById('submit-btn');

    // Gather form data
    const jobName = document.getElementById('job-name').value.trim();
    const skuCode = document.getElementById('sku-code').value.trim();
    const asinsText = document.getElementById('asins').value;
    const marketplace = document.getElementById('marketplace').value;
    const sortBy = document.getElementById('sort-by').value;
    const maxPages = parseInt(document.getElementById('max-pages').value);
    const keywordFilter = document.getElementById('keyword-filter').value.trim();
    const reviewerType = document.getElementById('reviewer-type').value;

    // Get star filters
    const starCheckboxes = document.querySelectorAll('input[name="stars"]:checked');
    const starFilters = Array.from(starCheckboxes).map(cb => cb.value);

    // Validate
    const asins = parseAsins(asinsText);
    if (asins.length === 0) {
        showAlert('error', 'Please enter at least one ASIN');
        return;
    }

    if (starFilters.length === 0) {
        showAlert('error', 'Please select at least one star rating');
        return;
    }

    // Build request data
    const data = {
        job_name: jobName,
        asins: asins,
        marketplace: marketplace,
        sort_by: sortBy,
        max_pages: maxPages,
        star_filters: starFilters,
        reviewer_type: reviewerType,
    };

    if (skuCode) {
        data.sku_code = skuCode;
    }

    if (keywordFilter) {
        data.keyword_filter = keywordFilter;
    }

    // Submit
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating Job...';

    try {
        const job = await api.createJob(data);
        showAlert('success', `Job "${job.job_name}" created successfully! Redirecting...`);

        // Redirect to job detail
        setTimeout(() => {
            window.location.href = `job-detail.html?id=${job.id}`;
        }, 1500);

    } catch (error) {
        showAlert('error', error.message);
        submitBtn.disabled = false;
        submitBtn.textContent = 'Start Scraping';
    }
}

function showAlert(type, message) {
    const alertContainer = document.getElementById('alert-container');
    alertContainer.innerHTML = `
        <div class="alert alert-${type}">
            ${escapeHtml(message)}
        </div>
    `;
    alertContainer.scrollIntoView({ behavior: 'smooth' });
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
