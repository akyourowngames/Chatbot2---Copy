/**
 * Command Palette - Quick Actions with Ctrl+K
 * ============================================
 * Fuzzy search command palette for JARVIS
 */

class CommandPalette {
    constructor() {
        this.isOpen = false;
        this.commands = [
            { id: 'new-chat', icon: '💬', title: 'New Conversation', description: 'Start a fresh chat', action: () => this.newChat() },
            { id: 'search', icon: '🔍', title: 'Search Messages', description: 'Find in conversation history', action: () => this.searchMessages() },
            { id: 'upload-file', icon: '📁', title: 'Upload File', description: 'Attach and analyze files', action: () => this.uploadFile() },
            { id: 'export-chat', icon: '💾', title: 'Export Chat', description: 'Download conversation', action: () => this.exportChat() },
            { id: 'clear-chat', icon: '🗑️', title: 'Clear Chat', description: 'Remove all messages', action: () => this.clearChat() },
            { id: 'settings', icon: '⚙️', title: 'Settings', description: 'Open preferences', action: () => this.openSettings() },
            { id: 'dashboard', icon: '📊', title: 'Dashboard', description: 'View analytics', action: () => window.open('dashboard.html') },
            { id: 'screenshot', icon: '📸', title: 'Take Screenshot', description: 'Capture screen', action: () => this.takeScreenshot() },
            { id: 'voice', icon: '🎤', title: 'Voice Input', description: 'Speak to JARVIS', action: () => this.toggleVoice() },
            { id: 'theme', icon: '🎨', title: 'Toggle Theme', description: 'Switch dark/light mode', action: () => this.toggleTheme() },
            { id: 'whatsapp-send', icon: '📱', title: 'Send WhatsApp Message', description: 'Send message via WhatsApp', action: () => this.sendWhatsAppMessage() },
            { id: 'whatsapp-call', icon: '📞', title: 'WhatsApp Call', description: 'Make a WhatsApp call', action: () => this.makeWhatsAppCall() },
            { id: 'whatsapp-group', icon: '👥', title: 'Message WhatsApp Group', description: 'Send group message', action: () => this.sendWhatsAppGroup() },
        ];
        this.filteredCommands = [...this.commands];
        this.selectedIndex = 0;
        this.init();
    }

    init() {
        this.createPaletteHTML();
        this.attachEventListeners();
    }

    createPaletteHTML() {
        const palette = document.createElement('div');
        palette.id = 'commandPalette';
        palette.className = 'command-palette';
        palette.innerHTML = `
            <div class="command-palette-backdrop" onclick="commandPalette.close()"></div>
            <div class="command-palette-modal">
                <div class="command-palette-search">
                    <span class="search-icon">🔍</span>
                    <input 
                        type="text" 
                        id="commandSearch" 
                        placeholder="Type a command or search..."
                        autocomplete="off"
                    />
                    <kbd class="shortcut-hint">Esc</kbd>
                </div>
                <div class="command-list" id="commandList"></div>
                <div class="command-palette-footer">
                    <span>↑↓ Navigate</span>
                    <span>↵ Select</span>
                    <span>Esc Close</span>
                </div>
            </div>
        `;
        document.body.appendChild(palette);
    }

    attachEventListeners() {
        // Ctrl+K to open
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.toggle();
            }
        });

        // Search input
        const searchInput = document.getElementById('commandSearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.handleSearch(e.target.value));
            searchInput.addEventListener('keydown', (e) => this.handleKeyNav(e));
        }
    }

    toggle() {
        if (this.isOpen) {
            this.close();
        } else {
            this.open();
        }
    }

    open() {
        if (window.fileManager && window.fileManager.isOpen) {
            window.fileManager.close();
        }
        this.isOpen = true;
        const palette = document.getElementById('commandPalette');
        palette.style.display = 'flex';
        setTimeout(() => palette.classList.add('active'), 10);

        const searchInput = document.getElementById('commandSearch');
        searchInput.value = '';
        searchInput.focus();

        this.filteredCommands = [...this.commands];
        this.selectedIndex = 0;
        this.renderCommands();
    }

    close() {
        this.isOpen = false;
        const palette = document.getElementById('commandPalette');
        palette.classList.remove('active');
        setTimeout(() => palette.style.display = 'none', 300);
    }

    handleSearch(query) {
        query = query.toLowerCase();
        this.filteredCommands = this.commands.filter(cmd =>
            cmd.title.toLowerCase().includes(query) ||
            cmd.description.toLowerCase().includes(query)
        );
        this.selectedIndex = 0;
        this.renderCommands();
    }

    handleKeyNav(e) {
        if (e.key === 'Escape') {
            e.preventDefault();
            this.close();
        } else if (e.key === 'ArrowDown') {
            e.preventDefault();
            this.selectedIndex = Math.min(this.selectedIndex + 1, this.filteredCommands.length - 1);
            this.renderCommands();
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            this.selectedIndex = Math.max(this.selectedIndex - 1, 0);
            this.renderCommands();
        } else if (e.key === 'Enter') {
            e.preventDefault();
            this.executeSelected();
        }
    }

    renderCommands() {
        const listEl = document.getElementById('commandList');
        if (!listEl) return;

        if (this.filteredCommands.length === 0) {
            listEl.innerHTML = '<div class="no-results">No commands found</div>';
            return;
        }

        listEl.innerHTML = this.filteredCommands.map((cmd, index) => `
            <div class="command-item ${index === this.selectedIndex ? 'selected' : ''}" 
                 onclick="commandPalette.executeCommand('${cmd.id}')"
                 onmouseenter="commandPalette.selectedIndex = ${index}; commandPalette.renderCommands();">
                <span class="command-icon">${cmd.icon}</span>
                <div class="command-info">
                    <div class="command-title">${cmd.title}</div>
                    <div class="command-description">${cmd.description}</div>
                </div>
            </div>
        `).join('');

        // Scroll selected into view
        const selected = listEl.querySelector('.command-item.selected');
        if (selected) {
            selected.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        }
    }

    executeSelected() {
        if (this.filteredCommands[this.selectedIndex]) {
            this.executeCommand(this.filteredCommands[this.selectedIndex].id);
        }
    }

    executeCommand(id) {
        const command = this.commands.find(cmd => cmd.id === id);
        if (command) {
            this.close();
            command.action();
        }
    }

    // Command actions
    newChat() {
        if (typeof window.newChat === 'function') {
            window.newChat();
        } else {
            // Fallback implementation
            document.getElementById('messages').innerHTML = '';
            const welcome = document.createElement('div');
            welcome.className = 'welcome';
            welcome.id = 'welcome';
            welcome.innerHTML = '<h1>⚡ JARVIS AI</h1><p>Your premium AI assistant with advanced capabilities</p>';
            document.getElementById('messages').appendChild(welcome);
        }
    }

    searchMessages() {
        const query = prompt('Search messages:');
        if (query) {
            fetch(`${API_URL}/conversations/search?q=${encodeURIComponent(query)}`, {
                headers: { 'X-API-Key': API_KEY }
            })
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'success' && data.results.length > 0) {
                        alert(`Found ${data.results.length} results for "${query}"`);
                    } else {
                        alert('No results found');
                    }
                })
                .catch(() => alert('Search failed'));
        }
    }

    uploadFile() {
        if (typeof window.fileManager !== 'undefined' && window.fileManager) {
            window.fileManager.open();
        } else if (typeof window.attachFile === 'function') {
            window.attachFile();
        } else {
            alert('File upload feature not available');
        }
    }

    exportChat() {
        const messages = document.querySelectorAll('.message');
        let chatText = 'JARVIS Conversation Export\n\n';

        messages.forEach(msg => {
            const role = msg.classList.contains('user') ? 'You' : 'JARVIS';
            const content = msg.querySelector('.message-content').textContent;
            chatText += `${role}: ${content}\n\n`;
        });

        const blob = new Blob([chatText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `jarvis-chat-${Date.now()}.txt`;
        a.click();
        URL.revokeObjectURL(url);
    }

    clearChat() {
        if (confirm('Clear all messages?')) {
            document.getElementById('messages').innerHTML = '';
            this.newChat();
        }
    }

    openSettings() {
        alert('Settings panel coming soon! You can access preferences via the API.');
    }

    takeScreenshot() {
        fetch(`${API_URL}/automation/screenshot`, {
            method: 'POST',
            headers: { 'X-API-Key': API_KEY }
        }).then(r => r.json()).then(data => {
            if (data.status === 'success') {
                alert('Screenshot saved to: ' + data.filepath);
            } else {
                alert('Screenshot failed');
            }
        }).catch(() => alert('Screenshot failed'));
    }

    toggleVoice() {
        if (typeof window.toggleVoice === 'function') {
            window.toggleVoice();
        } else {
            alert('Voice input feature not available in this view');
        }
    }

    toggleTheme() {
        document.body.classList.toggle('light-theme');
        const isLight = document.body.classList.contains('light-theme');

        // Save preference
        fetch(`${API_URL}/preferences`, {
            method: 'POST',
            headers: { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' },
            body: JSON.stringify({ key: 'theme', value: isLight ? 'light' : 'dark' })
        });

        alert(`Switched to ${isLight ? 'light' : 'dark'} theme`);
    }

    // WhatsApp Automation
    sendWhatsAppMessage() {
        const phone = prompt('Enter phone number with country code (e.g., +1234567890):');
        if (!phone) return;

        const message = prompt('Enter your message:');
        if (!message) return;

        fetch(`${API_URL}/whatsapp/send`, {
            method: 'POST',
            headers: { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone, message, instant: true })
        })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('✅ Message sent successfully!');
                } else {
                    alert('❌ Failed: ' + data.message);
                }
            })
            .catch(err => alert('❌ Error: ' + err.message));
    }

    makeWhatsAppCall() {
        const phone = prompt('Enter phone number with country code (e.g., +1234567890):');
        if (!phone) return;

        fetch(`${API_URL}/whatsapp/call`, {
            method: 'POST',
            headers: { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' },
            body: JSON.stringify({ phone })
        })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('📞 Call initiated! Check WhatsApp Web.');
                } else {
                    alert('❌ Failed: ' + data.message);
                }
            })
            .catch(err => alert('❌ Error: ' + err.message));
    }

    sendWhatsAppGroup() {
        const group = prompt('Enter group name:');
        if (!group) return;

        const message = prompt('Enter your message:');
        if (!message) return;

        fetch(`${API_URL}/whatsapp/send-group`, {
            method: 'POST',
            headers: { 'X-API-Key': API_KEY, 'Content-Type': 'application/json' },
            body: JSON.stringify({ group, message })
        })
            .then(r => r.json())
            .then(data => {
                if (data.status === 'success') {
                    alert('✅ Group message sent!');
                } else {
                    alert('❌ Failed: ' + data.message);
                }
            })
            .catch(err => alert('❌ Error: ' + err.message));
    }
}

// Initialize
let commandPalette;
document.addEventListener('DOMContentLoaded', () => {
    commandPalette = new CommandPalette();
});
