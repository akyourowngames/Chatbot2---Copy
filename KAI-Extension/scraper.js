/**
 * KAI Extension - Web Scraper Module
 * ===================================
 * Intelligent data extraction from web pages
 */

class WebScraper {
    constructor() {
        this.results = [];
    }

    /**
     * Extract all tables from the page
     */
    extractTables() {
        const tables = [];
        document.querySelectorAll('table').forEach((table, index) => {
            if (!this.isVisible(table)) return;

            const data = [];
            const headers = [];

            // Extract headers
            table.querySelectorAll('thead th, thead td').forEach(th => {
                headers.push(th.textContent.trim());
            });

            // If no thead, try first row
            if (headers.length === 0) {
                const firstRow = table.querySelector('tr');
                if (firstRow) {
                    firstRow.querySelectorAll('th, td').forEach(cell => {
                        headers.push(cell.textContent.trim());
                    });
                }
            }

            // Extract rows
            table.querySelectorAll('tbody tr, tr').forEach(row => {
                const rowData = {};
                row.querySelectorAll('td, th').forEach((cell, colIndex) => {
                    const header = headers[colIndex] || `Column ${colIndex + 1}`;
                    rowData[header] = cell.textContent.trim();
                });
                if (Object.keys(rowData).length > 0) {
                    data.push(rowData);
                }
            });

            if (data.length > 0) {
                tables.push({
                    index,
                    headers,
                    rows: data,
                    rowCount: data.length
                });
            }
        });

        return tables;
    }

    /**
     * Extract structured lists
     */
    extractLists() {
        const lists = [];

        document.querySelectorAll('ul, ol').forEach((list, index) => {
            if (!this.isVisible(list)) return;

            const items = [];
            list.querySelectorAll('li').forEach(li => {
                const text = li.textContent.trim();
                if (text) items.push(text);
            });

            if (items.length > 0) {
                lists.push({
                    type: list.tagName.toLowerCase(),
                    index,
                    items,
                    count: items.length
                });
            }
        });

        return lists;
    }

    /**
     * Extract all links
     */
    extractLinks() {
        const links = [];
        const seen = new Set();

        document.querySelectorAll('a[href]').forEach(a => {
            const href = a.href;
            if (href && !seen.has(href) && this.isVisible(a)) {
                seen.add(href);
                links.push({
                    text: a.textContent.trim() || 'no text',
                    url: href,
                    domain: new URL(href).hostname
                });
            }
        });

        return links;
    }

    /**
     * Extract images
     */
    extractImages() {
        const images = [];

        document.querySelectorAll('img[src]').forEach(img => {
            if (!this.isVisible(img)) return;
            images.push({
                src: img.src,
                alt: img.alt || '',
                width: img.naturalWidth,
                height: img.naturalHeight
            });
        });

        return images;
    }

    /**
     * Extract emails
     */
    extractEmails() {
        const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
        const text = document.body.textContent;
        const emails = [...new Set(text.match(emailRegex) || [])];
        return emails;
    }

    /**
     * Extract phone numbers
     */
    extractPhones() {
        const phoneRegex = /(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}/g;
        const text = document.body.textContent;
        const phones = [...new Set(text.match(phoneRegex) || [])];
        return phones;
    }

    /**
     * Extract product information (e-commerce)
     */
    extractProducts() {
        const products = [];

        // Try common e-commerce selectors
        const productSelectors = [
            '.product', '[data-product]',
            '.product-item', '.item',
            '[itemtype*="Product"]'
        ];

        productSelectors.forEach(selector => {
            document.querySelectorAll(selector).forEach(el => {
                const product = {
                    name: this.extractText(el, ['h1', 'h2', 'h3', '.title', '.name', '[itemprop="name"]']),
                    price: this.extractText(el, ['.price', '[itemprop="price"]', '.amount']),
                    image: this.extractImage(el),
                    link: this.extractLink(el)
                };

                if (product.name || product.price) {
                    products.push(product);
                }
            });
        });

        return products;
    }

    /**
     * Convert data to CSV
     */
    toCSV(data) {
        if (!Array.isArray(data) || data.length === 0) return '';

        const headers = Object.keys(data[0]);
        const rows = data.map(row =>
            headers.map(header => {
                const value = row[header] || '';
                // Escape quotes and wrap in quotes if contains comma
                return value.includes(',') || value.includes('"')
                    ? `"${value.replace(/"/g, '""')}"`
                    : value;
            }).join(',')
        );

        return [headers.join(','), ...rows].join('\n');
    }

    /**
     * Download extracted data
     */
    download(data, filename, format = 'json') {
        let content, mimeType;

        if (format === 'csv') {
            content = this.toCSV(data);
            mimeType = 'text/csv';
            filename += '.csv';
        } else {
            content = JSON.stringify(data, null, 2);
            mimeType = 'application/json';
            filename += '.json';
        }

        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }

    // Helper methods

    isVisible(el) {
        if (!el) return false;
        const style = window.getComputedStyle(el);
        return style.display !== 'none' && style.visibility !== 'hidden'
            && el.offsetWidth > 0 && el.offsetHeight > 0;
    }

    extractText(parent, selectors) {
        for (const sel of selectors) {
            const el = parent.querySelector(sel);
            if (el) return el.textContent.trim();
        }
        return '';
    }

    extractImage(parent) {
        const img = parent.querySelector('img[src]');
        return img ? img.src : '';
    }

    extractLink(parent) {
        const a = parent.querySelector('a[href]');
        return a ? a.href : '';
    }
}

// Global instance
window.kaiScraper = new WebScraper();
