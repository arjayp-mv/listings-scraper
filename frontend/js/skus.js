/**
 * =============================================================================
 * Amazon Reviews Scraper - SKUs Page
 * =============================================================================
 */

let currentPage = 1;
const pageSize = 20;
let searchTimeout = null;

document.addEventListener('DOMContentLoaded', () => {
    loadSkus();
});

// Debounced search function
function debouncedSearch() {
    if (searchTimeout) {
        clearTimeout(searchTimeout);
    }
    searchTimeout = setTimeout(() => {
        currentPage = 1; // Reset to first page on search
        loadSkus();
    }, 300);
}

function clearSearch() {
    document.getElementById('sku-search').value = '';
    document.getElementById('clear-search-btn').style.display = 'none';
    currentPage = 1;
    loadSkus();
}

async function loadSkus() {
    const searchValue = document.getElementById('sku-search')?.value?.trim() || null;

    // Show/hide clear button
    const clearBtn = document.getElementById('clear-search-btn');
    if (clearBtn) {
        clearBtn.style.display = searchValue ? 'inline-flex' : 'none';
    }

    try {
        const result = await api.listSkus(currentPage, pageSize, searchValue);
        renderSkus(result.items, searchValue);
        renderPagination(result);
    } catch (error) {
        console.error('Failed to load SKUs:', error);
        document.getElementById('skus-body').innerHTML = `
            <tr>
                <td colspan="5" class="text-danger">Failed to load SKUs: ${escapeHtml(error.message)}</td>
            </tr>
        `;
    }
}

function renderSkus(skus, searchValue = null) {
    const tbody = document.getElementById('skus-body');

    if (!skus || skus.length === 0) {
        const message = searchValue
            ? `No SKUs found matching "${escapeHtml(searchValue)}". <button class="btn btn-secondary btn-sm" onclick="clearSearch()">Clear search</button>`
            : `No SKUs yet. <button class="btn btn-primary btn-sm" onclick="openModal()">Add your first SKU</button>`;
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="empty-state">
                    ${message}
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = skus.map(sku => `
        <tr>
            <td style="font-weight: 500;">
                <a href="sku-reviews.html?id=${sku.id}" style="color: var(--primary); text-decoration: none;">
                    ${escapeHtml(sku.sku_code)}
                </a>
            </td>
            <td>${sku.description ? escapeHtml(sku.description) : '<span class="text-muted">-</span>'}</td>
            <td>
                <a href="jobs.html?sku_id=${sku.id}" style="color: var(--text-muted);">
                    ${sku.job_count} jobs
                </a>
            </td>
            <td>${formatDate(sku.created_at)}</td>
            <td>
                <div class="flex gap-1">
                    <a href="sku-reviews.html?id=${sku.id}" class="btn btn-primary btn-sm">View Reviews</a>
                    <button class="btn btn-secondary btn-sm" onclick="editSku(${sku.id})">Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteSku(${sku.id})">Delete</button>
                </div>
            </td>
        </tr>
    `).join('');
}

function renderPagination(result) {
    const pagination = document.getElementById('pagination');

    if (result.total_pages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    pagination.innerHTML = `
        <button class="pagination-btn" onclick="goToPage(${currentPage - 1})" ${!result.has_previous ? 'disabled' : ''}>
            Previous
        </button>
        <span class="pagination-info">
            Page ${result.page} of ${result.total_pages}
        </span>
        <button class="pagination-btn" onclick="goToPage(${currentPage + 1})" ${!result.has_next ? 'disabled' : ''}>
            Next
        </button>
    `;
}

function goToPage(page) {
    currentPage = page;
    loadSkus();
}

function openModal(sku = null) {
    const modal = document.getElementById('sku-modal');
    const title = document.getElementById('modal-title');
    const form = document.getElementById('sku-form');

    if (sku) {
        title.textContent = 'Edit SKU';
        document.getElementById('sku-id').value = sku.id;
        document.getElementById('sku-code').value = sku.sku_code;
        document.getElementById('sku-description').value = sku.description || '';
    } else {
        title.textContent = 'Add SKU';
        form.reset();
        document.getElementById('sku-id').value = '';
    }

    modal.classList.add('active');
}

function closeModal() {
    document.getElementById('sku-modal').classList.remove('active');
}

async function editSku(id) {
    try {
        const sku = await api.getSku(id);
        openModal(sku);
    } catch (error) {
        showAlert('error', 'Failed to load SKU: ' + error.message);
    }
}

async function saveSku(event) {
    event.preventDefault();

    const id = document.getElementById('sku-id').value;
    const data = {
        sku_code: document.getElementById('sku-code').value.trim(),
        description: document.getElementById('sku-description').value.trim() || null,
    };

    try {
        if (id) {
            await api.updateSku(id, data);
            showAlert('success', 'SKU updated successfully');
        } else {
            await api.createSku(data);
            showAlert('success', 'SKU created successfully');
        }

        closeModal();
        loadSkus();

    } catch (error) {
        showAlert('error', error.message);
    }
}

async function deleteSku(id) {
    if (!confirm('Are you sure you want to delete this SKU? Jobs will be unlinked but not deleted.')) return;

    try {
        await api.deleteSku(id);
        showAlert('success', 'SKU deleted successfully');
        loadSkus();
    } catch (error) {
        showAlert('error', 'Failed to delete SKU: ' + error.message);
    }
}

function showAlert(type, message) {
    const container = document.getElementById('alert-container');
    container.innerHTML = `
        <div class="alert alert-${type}">
            ${escapeHtml(message)}
        </div>
    `;

    // Auto-hide after 3 seconds
    setTimeout(() => {
        container.innerHTML = '';
    }, 3000);
}

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Close modal when clicking outside
document.getElementById('sku-modal').addEventListener('click', (e) => {
    if (e.target.id === 'sku-modal') {
        closeModal();
    }
});
