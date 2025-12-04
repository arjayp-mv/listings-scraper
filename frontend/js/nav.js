/**
 * Shared Navigation Component
 * Generates the header navigation dynamically so changes only need to be made in one place.
 */

(function() {
    // Navigation structure
    const navConfig = {
        logo: {
            text: 'Amazon Reviews Scraper',
            href: 'index.html'
        },
        items: [
            {
                type: 'link',
                text: 'Dashboard',
                href: 'index.html',
                pages: ['index.html']
            },
            {
                type: 'dropdown',
                text: 'Product Reviews',
                pages: ['new-scrape.html', 'jobs.html', 'job-detail.html', 'skus.html', 'sku-reviews.html'],
                items: [
                    { text: 'New Scrape', href: 'new-scrape.html' },
                    { text: 'Jobs', href: 'jobs.html' },
                    { text: 'SKU Reviews', href: 'skus.html' }
                ]
            },
            {
                type: 'dropdown',
                text: 'Channel SKU Metrics',
                pages: ['new-scan.html', 'scans.html', 'scan-detail.html', 'listings.html', 'skus-list.html', 'sku-detail.html'],
                items: [
                    { text: 'New Scan', href: 'new-scan.html' },
                    { text: 'Scan History', href: 'scans.html' },
                    { text: 'All Listings', href: 'listings.html' },
                    { text: 'Parent SKUs', href: 'skus-list.html' }
                ]
            },
            {
                type: 'dropdown',
                text: 'Competitor Research',
                pages: ['competitor-dashboard.html', 'competitor-parent-skus.html', 'competitor-parent-sku-detail.html', 'competitor-detail.html', 'competitor-keywords.html', 'competitor-monitoring.html'],
                items: [
                    { text: 'Dashboard', href: 'competitor-dashboard.html' },
                    { text: 'Parent SKUs', href: 'competitor-parent-skus.html' },
                    { text: 'Keywords', href: 'competitor-keywords.html' },
                    { text: 'Monitoring', href: 'competitor-monitoring.html' }
                ]
            }
        ]
    };

    // Get current page filename
    function getCurrentPage() {
        const path = window.location.pathname;
        const page = path.substring(path.lastIndexOf('/') + 1) || 'index.html';
        return page;
    }

    // Check if current page is in a list of pages
    function isActivePage(pages) {
        const currentPage = getCurrentPage();
        return pages.includes(currentPage);
    }

    // Generate dropdown arrow SVG
    function getDropdownArrow() {
        return `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"></polyline>
        </svg>`;
    }

    // Generate navigation HTML
    function generateNavHTML() {
        const currentPage = getCurrentPage();

        let navHTML = '';

        for (const item of navConfig.items) {
            if (item.type === 'link') {
                const isActive = isActivePage(item.pages);
                navHTML += `<a href="${item.href}"${isActive ? ' class="active"' : ''}>${item.text}</a>`;
            } else if (item.type === 'dropdown') {
                const isActive = isActivePage(item.pages);
                navHTML += `
                    <div class="nav-dropdown">
                        <a href="#" class="nav-dropdown-trigger${isActive ? ' active' : ''}">
                            ${item.text}
                            ${getDropdownArrow()}
                        </a>
                        <div class="nav-dropdown-menu">
                            ${item.items.map(subItem => `<a href="${subItem.href}">${subItem.text}</a>`).join('')}
                        </div>
                    </div>
                `;
            }
        }

        return navHTML;
    }

    // Generate full header HTML
    function generateHeaderHTML() {
        return `
            <div class="container header-content">
                <a href="${navConfig.logo.href}" class="logo">${navConfig.logo.text}</a>
                <nav class="nav">
                    ${generateNavHTML()}
                </nav>
            </div>
        `;
    }

    // Initialize navigation
    function initNav() {
        const header = document.querySelector('header.header');
        if (header) {
            header.innerHTML = generateHeaderHTML();
        }
    }

    // Run when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initNav);
    } else {
        initNav();
    }
})();
