/**
 * Universal Quick Search Component for JARVIS
 * Keyboard shortcut: Ctrl+Space
 */

class QuickSearch {
    constructor() {
        this.API_URL = 'http://localhost:5000/api/v1';
        this.API_KEY = 'demo_key_12345';
        this.isOpen = false;
        this.selectedIndex = 0;
        this.results = [];
        this.searchTimeout = null;

        this.init();
    }

    init() {
        // Create overlay HTML
        this.createOverlay();

        // Bind keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            // Ctrl+Space to toggle
            if (e.ctrlKey && e.code === 'Space') {
                e.preventDefault();
                this.toggle();
            }

            // Esc to close
            if (e.key === 'Escape' && this.isOpen) {
                this.close();
            }
        });
    }

    createOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'quick-search-overlay';
        overlay.className = 'quick-search-overlay hidden';
        overlay.innerHTML = `
            <div class="quick-search-backdrop" onclick="quickSearch.close()"></div>
            <div class="quick-search-container">
                <div class="quick-search-header">
                    <div class="search-icon">🔍</div>
                    <input 
                        type="text" 
                        id="quick-search-input" 
                        placeholder="Search files, chat, screenshots, web..."
                        autocomplete="off"
                    />
                    <div class="search-hint">Ctrl+Space</div>
                </div>
                
                <div class="quick-search-filters">
                    <button class="filter-btn active" data-filter="all">All</button>
                    <button class="filter-btn" data-filter="files">Files</button>
                    <button class="filter-btn" data-filter="chat">Chat</button>
                    <button class="filter-btn" data-filter="screenshots">Screenshots</button>
                    <button class="filter-btn" data-filter="web">Web</button>
                </div>
                
                <div class="quick-search-results" id="quick-search-results">
                    <div class="search-empty">
                        <div class="empty-icon">🔍</div>
                        <div class="empty-text">Type to search...</div>
                        <div class="empty-hint">Search across files, chat history, screenshots, and web</div>
                    </div>
                </div>
                
                <div class="quick-search-footer">
                    <div class="footer-shortcuts">
                        <span><kbd>↑↓</kbd> Navigate</span>
                        <span><kbd>Enter</kbd> Open</span>
                        <span><kbd>Esc</kbd> Close</span>
                    </div>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Bind input events
        const input = document.getElementById('quick-search-input');
        input.addEventListener('input', (e) => this.handleSearch(e.target.value));
        input.addEventListener('keydown', (e) => this.handleKeyboard(e));

        // Bind filter buttons
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleFilter(e.target.dataset.filter));
        });
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    open() {
        // Close file manager if open
        if (window.fileManager && window.fileManager.isOpen) {
            window.fileManager.close();
        }
        // Close command palette if open
        if (window.commandPalette && window.commandPalette.isOpen) {
            window.commandPalette.close();
        }

        this.isOpen = true;
        const overlay = document.getElementById('quick-search-overlay');
        overlay.classList.remove('hidden');
        overlay.classList.add('active');

        // Focus input
        setTimeout(() => {
            document.getElementById('quick-search-input').focus();
        }, 100);
    }

    close() {
        this.isOpen = false;
        const overlay = document.getElementById('quick-search-overlay');
        overlay.classList.remove('active');
        overlay.classList.add('hidden');

        // Clear search
        document.getElementById('quick-search-input').value = '';
        this.results = [];
        this.selectedIndex = 0;
    }

    async handleSearch(query) {
        // Debounce search
        clearTimeout(this.searchTimeout);

        if (!query || query.length < 2) {
            this.showEmpty();
            return;
        }

        this.searchTimeout = setTimeout(async () => {
            await this.performSearch(query);
        }, 300);
    }

    async performSearch(query) {
        try {
            this.showLoading();

            const response = await fetch(`${this.API_URL}/search/universal`, {
                method: 'POST',
                headers: {
                    'X-API-Key': this.API_KEY,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ query })
            });

            const data = await response.json();

            if (data.success) {
                this.displayResults(data.results);
            } else {
                this.showError(data.error);
            }
        } catch (error) {
            console.error('Search error:', error);
            this.showError('Search failed');
        }
    }

    displayResults(results) {
        this.results = [];
        let html = '';

        // Flatten results from all categories
        Object.entries(results).forEach(([category, items]) => {
            if (Array.isArray(items) && items.length > 0) {
                html += `<div class="result-category">${this.getCategoryIcon(category)} ${category.toUpperCase()}</div>`;

                items.forEach((item, index) => {
                    const globalIndex = this.results.length;
                    this.results.push({ ...item, category });

                    html += this.renderResultItem(item, globalIndex);
                });
            }
        });

        if (html === '') {
            this.showEmpty('No results found');
        } else {
            document.getElementById('quick-search-results').innerHTML = html;
            this.selectedIndex = 0;
            this.updateSelection();
        }
    }

    renderResultItem(item, index) {
        const icon = item.icon || '📄';
        const title = this.highlightMatch(item.title || item.name || 'Untitled');
        const subtitle = item.path || item.url || item.description || '';

        return `
            <div class="result-item" data-index="${index}" onclick="quickSearch.selectResult(${index})">
                <div class="result-icon">${icon}</div>
                <div class="result-content">
                    <div class="result-title">${title}</div>
                    ${subtitle ? `<div class="result-subtitle">${subtitle}</div>` : ''}
                </div>
                <div class="result-actions">
                    <button class="action-btn" onclick="quickSearch.openResult(${index}); event.stopPropagation();" title="Open">↗</button>
                </div>
            </div>
        `;
    }

    highlightMatch(text) {
        // Simple highlight - could be improved with actual query matching
        return text;
    }

    getCategoryIcon(category) {
        const icons = {
            files: '📁',
            code: '💻',
            chat: '💬',
            screenshots: '📸',
            web: '🌐'
        };
        return icons[category] || '📄';
    }

    handleKeyboard(e) {
        if (e.key === 'ArrowDown') {
            e.preventDefault();
            this.selectedIndex = Math.min(this.selectedIndex + 1, this.results.length - 1);
            this.updateSelection();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
            this.updateSelection();
        } else if (e.key === 'Enter') {
            e.preventDefault();
            this.openResult(this.selectedIndex);
        }
    }

    updateSelection() {
        document.querySelectorAll('.result-item').forEach((item, index) => {
            if (index === this.selectedIndex) {
                item.classList.add('selected');
                item.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
            } else {
                item.classList.remove('selected');
            }
        });
    }

    selectResult(index) {
        this.selectedIndex = index;
        this.updateSelection();
    }

    openResult(index) {
        const result = this.results[index];
        if (!result) return;

        if (result.url) {
            window.open(result.url, '_blank');
        } else if (result.path) {
            // For files, show in a new window or download
            if (result.type === 'screenshot' || result.type === 'file') {
                window.open(result.thumbnail || result.path, '_blank');
            } else {
                alert(`File: ${result.path}`);
            }
        }

        this.close();
    }

    handleFilter(filter) {
        // Update active filter button
        document.querySelectorAll('.filter-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.filter === filter);
        });

        // Re-search with filter
        const query = document.getElementById('quick-search-input').value;
        if (query) {
            this.handleSearch(query);
        }
    }

    showLoading() {
        document.getElementById('quick-search-results').innerHTML = `
            <div class="search-loading">
                <div class="loading-spinner"></div>
                <div class="loading-text">Searching...</div>
            </div>
        `;
    }

    showEmpty(message = 'Type to search...') {
        document.getElementById('quick-search-results').innerHTML = `
            <div class="search-empty">
                <div class="empty-icon">🔍</div>
                <div class="empty-text">${message}</div>
                <div class="empty-hint">Search across files, chat history, screenshots, and web</div>
            </div>
        `;
    }

    showError(message) {
        document.getElementById('quick-search-results').innerHTML = `
            <div class="search-error">
                <div class="error-icon">⚠️</div>
                <div class="error-text">${message}</div>
            </div>
        `;
    }
}

// Initialize global instance
let quickSearch;
document.addEventListener('DOMContentLoaded', () => {
    quickSearch = new QuickSearch();
    console.log('✅ Quick Search initialized (Ctrl+Space)');
});
