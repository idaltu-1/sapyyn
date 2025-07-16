// Sapyyn Patient Referral System - Enhanced Main JavaScript
// Copyright (c) 2025 Sapyyn. All rights reserved.

// Global variables and configuration
const SapyynApp = {
    apiUrl: '/api',
    version: '1.0.0',
    debug: true,
    year: 2025
};

// ============================================================================
// STICKY CTA FUNCTIONALITY - High Converting Floating Action
// ============================================================================

class StickyCTA {
    constructor() {
        this.element = document.getElementById('stickyCTA');
        this.threshold = 500; // Show after scrolling 500px
        this.isVisible = false;
        this.init();
    }

    init() {
        if (!this.element) return;
        
        // Show/hide based on scroll position
        window.addEventListener('scroll', this.handleScroll.bind(this));
        
        // Track CTA clicks for analytics
        this.element.addEventListener('click', this.trackClick.bind(this));
        
        // Hide on mobile to avoid interference
        this.checkMobile();
        window.addEventListener('resize', this.checkMobile.bind(this));
    }

    handleScroll() {
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        
        if (scrollTop > this.threshold && !this.isVisible) {
            this.show();
        } else if (scrollTop <= this.threshold && this.isVisible) {
            this.hide();
        }
    }

    show() {
        if (!this.element) return;
        this.element.classList.add('visible');
        this.isVisible = true;
        
        // Announce to screen readers
        this.element.setAttribute('aria-live', 'polite');
        this.element.setAttribute('aria-label', 'Free trial call-to-action appeared');
    }

    hide() {
        if (!this.element) return;
        this.element.classList.remove('visible');
        this.isVisible = false;
    }

    checkMobile() {
        if (window.innerWidth <= 768 && this.element) {
            this.element.style.display = 'none';
        } else if (this.element) {
            this.element.style.display = 'block';
        }
    }

    trackClick() {
        // Track CTA click for analytics
        if (typeof gtag !== 'undefined') {
            gtag('event', 'click', {
                event_category: 'CTA',
                event_label: 'Sticky CTA',
                value: 1
            });
        }
        
        console.log('Sticky CTA clicked');
    }
}

// ============================================================================
// ENHANCED FORM INTERACTIONS & ACCESSIBILITY
// ============================================================================

class FormEnhancements {
    constructor() {
        this.init();
    }

    init() {
        this.enhanceProviderCodeInput();
        this.addFormValidation();
        this.improveAccessibility();
    }

    enhanceProviderCodeInput() {
        const providerCodeInput = document.getElementById('homeProviderCode');
        if (!providerCodeInput) return;

        // Format input as user types
        providerCodeInput.addEventListener('input', (e) => {
            let value = e.target.value.replace(/\D/g, ''); // Remove non-digits
            
            if (value.length > 6) {
                value = value.substring(0, 6);
            }
            
            e.target.value = value;
            
            // Validate in real-time
            this.validateProviderCode(e.target);
        });

        // Add paste handling
        providerCodeInput.addEventListener('paste', (e) => {
            setTimeout(() => {
                let value = e.target.value.replace(/\D/g, '');
                if (value.length > 6) value = value.substring(0, 6);
                e.target.value = value;
                this.validateProviderCode(e.target);
            }, 0);
        });
    }

    validateProviderCode(input) {
        const isValid = input.value.length === 6 && /^\d{6}$/.test(input.value);
        
        if (isValid) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
            input.setAttribute('aria-describedby', 'valid-feedback');
        } else if (input.value.length > 0) {
            input.classList.remove('is-valid');
            input.classList.add('is-invalid');
            input.setAttribute('aria-describedby', 'invalid-feedback');
        } else {
            input.classList.remove('is-valid', 'is-invalid');
            input.removeAttribute('aria-describedby');
        }
    }

    addFormValidation() {
        const forms = document.querySelectorAll('form[data-validate]');
        forms.forEach(form => {
            form.addEventListener('submit', this.handleFormSubmit.bind(this));
        });
    }

    handleFormSubmit(e) {
        const form = e.target;
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
                field.classList.add('is-valid');
            }
        });

        if (!isValid) {
            e.preventDefault();
            // Focus first invalid field
            const firstInvalid = form.querySelector('.is-invalid');
            if (firstInvalid) firstInvalid.focus();
        }
    }

    improveAccessibility() {
        // Add aria-live regions for dynamic content
        const dynamicElements = document.querySelectorAll('[data-dynamic]');
        dynamicElements.forEach(el => {
            if (!el.getAttribute('aria-live')) {
                el.setAttribute('aria-live', 'polite');
            }
        });

        // Improve focus management
        this.addFocusIndicators();
    }

    addFocusIndicators() {
        // Add visible focus indicators for better accessibility
        const focusableElements = document.querySelectorAll(
            'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );

        focusableElements.forEach(el => {
            el.addEventListener('focus', () => {
                el.classList.add('focused');
            });

            el.addEventListener('blur', () => {
                el.classList.remove('focused');
            });
        });
    }
}

// ============================================================================
// IMAGE LAZY LOADING & OPTIMIZATION
// ============================================================================

class ImageOptimization {
    constructor() {
        this.lazyImages = document.querySelectorAll('img[data-src]');
        this.init();
    }

    init() {
        if ('IntersectionObserver' in window) {
            this.lazyImageObserver = new IntersectionObserver(this.onIntersection.bind(this));
            this.lazyImages.forEach(img => this.lazyImageObserver.observe(img));
        } else {
            // Fallback for older browsers
            this.loadAllImages();
        }

        this.addWebPSupport();
    }

    onIntersection(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                this.loadImage(img);
                this.lazyImageObserver.unobserve(img);
            }
        });
    }

    loadImage(img) {
        img.src = img.dataset.src;
        img.classList.remove('lazy');
        img.classList.add('loaded');
        
        img.addEventListener('load', () => {
            img.classList.add('fade-in');
        });
    }

    loadAllImages() {
        this.lazyImages.forEach(img => this.loadImage(img));
    }

    addWebPSupport() {
        // Check WebP support and update image sources
        const webpSupported = this.supportsWebP();
        if (webpSupported) {
            const images = document.querySelectorAll('img[data-webp]');
            images.forEach(img => {
                if (img.dataset.webp) {
                    img.src = img.dataset.webp;
                }
            });
        }
    }

    supportsWebP() {
        const canvas = document.createElement('canvas');
        canvas.width = 1;
        canvas.height = 1;
        return canvas.toDataURL('image/webp').indexOf('webp') !== -1;
    }
}

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

// ============================================================================
// INITIALIZATION - DOM Content Loaded
// ============================================================================

document.addEventListener('DOMContentLoaded', function() {
    console.log(`🚀 Sapyyn v${SapyynApp.version} initialized`);
    
    // Initialize core functionality
    try {
        // Initialize sticky CTA
        const stickyCTA = new StickyCTA();
        
        // Initialize form enhancements
        const formEnhancements = new FormEnhancements();
        
        // Initialize image optimization
        const imageOptimization = new ImageOptimization();
        
        // Initialize existing features
        FileUpload.init();
        Forms.init();
        
        // Initialize dashboard if on dashboard page
        if (document.querySelector('[data-page="dashboard"]')) {
            Dashboard.init();
        }
        
        // Initialize search if search elements exist
        if (document.querySelector('[data-search]')) {
            Search.init();
        }
        
        // Add smooth scrolling for anchor links
        initSmoothScrolling();
        
        // Add scroll-to-top functionality
        initScrollToTop();
        
        // Initialize performance monitoring
        initPerformanceMonitoring();
        
        console.log('✅ All Sapyyn components initialized successfully');
        
    } catch (error) {
        console.error('❌ Error during Sapyyn initialization:', error);
    }
});

// ============================================================================
// SMOOTH SCROLLING & NAVIGATION ENHANCEMENTS
// ============================================================================

function initSmoothScrolling() {
    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
                
                // Update focus for accessibility
                target.focus();
                if (!target.hasAttribute('tabindex')) {
                    target.setAttribute('tabindex', '-1');
                }
            }
        });
    });
}

function initScrollToTop() {
    // Create scroll to top button
    const scrollBtn = document.createElement('button');
    scrollBtn.innerHTML = '<i class="bi bi-arrow-up" aria-hidden="true"></i>';
    scrollBtn.className = 'btn btn-primary scroll-to-top';
    scrollBtn.setAttribute('aria-label', 'Scroll to top');
    scrollBtn.style.cssText = `
        position: fixed;
        bottom: 2rem;
        left: 2rem;
        z-index: 999;
        border-radius: 50%;
        width: 50px;
        height: 50px;
        opacity: 0;
        transform: translateY(100px);
        transition: all 0.3s ease;
        pointer-events: none;
    `;
    
    document.body.appendChild(scrollBtn);
    
    // Show/hide scroll to top button
    let scrollToTopVisible = false;
    window.addEventListener('scroll', () => {
        const shouldShow = window.pageYOffset > 300;
        
        if (shouldShow && !scrollToTopVisible) {
            scrollBtn.style.opacity = '1';
            scrollBtn.style.transform = 'translateY(0)';
            scrollBtn.style.pointerEvents = 'auto';
            scrollToTopVisible = true;
        } else if (!shouldShow && scrollToTopVisible) {
            scrollBtn.style.opacity = '0';
            scrollBtn.style.transform = 'translateY(100px)';
            scrollBtn.style.pointerEvents = 'none';
            scrollToTopVisible = false;
        }
    });
    
    // Handle click
    scrollBtn.addEventListener('click', () => {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
}

// ============================================================================
// PERFORMANCE MONITORING & OPTIMIZATION
// ============================================================================

function initPerformanceMonitoring() {
    // Monitor Core Web Vitals
    if ('web-vital' in window) {
        // Largest Contentful Paint
        getLCP(console.log);
        
        // First Input Delay
        getFID(console.log);
        
        // Cumulative Layout Shift
        getCLS(console.log);
    }
    
    // Monitor page load time
    window.addEventListener('load', () => {
        const loadTime = performance.timing.loadEventEnd - performance.timing.navigationStart;
        console.log(`📊 Page load time: ${loadTime}ms`);
        
        // Track slow loads
        if (loadTime > 3000) {
            console.warn('⚠️ Slow page load detected');
        }
    });
}

// ============================================================================
// ACCESSIBILITY ENHANCEMENTS
// ============================================================================

// Add keyboard navigation improvements
document.addEventListener('keydown', function(e) {
    // Escape key to close modals/dropdowns
    if (e.key === 'Escape') {
        const activeModal = document.querySelector('.modal.show');
        if (activeModal) {
            const modalInstance = bootstrap.Modal.getInstance(activeModal);
            if (modalInstance) modalInstance.hide();
        }
        
        const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
        openDropdowns.forEach(dropdown => {
            const dropdownInstance = bootstrap.Dropdown.getInstance(dropdown.previousElementSibling);
            if (dropdownInstance) dropdownInstance.hide();
        });
    }
});

// Announce page changes to screen readers
function announcePageChange(message) {
    const announcement = document.createElement('div');
    announcement.setAttribute('aria-live', 'polite');
    announcement.setAttribute('aria-atomic', 'true');
    announcement.className = 'sr-only';
    announcement.textContent = message;
    
    document.body.appendChild(announcement);
    
    setTimeout(() => {
        document.body.removeChild(announcement);
    }, 1000);
}

// Export new classes for global use
window.StickyCTA = StickyCTA;
window.FormEnhancements = FormEnhancements;
window.ImageOptimization = ImageOptimization;
window.Notifications = Notifications;