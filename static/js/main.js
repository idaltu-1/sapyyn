// Sapyyn Patient Referral System - Main JavaScript
// Copyright (c) 2025 Sapyyn. All rights reserved.

// Global variables and configuration
const SapyynApp = {
    apiUrl: '/api',
    version: '1.0.0',
    debug: true,
    year: 2025
};

// Utility functions
const Utils = {
    // Format file size
    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // Format date
    formatDate(dateString) {
        const options = { 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        };
        return new Date(dateString).toLocaleDateString('en-US', options);
    },

    // Debounce function
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    // Show toast notification
    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer') || this.createToastContainer();
        
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'assertive');
        toast.setAttribute('aria-atomic', 'true');
        
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" 
                        data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove toast after it's hidden
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    },

    // Create toast container if it doesn't exist
    createToastContainer() {
        const container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
        return container;
    },

    // Loading overlay
    showLoading() {
        if (document.getElementById('loadingOverlay')) return;
        
        const overlay = document.createElement('div');
        overlay.id = 'loadingOverlay';
        overlay.className = 'loading-overlay';
        overlay.innerHTML = `
            <div class="text-center">
                <div class="loading-spinner"></div>
                <p class="mt-3 text-muted">Loading...</p>
            </div>
        `;
        document.body.appendChild(overlay);
    },

    hideLoading() {
        const overlay = document.getElementById('loadingOverlay');
        if (overlay) {
            overlay.remove();
        }
    }
};

// File upload functionality
const FileUpload = {
    init() {
        this.setupDragAndDrop();
        this.setupFileValidation();
    },

    setupDragAndDrop() {
        const uploadArea = document.querySelector('.file-upload-area');
        if (!uploadArea) return;

        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.preventDefaults, false);
            document.body.addEventListener(eventName, this.preventDefaults, false);
        });

        ['dragenter', 'dragover'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.highlight.bind(this), false);
        });

        ['dragleave', 'drop'].forEach(eventName => {
            uploadArea.addEventListener(eventName, this.unhighlight.bind(this), false);
        });

        uploadArea.addEventListener('drop', this.handleDrop.bind(this), false);
    },

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    },

    highlight(e) {
        e.target.classList.add('dragover');
    },

    unhighlight(e) {
        e.target.classList.remove('dragover');
    },

    handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        
        if (files.length > 0) {
            const fileInput = document.getElementById('file');
            if (fileInput) {
                fileInput.files = files;
                this.handleFileSelect(files[0]);
            }
        }
    },

    setupFileValidation() {
        const fileInput = document.getElementById('file');
        if (!fileInput) return;

        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFileSelect(e.target.files[0]);
            }
        });
    },

    handleFileSelect(file) {
        if (!this.validateFile(file)) return;

        this.showFilePreview(file);
        Utils.showToast(`File "${file.name}" selected successfully`, 'success');
    },

    validateFile(file) {
        const maxSize = 16 * 1024 * 1024; // 16MB
        const allowedTypes = [
            'application/pdf',
            'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'text/plain',
            'image/png',
            'image/jpeg',
            'image/jpg',
            'image/gif',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ];

        if (file.size > maxSize) {
            Utils.showToast('File size must be less than 16MB', 'danger');
            return false;
        }

        if (!allowedTypes.includes(file.type)) {
            Utils.showToast('File type not supported', 'danger');
            return false;
        }

        return true;
    },

    showFilePreview(file) {
        const preview = document.getElementById('filePreview');
        if (!preview) return;

        const previewContent = preview.querySelector('#previewContent');
        if (!previewContent) return;

        let content = `
            <div class="d-flex align-items-center">
                <div class="me-3">
                    ${this.getFileIcon(file.type)}
                </div>
                <div>
                    <div class="fw-semibold">${file.name}</div>
                    <div class="text-muted small">
                        Size: ${Utils.formatFileSize(file.size)} | 
                        Type: ${file.type || 'Unknown'}
                    </div>
                </div>
            </div>
        `;

        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                content += `
                    <div class="mt-3">
                        <img src="${e.target.result}" alt="Preview" class="img-thumbnail" style="max-height: 200px;">
                    </div>
                `;
                previewContent.innerHTML = content;
            };
            reader.readAsDataURL(file);
        } else {
            previewContent.innerHTML = content;
        }

        preview.style.display = 'block';
    },

    getFileIcon(type) {
        const iconMap = {
            'application/pdf': '<i class="bi bi-file-pdf text-danger fs-1"></i>',
            'application/msword': '<i class="bi bi-file-word text-primary fs-1"></i>',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '<i class="bi bi-file-word text-primary fs-1"></i>',
            'text/plain': '<i class="bi bi-file-text text-secondary fs-1"></i>',
            'application/vnd.ms-excel': '<i class="bi bi-file-excel text-success fs-1"></i>',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '<i class="bi bi-file-excel text-success fs-1"></i>'
        };

        if (type.startsWith('image/')) {
            return '<i class="bi bi-file-image text-info fs-1"></i>';
        }

        return iconMap[type] || '<i class="bi bi-file-earmark text-muted fs-1"></i>';
    }
};

// Dashboard functionality
const Dashboard = {
    init() {
        this.loadStats();
        this.setupAutoRefresh();
    },

    loadStats() {
        fetch('/api/stats')
            .then(response => response.json())
            .then(data => {
                this.updateStatCards(data);
                this.updateCharts(data);
            })
            .catch(error => {
                console.error('Error loading stats:', error);
                Utils.showToast('Failed to load dashboard statistics', 'danger');
            });
    },

    updateStatCards(data) {
        const pendingElement = document.getElementById('pendingCount');
        const approvedElement = document.getElementById('approvedCount');

        if (pendingElement) {
            pendingElement.textContent = data.status_counts?.pending || 0;
        }
        if (approvedElement) {
            approvedElement.textContent = data.status_counts?.approved || 0;
        }
    },

    updateCharts(data) {
        // Implement chart updates if needed
        console.log('Charts data:', data);
    },

    setupAutoRefresh() {
        // Refresh dashboard every 5 minutes
        setInterval(() => {
            this.loadStats();
        }, 5 * 60 * 1000);
    }
};

// Search and filter functionality
const Search = {
    init() {
        this.setupDocumentSearch();
        this.setupReferralSearch();
    },

    setupDocumentSearch() {
        const searchInput = document.getElementById('searchDocuments');
        const filterSelect = document.getElementById('filterType');

        if (searchInput) {
            searchInput.addEventListener('input', Utils.debounce(() => {
                this.filterDocuments();
            }, 300));
        }

        if (filterSelect) {
            filterSelect.addEventListener('change', () => {
                this.filterDocuments();
            });
        }
    },

    setupReferralSearch() {
        const searchInput = document.getElementById('searchReferrals');
        if (searchInput) {
            searchInput.addEventListener('input', Utils.debounce(() => {
                this.filterReferrals();
            }, 300));
        }
    },

    filterDocuments() {
        const searchTerm = document.getElementById('searchDocuments')?.value.toLowerCase() || '';
        const filterType = document.getElementById('filterType')?.value || '';
        const documents = document.querySelectorAll('.document-item');

        let visibleCount = 0;

        documents.forEach(doc => {
            const name = doc.dataset.name || '';
            const type = doc.dataset.type || '';

            const matchesSearch = !searchTerm || name.includes(searchTerm);
            const matchesFilter = !filterType || type === filterType;

            if (matchesSearch && matchesFilter) {
                doc.style.display = 'block';
                visibleCount++;
            } else {
                doc.style.display = 'none';
            }
        });

        // Update results counter
        this.updateResultsCounter(visibleCount, documents.length);
    },

    filterReferrals() {
        // Implement referral filtering
        console.log('Filtering referrals...');
    },

    updateResultsCounter(visible, total) {
        let counter = document.getElementById('resultsCounter');
        if (!counter) {
            counter = document.createElement('div');
            counter.id = 'resultsCounter';
            counter.className = 'text-muted small mt-2';
            
            const searchContainer = document.getElementById('searchDocuments')?.parentNode;
            if (searchContainer) {
                searchContainer.appendChild(counter);
            }
        }
        
        counter.textContent = `Showing ${visible} of ${total} documents`;
    }
};

// Form validation and enhancement
const Forms = {
    init() {
        this.setupFormValidation();
        this.setupAutoSave();
    },

    setupFormValidation() {
        const forms = document.querySelectorAll('form[data-validate]');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                }
            });
        });
    },

    validateForm(form) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                this.showFieldError(field, 'This field is required');
                isValid = false;
            } else {
                this.clearFieldError(field);
            }
        });

        return isValid;
    },

    showFieldError(field, message) {
        field.classList.add('is-invalid');
        
        let feedback = field.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            field.parentNode.appendChild(feedback);
        }
        feedback.textContent = message;
    },

    clearFieldError(field) {
        field.classList.remove('is-invalid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    },

    setupAutoSave() {
        const forms = document.querySelectorAll('form[data-autosave]');
        forms.forEach(form => {
            form.addEventListener('input', Utils.debounce(() => {
                this.autoSave(form);
            }, 2000));
        });
    },

    autoSave(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData);
        const formId = form.id || 'form';
        
        localStorage.setItem(`autosave_${formId}`, JSON.stringify(data));
        Utils.showToast('Draft saved automatically', 'info');
    }
};

// QR Code functionality
const QRCode = {
    generate(data, containerId) {
        // This would integrate with a QR code library
        console.log('Generating QR code for:', data);
        
        const container = document.getElementById(containerId);
        if (container) {
            container.innerHTML = `
                <div class="qr-code-container">
                    <div class="placeholder bg-light p-4 text-center">
                        <i class="bi bi-qr-code fs-1 text-muted"></i>
                        <p class="mt-2 text-muted">QR Code would be generated here</p>
                    </div>
                </div>
            `;
        }
    },

    download(qrCodeData, filename = 'qr-code.png') {
        // Create download link for QR code
        const link = document.createElement('a');
        link.download = filename;
        link.href = `data:image/png;base64,${qrCodeData}`;
        link.click();
    }
};

// Notification system
const Notifications = {
    init() {
        this.checkPermission();
        this.setupServiceWorker();
    },

    checkPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    },

    show(title, options = {}) {
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(title, {
                icon: '/static/images/logo.png',
                badge: '/static/images/badge.png',
                ...options
            });
        } else {
            Utils.showToast(title, 'info');
        }
    },

    setupServiceWorker() {
        if ('serviceWorker' in navigator) {
            navigator.serviceWorker.register('/static/js/sw.js')
                .then(registration => {
                    console.log('Service Worker registered:', registration);
                })
                .catch(error => {
                    console.log('Service Worker registration failed:', error);
                });
        }
    }
};

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
    console.log('Sapyyn App initialized');
    
    // Initialize modules
    FileUpload.init();
    Dashboard.init();
    Search.init();
    Forms.init();
    Notifications.init();
    
    // Setup global event listeners
    setupGlobalEventListeners();
    
    // Setup theme handling
    setupThemeHandling();
});

// Global event listeners
function setupGlobalEventListeners() {
    // Handle all modal events
    document.addEventListener('show.bs.modal', function(e) {
        console.log('Modal opening:', e.target.id);
    });
    
    // Handle form submissions
    document.addEventListener('submit', function(e) {
        const form = e.target;
        if (form.tagName === 'FORM') {
            Utils.showLoading();
        }
    });
    
    // Handle page unload
    window.addEventListener('beforeunload', function(e) {
        // Check for unsaved changes
        const hasUnsavedChanges = localStorage.getItem('hasUnsavedChanges');
        if (hasUnsavedChanges === 'true') {
            e.preventDefault();
            e.returnValue = '';
        }
    });
}

// Theme handling
function setupThemeHandling() {
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });
    }
    
    // Load saved theme
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    }
}

// Export functions for global use
window.SapyynApp = SapyynApp;
window.Utils = Utils;
window.FileUpload = FileUpload;
window.Dashboard = Dashboard;
window.Search = Search;
window.Forms = Forms;
window.QRCode = QRCode;
window.Notifications = Notifications;