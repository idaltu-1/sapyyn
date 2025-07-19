/**
 * Sapyyn Enhanced UI JavaScript
 * Site-wide improvements for user experience and interactivity
 */

// Global configuration
window.SapyynUI = {
    config: {
        animationDuration: 300,
        debounceDelay: 250,
        scrollOffset: 80,
        breakpoints: {
            sm: 640,
            md: 768,
            lg: 1024,
            xl: 1280
        }
    },
    
    // Utility functions
    utils: {
        // Debounce function for performance
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
        
        // Throttle function for scroll events
        throttle(func, limit) {
            let inThrottle;
            return function() {
                const args = arguments;
                const context = this;
                if (!inThrottle) {
                    func.apply(context, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },
        
        // Check if element is in viewport
        isInViewport(element, offset = 0) {
            const rect = element.getBoundingClientRect();
            return (
                rect.top >= -offset &&
                rect.left >= 0 &&
                rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) + offset &&
                rect.right <= (window.innerWidth || document.documentElement.clientWidth)
            );
        },
        
        // Smooth scroll to element
        scrollTo(target, offset = 0) {
            const element = typeof target === 'string' ? document.querySelector(target) : target;
            if (!element) return;
            
            const targetPosition = element.offsetTop - offset;
            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        },
        
        // Get current breakpoint
        getCurrentBreakpoint() {
            const width = window.innerWidth;
            if (width >= this.config.breakpoints.xl) return 'xl';
            if (width >= this.config.breakpoints.lg) return 'lg';
            if (width >= this.config.breakpoints.md) return 'md';
            if (width >= this.config.breakpoints.sm) return 'sm';
            return 'xs';
        },
        
        // Format currency
        formatCurrency(amount, currency = 'USD') {
            return new Intl.NumberFormat('en-US', {
                style: 'currency',
                currency: currency
            }).format(amount);
        },
        
        // Format date
        formatDate(date, options = {}) {
            const defaultOptions = {
                year: 'numeric',
                month: 'short',
                day: 'numeric'
            };
            return new Intl.DateTimeFormat('en-US', { ...defaultOptions, ...options }).format(new Date(date));
        }
    }
};

// Enhanced Navigation
class EnhancedNavigation {
    constructor() {
        this.navbar = document.querySelector('.navbar');
        this.navToggler = document.querySelector('.navbar-toggler');
        this.navCollapse = document.querySelector('.navbar-collapse');
        this.dropdowns = document.querySelectorAll('.dropdown');
        this.lastScrollY = window.scrollY;
        
        this.init();
    }
    
    init() {
        this.setupScrollBehavior();
        this.setupMobileMenu();
        this.setupDropdowns();
        this.setupActiveLinks();
    }
    
    setupScrollBehavior() {
        const handleScroll = SapyynUI.utils.throttle(() => {
            const currentScrollY = window.scrollY;
            
            // Add/remove scrolled class
            if (currentScrollY > 50) {
                this.navbar?.classList.add('navbar-scrolled');
            } else {
                this.navbar?.classList.remove('navbar-scrolled');
            }
            
            // Hide/show navbar on scroll (mobile)
            if (window.innerWidth <= SapyynUI.config.breakpoints.md) {
                if (currentScrollY > this.lastScrollY && currentScrollY > 100) {
                    this.navbar?.classList.add('navbar-hidden');
                } else {
                    this.navbar?.classList.remove('navbar-hidden');
                }
            }
            
            this.lastScrollY = currentScrollY;
        }, 100);
        
        window.addEventListener('scroll', handleScroll);
    }
    
    setupMobileMenu() {
        if (!this.navToggler || !this.navCollapse) return;
        
        this.navToggler.addEventListener('click', (e) => {
            e.preventDefault();
            this.toggleMobileMenu();
        });
        
        // Close mobile menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.navbar?.contains(e.target) && this.navCollapse?.classList.contains('show')) {
                this.closeMobileMenu();
            }
        });
        
        // Close mobile menu on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.navCollapse?.classList.contains('show')) {
                this.closeMobileMenu();
            }
        });
    }
    
    toggleMobileMenu() {
        this.navCollapse?.classList.toggle('show');
        this.navToggler?.setAttribute('aria-expanded', 
            this.navCollapse?.classList.contains('show') ? 'true' : 'false'
        );
    }
    
    closeMobileMenu() {
        this.navCollapse?.classList.remove('show');
        this.navToggler?.setAttribute('aria-expanded', 'false');
    }
    
    setupDropdowns() {
        this.dropdowns.forEach(dropdown => {
            const toggle = dropdown.querySelector('.dropdown-toggle');
            const menu = dropdown.querySelector('.dropdown-menu');
            
            if (!toggle || !menu) return;
            
            // Desktop hover behavior
            if (window.innerWidth > SapyynUI.config.breakpoints.md) {
                dropdown.addEventListener('mouseenter', () => {
                    menu.classList.add('show');
                });
                
                dropdown.addEventListener('mouseleave', () => {
                    menu.classList.remove('show');
                });
            }
            
            // Click behavior for all devices
            toggle.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                
                // Close other dropdowns
                this.dropdowns.forEach(otherDropdown => {
                    if (otherDropdown !== dropdown) {
                        otherDropdown.querySelector('.dropdown-menu')?.classList.remove('show');
                    }
                });
                
                menu.classList.toggle('show');
            });
        });
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', () => {
            this.dropdowns.forEach(dropdown => {
                dropdown.querySelector('.dropdown-menu')?.classList.remove('show');
            });
        });
    }
    
    setupActiveLinks() {
        const currentPath = window.location.pathname;
        const navLinks = document.querySelectorAll('.nav-link');
        
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.classList.add('active');
            }
        });
    }
}

// Enhanced Forms
class EnhancedForms {
    constructor() {
        this.forms = document.querySelectorAll('form');
        this.init();
    }
    
    init() {
        this.setupFormValidation();
        this.setupPasswordToggles();
        this.setupFileUploads();
        this.setupAutoSave();
    }
    
    setupFormValidation() {
        this.forms.forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            
            inputs.forEach(input => {
                // Real-time validation
                input.addEventListener('blur', () => this.validateField(input));
                input.addEventListener('input', SapyynUI.utils.debounce(() => {
                    if (input.classList.contains('is-invalid')) {
                        this.validateField(input);
                    }
                }, 500));
            });
            
            // Form submission validation
            form.addEventListener('submit', (e) => {
                if (!this.validateForm(form)) {
                    e.preventDefault();
                    e.stopPropagation();
                }
            });
        });
    }
    
    validateField(field) {
        const value = field.value.trim();
        const type = field.type;
        const required = field.hasAttribute('required');
        let isValid = true;
        let message = '';
        
        // Remove existing validation classes
        field.classList.remove('is-valid', 'is-invalid');
        
        // Required field validation
        if (required && !value) {
            isValid = false;
            message = 'This field is required';
        }
        
        // Email validation
        else if (type === 'email' && value) {
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (!emailRegex.test(value)) {
                isValid = false;
                message = 'Please enter a valid email address';
            }
        }
        
        // Password validation
        else if (type === 'password' && value) {
            if (value.length < 8) {
                isValid = false;
                message = 'Password must be at least 8 characters long';
            }
        }
        
        // Phone validation
        else if (field.name === 'phone' && value) {
            const phoneRegex = /^[\+]?[1-9][\d]{0,15}$/;
            if (!phoneRegex.test(value.replace(/[\s\-\(\)]/g, ''))) {
                isValid = false;
                message = 'Please enter a valid phone number';
            }
        }
        
        // Apply validation result
        field.classList.add(isValid ? 'is-valid' : 'is-invalid');
        
        // Show/hide feedback message
        this.showFieldFeedback(field, message, isValid);
        
        return isValid;
    }
    
    validateForm(form) {
        const inputs = form.querySelectorAll('input, textarea, select');
        let isFormValid = true;
        
        inputs.forEach(input => {
            if (!this.validateField(input)) {
                isFormValid = false;
            }
        });
        
        return isFormValid;
    }
    
    showFieldFeedback(field, message, isValid) {
        let feedback = field.parentNode.querySelector('.invalid-feedback, .valid-feedback');
        
        if (!feedback) {
            feedback = document.createElement('div');
            field.parentNode.appendChild(feedback);
        }
        
        feedback.className = isValid ? 'valid-feedback' : 'invalid-feedback';
        feedback.textContent = message;
        feedback.style.display = message ? 'block' : 'none';
    }
    
    setupPasswordToggles() {
        const passwordFields = document.querySelectorAll('input[type="password"]');
        
        passwordFields.forEach(field => {
            const wrapper = field.parentNode;
            if (wrapper.querySelector('.password-toggle')) return;
            
            const toggle = document.createElement('button');
            toggle.type = 'button';
            toggle.className = 'password-toggle';
            toggle.innerHTML = '<i class="bi bi-eye"></i>';
            toggle.setAttribute('aria-label', 'Toggle password visibility');
            
            wrapper.style.position = 'relative';
            wrapper.appendChild(toggle);
            
            toggle.addEventListener('click', () => {
                const isPassword = field.type === 'password';
                field.type = isPassword ? 'text' : 'password';
                toggle.innerHTML = isPassword ? '<i class="bi bi-eye-slash"></i>' : '<i class="bi bi-eye"></i>';
            });
        });
    }
    
    setupFileUploads() {
        const fileInputs = document.querySelectorAll('input[type="file"]');
        
        fileInputs.forEach(input => {
            const wrapper = document.createElement('div');
            wrapper.className = 'file-upload-wrapper';
            
            input.parentNode.insertBefore(wrapper, input);
            wrapper.appendChild(input);
            
            const label = document.createElement('label');
            label.className = 'file-upload-label';
            label.setAttribute('for', input.id);
            label.innerHTML = `
                <i class="bi bi-cloud-upload"></i>
                <span>Choose file or drag here</span>
                <small>Maximum file size: 16MB</small>
            `;
            wrapper.appendChild(label);
            
            // Drag and drop functionality
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                wrapper.addEventListener(eventName, this.preventDefaults, false);
            });
            
            ['dragenter', 'dragover'].forEach(eventName => {
                wrapper.addEventListener(eventName, () => wrapper.classList.add('dragover'), false);
            });
            
            ['dragleave', 'drop'].forEach(eventName => {
                wrapper.addEventListener(eventName, () => wrapper.classList.remove('dragover'), false);
            });
            
            wrapper.addEventListener('drop', (e) => {
                const files = e.dataTransfer.files;
                input.files = files;
                this.updateFileLabel(input, label);
            });
            
            input.addEventListener('change', () => {
                this.updateFileLabel(input, label);
            });
        });
    }
    
    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    updateFileLabel(input, label) {
        const files = input.files;
        if (files.length > 0) {
            const fileName = files.length === 1 ? files[0].name : `${files.length} files selected`;
            label.querySelector('span').textContent = fileName;
            label.classList.add('has-file');
        } else {
            label.querySelector('span').textContent = 'Choose file or drag here';
            label.classList.remove('has-file');
        }
    }
    
    setupAutoSave() {
        const autoSaveForms = document.querySelectorAll('[data-autosave]');
        
        autoSaveForms.forEach(form => {
            const inputs = form.querySelectorAll('input, textarea, select');
            const formId = form.id || 'autosave-form';
            
            // Load saved data
            this.loadFormData(form, formId);
            
            // Save data on input
            inputs.forEach(input => {
                input.addEventListener('input', SapyynUI.utils.debounce(() => {
                    this.saveFormData(form, formId);
                }, 1000));
            });
        });
    }
    
    saveFormData(form, formId) {
        const formData = new FormData(form);
        const data = {};
        
        for (let [key, value] of formData.entries()) {
            data[key] = value;
        }
        
        localStorage.setItem(`sapyyn-autosave-${formId}`, JSON.stringify(data));
        
        // Show save indicator
        this.showSaveIndicator(form);
    }
    
    loadFormData(form, formId) {
        const savedData = localStorage.getItem(`sapyyn-autosave-${formId}`);
        
        if (savedData) {
            try {
                const data = JSON.parse(savedData);
                
                Object.keys(data).forEach(key => {
                    const input = form.querySelector(`[name="${key}"]`);
                    if (input && input.type !== 'password') {
                        input.value = data[key];
                    }
                });
            } catch (e) {
                console.warn('Failed to load autosaved form data:', e);
            }
        }
    }
    
    showSaveIndicator(form) {
        let indicator = form.querySelector('.autosave-indicator');
        
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.className = 'autosave-indicator';
            indicator.innerHTML = '<i class="bi bi-check-circle"></i> Saved';
            form.appendChild(indicator);
        }
        
        indicator.style.display = 'block';
        indicator.style.opacity = '1';
        
        setTimeout(() => {
            indicator.style.opacity = '0';
            setTimeout(() => {
                indicator.style.display = 'none';
            }, 300);
        }, 2000);
    }
}

// Enhanced Modals
class EnhancedModals {
    constructor() {
        this.modals = document.querySelectorAll('.modal');
        this.init();
    }
    
    init() {
        this.setupModalTriggers();
        this.setupModalBehavior();
    }
    
    setupModalTriggers() {
        const triggers = document.querySelectorAll('[data-bs-toggle="modal"]');
        
        triggers.forEach(trigger => {
            trigger.addEventListener('click', (e) => {
                e.preventDefault();
                const targetId = trigger.getAttribute('data-bs-target');
                const modal = document.querySelector(targetId);
                if (modal) {
                    this.showModal(modal);
                }
            });
        });
    }
    
    setupModalBehavior() {
        this.modals.forEach(modal => {
            const closeButtons = modal.querySelectorAll('[data-bs-dismiss="modal"]');
            
            closeButtons.forEach(button => {
                button.addEventListener('click', () => this.hideModal(modal));
            });
            
            // Close on backdrop click
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.hideModal(modal);
                }
            });
            
            // Close on escape key
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape' && modal.classList.contains('show')) {
                    this.hideModal(modal);
                }
            });
        });
    }
    
    showModal(modal) {
        document.body.style.overflow = 'hidden';
        modal.style.display = 'block';
        modal.classList.add('show');
        
        // Focus management
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        if (focusableElements.length > 0) {
            focusableElements[0].focus();
        }
        
        // Trigger shown event
        modal.dispatchEvent(new CustomEvent('shown.bs.modal'));
    }
    
    hideModal(modal) {
        document.body.style.overflow = '';
        modal.classList.remove('show');
        
        setTimeout(() => {
            modal.style.display = 'none';
        }, 300);
        
        // Trigger hidden event
        modal.dispatchEvent(new CustomEvent('hidden.bs.modal'));
    }
}

// Enhanced Alerts
class EnhancedAlerts {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupDismissibleAlerts();
    }
    
    setupDismissibleAlerts() {
        const alerts = document.querySelectorAll('.alert-dismissible');
        
        alerts.forEach(alert => {
            const closeButton = alert.querySelector('.btn-close');
            
            if (closeButton) {
                closeButton.addEventListener('click', () => {
                    this.dismissAlert(alert);
                });
            }
            
            // Auto-dismiss after 5 seconds for success alerts
            if (alert.classList.contains('alert-success')) {
                setTimeout(() => {
                    this.dismissAlert(alert);
                }, 5000);
            }
        });
    }
    
    dismissAlert(alert) {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        
        setTimeout(() => {
            alert.remove();
        }, 300);
    }
    
    static show(message, type = 'info', duration = 5000) {
        const alertContainer = document.querySelector('.alert-container') || document.body;
        
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" aria-label="Close"></button>
        `;
        
        alertContainer.appendChild(alert);
        
        // Setup dismiss functionality
        const closeButton = alert.querySelector('.btn-close');
        closeButton.addEventListener('click', () => {
            new EnhancedAlerts().dismissAlert(alert);
        });
        
        // Auto-dismiss
        if (duration > 0) {
            setTimeout(() => {
                new EnhancedAlerts().dismissAlert(alert);
            }, duration);
        }
        
        return alert;
    }
}

// Enhanced Tables
class EnhancedTables {
    constructor() {
        this.tables = document.querySelectorAll('.table-enhanced');
        this.init();
    }
    
    init() {
        this.tables.forEach(table => {
            this.setupSorting(table);
            this.setupFiltering(table);
            this.setupPagination(table);
        });
    }
    
    setupSorting(table) {
        const headers = table.querySelectorAll('th[data-sortable]');
        
        headers.forEach(header => {
            header.style.cursor = 'pointer';
            header.innerHTML += ' <i class="bi bi-arrow-down-up sort-icon"></i>';
            
            header.addEventListener('click', () => {
                this.sortTable(table, header);
            });
        });
    }
    
    sortTable(table, header) {
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        const columnIndex = Array.from(header.parentNode.children).indexOf(header);
        const isAscending = !header.classList.contains('sort-asc');
        
        // Remove sort classes from all headers
        table.querySelectorAll('th').forEach(th => {
            th.classList.remove('sort-asc', 'sort-desc');
        });
        
        // Add sort class to current header
        header.classList.add(isAscending ? 'sort-asc' : 'sort-desc');
        
        // Sort rows
        rows.sort((a, b) => {
            const aValue = a.children[columnIndex].textContent.trim();
            const bValue = b.children[columnIndex].textContent.trim();
            
            // Try to parse as numbers
            const aNum = parseFloat(aValue);
            const bNum = parseFloat(bValue);
            
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return isAscending ? aNum - bNum : bNum - aNum;
            }
            
            // String comparison
            return isAscending ? 
                aValue.localeCompare(bValue) : 
                bValue.localeCompare(aValue);
        });
        
        // Reorder rows in DOM
        rows.forEach(row => tbody.appendChild(row));
    }
    
    setupFiltering(table) {
        const filterInput = table.parentNode.querySelector('.table-filter');
        if (!filterInput) return;
        
        filterInput.addEventListener('input', SapyynUI.utils.debounce(() => {
            this.filterTable(table, filterInput.value);
        }, 300));
    }
    
    filterTable(table, searchTerm) {
        const tbody = table.querySelector('tbody');
        const rows = tbody.querySelectorAll('tr');
        const term = searchTerm.toLowerCase();
        
        rows.forEach(row => {
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(term) ? '' : 'none';
        });
    }
    
    setupPagination(table) {
        const paginationContainer = table.parentNode.querySelector('.table-pagination');
        if (!paginationContainer) return;
        
        const rowsPerPage = parseInt(table.dataset.rowsPerPage) || 10;
        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        this.paginateTable(table, rows, rowsPerPage, paginationContainer);
    }
    
    paginateTable(table, rows, rowsPerPage, container) {
        const totalPages = Math.ceil(rows.length / rowsPerPage);
        let currentPage = 1;
        
        const showPage = (page) => {
            const start = (page - 1) * rowsPerPage;
            const end = start + rowsPerPage;
            
            rows.forEach((row, index) => {
                row.style.display = (index >= start && index < end) ? '' : 'none';
            });
            
            currentPage = page;
            updatePaginationControls();
        };
        
        const updatePaginationControls = () => {
            container.innerHTML = '';
            
            // Previous button
            const prevBtn = document.createElement('button');
            prevBtn.textContent = 'Previous';
            prevBtn.className = 'btn btn-sm btn-outline-primary';
            prevBtn.disabled = currentPage === 1;
            prevBtn.addEventListener('click', () => showPage(currentPage - 1));
            container.appendChild(prevBtn);
            
            // Page numbers
            for (let i = 1; i <= totalPages; i++) {
                const pageBtn = document.createElement('button');
                pageBtn.textContent = i;
                pageBtn.className = `btn btn-sm ${i === currentPage ? 'btn-primary' : 'btn-outline-primary'}`;
                pageBtn.addEventListener('click', () => showPage(i));
                container.appendChild(pageBtn);
            }
            
            // Next button
            const nextBtn = document.createElement('button');
            nextBtn.textContent = 'Next';
            nextBtn.className = 'btn btn-sm btn-outline-primary';
            nextBtn.disabled = currentPage === totalPages;
            nextBtn.addEventListener('click', () => showPage(currentPage + 1));
            container.appendChild(nextBtn);
        };
        
        showPage(1);
    }
}

// Performance Monitor
class PerformanceMonitor {
    constructor() {
        this.metrics = {};
        this.init();
    }
    
    init() {
        this.measurePageLoad();
        this.measureInteractions();
        this.setupErrorTracking();
    }
    
    measurePageLoad() {
        window.addEventListener('load', () => {
            const navigation = performance.getEntriesByType('navigation')[0];
            
            this.metrics.pageLoad = {
                domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                loadComplete: navigation.loadEventEnd - navigation.loadEventStart,
                totalTime: navigation.loadEventEnd - navigation.fetchStart
            };
            
            // Report to analytics if available
            if (window.gtag) {
                gtag('event', 'page_load_time', {
                    value: Math.round(this.metrics.pageLoad.totalTime),
                    custom_parameter_1: 'performance'
                });
            }
        });
    }
    
    measureInteractions() {
        // Measure form submissions
        document.addEventListener('submit', (e) => {
            const startTime = performance.now();
            
            setTimeout(() => {
                const endTime = performance.now();
                const duration = endTime - startTime;
                
                if (window.gtag) {
                    gtag('event', 'form_submission_time', {
                        value: Math.round(duration),
                        form_id: e.target.id || 'unknown'
                    });
                }
            }, 0);
        });
        
        // Measure button clicks
        document.addEventListener('click', (e) => {
            if (e.target.matches('button, .btn')) {
                const startTime = performance.now();
                
                requestAnimationFrame(() => {
                    const endTime = performance.now();
                    const duration = endTime - startTime;
                    
                    if (duration > 100) { // Only report slow interactions
                        if (window.gtag) {
                            gtag('event', 'slow_interaction', {
                                value: Math.round(duration),
                                element_type: 'button'
                            });
                        }
                    }
                });
            }
        });
    }
    
    setupErrorTracking() {
        window.addEventListener('error', (e) => {
            if (window.gtag) {
                gtag('event', 'javascript_error', {
                    error_message: e.message,
                    error_filename: e.filename,
                    error_line: e.lineno
                });
            }
        });
        
        window.addEventListener('unhandledrejection', (e) => {
            if (window.gtag) {
                gtag('event', 'promise_rejection', {
                    error_message: e.reason?.message || 'Unknown promise rejection'
                });
            }
        });
    }
}

// Accessibility Enhancements
class AccessibilityEnhancements {
    constructor() {
        this.init();
    }
    
    init() {
        this.setupKeyboardNavigation();
        this.setupFocusManagement();
        this.setupScreenReaderSupport();
        this.setupReducedMotion();
    }
    
    setupKeyboardNavigation() {
        // Skip to main content link
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.textContent = 'Skip to main content';
        skipLink.className = 'skip-link sr-only';
        skipLink.addEventListener('focus', () => skipLink.classList.remove('sr-only'));
        skipLink.addEventListener('blur', () => skipLink.classList.add('sr-only'));
        
        document.body.insertBefore(skipLink, document.body.firstChild);
        
        // Enhanced keyboard navigation for dropdowns
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                // Close any open dropdowns or modals
                document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
                    menu.classList.remove('show');
                });
                
                document.querySelectorAll('.modal.show').forEach(modal => {
                    new EnhancedModals().hideModal(modal);
                });
            }
        });
    }
    
    setupFocusManagement() {
        // Ensure focus is visible
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });
        
        document.addEventListener('mousedown', () => {
            document.body.classList.remove('keyboard-navigation');
        });
        
        // Focus trap for modals
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Tab') {
                const modal = document.querySelector('.modal.show');
                if (modal) {
                    this.trapFocus(e, modal);
                }
            }
        });
    }
    
    trapFocus(e, container) {
        const focusableElements = container.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        
        if (focusableElements.length === 0) return;
        
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];
        
        if (e.shiftKey) {
            if (document.activeElement === firstElement) {
                e.preventDefault();
                lastElement.focus();
            }
        } else {
            if (document.activeElement === lastElement) {
                e.preventDefault();
                firstElement.focus();
            }
        }
    }
    
    setupScreenReaderSupport() {
        // Add ARIA labels to interactive elements without them
        const interactiveElements = document.querySelectorAll('button, [role="button"], input, select, textarea');
        
        interactiveElements.forEach(element => {
            if (!element.getAttribute('aria-label') && !element.getAttribute('aria-labelledby')) {
                const text = element.textContent?.trim() || element.value || element.placeholder;
                if (text) {
                    element.setAttribute('aria-label', text);
                }
            }
        });
        
        // Add live region for dynamic content
        if (!document.querySelector('#live-region')) {
            const liveRegion = document.createElement('div');
            liveRegion.id = 'live-region';
            liveRegion.setAttribute('aria-live', 'polite');
            liveRegion.setAttribute('aria-atomic', 'true');
            liveRegion.className = 'sr-only';
            document.body.appendChild(liveRegion);
        }
    }
    
    setupReducedMotion() {
        // Respect user's motion preferences
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
        
        if (prefersReducedMotion.matches) {
            document.documentElement.style.setProperty('--transition-fast', '0ms');
            document.documentElement.style.setProperty('--transition-base', '0ms');
            document.documentElement.style.setProperty('--transition-slow', '0ms');
        }
        
        prefersReducedMotion.addEventListener('change', (e) => {
            if (e.matches) {
                document.documentElement.style.setProperty('--transition-fast', '0ms');
                document.documentElement.style.setProperty('--transition-base', '0ms');
                document.documentElement.style.setProperty('--transition-slow', '0ms');
            } else {
                document.documentElement.style.removeProperty('--transition-fast');
                document.documentElement.style.removeProperty('--transition-base');
                document.documentElement.style.removeProperty('--transition-slow');
            }
        });
    }
    
    static announceToScreenReader(message) {
        const liveRegion = document.querySelector('#live-region');
        if (liveRegion) {
            liveRegion.textContent = message;
        }
    }
}

// Initialize all enhancements when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Initialize all enhancement classes
    new EnhancedNavigation();
    new EnhancedForms();
    new EnhancedModals();
    new EnhancedAlerts();
    new EnhancedTables();
    new PerformanceMonitor();
    new AccessibilityEnhancements();
    
    // Add global utility functions to window
    window.SapyynUI.showAlert = EnhancedAlerts.show;
    window.SapyynUI.announceToScreenReader = AccessibilityEnhancements.announceToScreenReader;
    
    console.log('Sapyyn Enhanced UI initialized successfully');
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        EnhancedNavigation,
        EnhancedForms,
        EnhancedModals,
        EnhancedAlerts,
        EnhancedTables,
        PerformanceMonitor,
        AccessibilityEnhancements
    };
}
