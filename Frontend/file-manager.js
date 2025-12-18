/**
 * File Manager - Drag & Drop File Management
 * ==========================================
 * File upload, history, and management UI
 */

class FileManager {
    constructor() {
        this.isOpen = false;
        this.files = [];
        this.init();
    }

    init() {
        this.createFileManagerHTML();
        this.attachEventListeners();
        this.loadFileHistory();
    }

    createFileManagerHTML() {
        const fileManager = document.createElement('div');
        fileManager.id = 'fileManager';
        fileManager.className = 'file-manager';
        fileManager.innerHTML = `
            <div class="file-manager-header">
                <div class="file-manager-title">📁 Files</div>
                <button class="file-manager-close" onclick="fileManager.close()">✕</button>
            </div>
            
            <div class="file-drop-zone" id="fileDropZone">
                <div class="file-drop-icon">📤</div>
                <div class="file-drop-text">Drop files here</div>
                <div class="file-drop-hint">or click to browse</div>
                <input type="file" id="fileInput" style="display: none;" multiple>
            </div>
            
            <div class="file-list">
                <div class="file-list-title">Recent Files</div>
                <div id="fileListContainer"></div>
            </div>
        `;
        document.body.appendChild(fileManager);
    }

    attachEventListeners() {
        const dropZone = document.getElementById('fileDropZone');
        const fileInput = document.getElementById('fileInput');

        // Click to browse
        dropZone.addEventListener('click', () => fileInput.click());

        // File input change
        fileInput.addEventListener('change', (e) => {
            this.handleFiles(Array.from(e.target.files));
        });

        // Drag and drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('drag-over');
        });

        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('drag-over');
        });

        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('drag-over');
            this.handleFiles(Array.from(e.dataTransfer.files));
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
        if (window.commandPalette && window.commandPalette.isOpen) {
            window.commandPalette.close();
        }
        this.isOpen = true;
        document.getElementById('fileManager').classList.add('open');
        this.loadFileHistory();
    }

    close() {
        this.isOpen = false;
        document.getElementById('fileManager').classList.remove('open');
    }

    async handleFiles(files) {
        for (const file of files) {
            await this.uploadFile(file);
        }
    }

    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch(`${API_URL}/files/upload`, {
                method: 'POST',
                headers: { 'X-API-Key': API_KEY },
                body: formData
            });

            const data = await response.json();

            if (data.status === 'success') {
                this.showNotification(`✅ ${file.name} uploaded successfully`);
                this.loadFileHistory();

                // Show analysis in chat
                if (data.analysis && data.analysis.analysis) {
                    addMessage('assistant', data.analysis.analysis);
                }
            } else {
                this.showNotification(`❌ Failed to upload ${file.name}`);
            }
        } catch (error) {
            console.error('Upload error:', error);
            this.showNotification(`❌ Upload failed: ${error.message}`);
        }
    }

    async loadFileHistory() {
        try {
            const response = await fetch(`${API_URL}/files`, {
                headers: { 'X-API-Key': API_KEY }
            });
            const data = await response.json();
            // Expected format: { files: [...] }
            if (Array.isArray(data.files)) {
                this.files = data.files;
                this.renderFileList();
            } else {
                console.error('Unexpected file list response:', data);
            }
        } catch (error) {
            console.error('Failed to load file list:', error);
        }
    }

    renderFileList() {
        const container = document.getElementById('fileListContainer');

        if (this.files.length === 0) {
            container.innerHTML = '<div style="text-align: center; padding: 20px; color: #94a3b8;">No files yet</div>';
            return;
        }

        container.innerHTML = this.files.map(file => `
            <div class="file-item" onclick="fileManager.viewFile('${file.filepath}')">
                <div class="file-item-icon">${this.getFileIcon(file.file_type)}</div>
                <div class="file-item-info">
                    <div class="file-item-name">${file.filename}</div>
                    <div class="file-item-meta">${this.formatFileSize(file.size_bytes)} • ${this.formatDate(file.uploaded_at)}</div>
                </div>
                <div class="file-item-actions">
                    <button class="file-action-btn" onclick="event.stopPropagation(); fileManager.downloadFile('${file.id}')" title="Download">⬇️</button>
                    <button class="file-action-btn" onclick="event.stopPropagation(); fileManager.analyzeFile('${file.id}')" title="Analyze">🔍</button>
                    <button class="file-action-btn" onclick="event.stopPropagation(); fileManager.deleteFile('${file.id}')" title="Delete">🗑️</button>
                </div>
            </div>
        `).join('');
    }

    getFileIcon(type) {
        const icons = {
            'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️', 'gif': '🖼️',
            'pdf': '📄', 'doc': '📝', 'docx': '📝', 'txt': '📝',
            'py': '🐍', 'js': '📜', 'html': '🌐', 'css': '🎨',
            'json': '📋', 'csv': '📊', 'xml': '📋',
            'zip': '📦', 'rar': '📦', '7z': '📦'
        };
        return icons[type] || '📄';
    }

    formatFileSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    formatDate(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diff = now - date;

        if (diff < 60000) return 'Just now';
        if (diff < 3600000) return Math.floor(diff / 60000) + 'm ago';
        if (diff < 86400000) return Math.floor(diff / 3600000) + 'h ago';
        return Math.floor(diff / 86400000) + 'd ago';
    }

    viewFile(filepath) {
        // TODO: Implement file preview
        alert('File preview coming soon!');
    }

    downloadFile(fileId) {
        // Open the download endpoint for the file
        const url = `${API_URL}/files/${fileId}/download`;
        window.open(url, '_blank');
    }

    async deleteFile(fileId) {
        if (!confirm('Delete this file?')) return;
        try {
            const response = await fetch(`${API_URL}/files/${fileId}`, {
                method: 'DELETE',
                headers: { 'X-API-Key': API_KEY }
            });
            const data = await response.json();
            if (data.success) {
                this.showNotification('File deleted successfully');
                this.loadFileHistory();
            } else {
                this.showNotification(`Delete failed: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Delete error:', error);
            this.showNotification('Delete request failed');
        }
    }

    async analyzeFile(fileId) {
        try {
            const response = await fetch(`${API_URL}/files/${fileId}/analyze`, {
                method: 'GET',
                headers: { 'X-API-Key': API_KEY }
            });
            const data = await response.json();
            if (data.success) {
                // Show analysis in chat or notification
                addMessage('assistant', data.description || data.analysis || 'No analysis returned');
                this.showNotification('Analysis completed');
            } else {
                this.showNotification(`Analysis failed: ${data.error || 'Unknown error'}`);
            }
        } catch (error) {
            console.error('Analysis error:', error);
            this.showNotification('Analysis request failed');
        }
    }

    showNotification(message) {
        // Simple notification
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: rgba(10, 14, 39, 0.98);
            border: 1px solid rgba(0, 212, 255, 0.3);
            padding: 16px 24px;
            border-radius: 12px;
            color: #f8fafc;
            z-index: 10000;
            animation: slideIn 0.3s ease;
        `;
        notification.textContent = message;
        document.body.appendChild(notification);

        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => notification.remove(), 300);
        }, 3000);
    }
}

// Initialize
let fileManager;
document.addEventListener('DOMContentLoaded', () => {
    fileManager = new FileManager();
});

// Global function for attach button
function attachFile() {
    if (!fileManager) {
        fileManager = new FileManager();
    }
    fileManager.open();
}
