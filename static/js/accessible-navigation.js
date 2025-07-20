/**
 * Sapyyn Accessible Navigation - WCAG 2.1 Compliant
 * Handles keyboard navigation, focus management, and screen reader support
 */

(function() {
    'use strict';

    // Accessibility utilities
    const Accessibility = {
        // Initialize all accessibility features
        init: function() {
            this.setupSkipLinks();
            this.setupKeyboardNavigation();
            this.setupFocusManagement();
            this.setupFormValidation();
            this.setupLiveRegions();
            this.setupMobileMenu();
        },

        // Skip link functionality
        setupSkipLinks: function() {
            const skipLink = document.querySelector('.skip-link');
            if (skipLink) {
                skipLink.addEventListener('click', function(e) {
                    e.preventDefault();
                    const mainContent = document.getElementById('main-content');
                    if (mainContent) {
                        mainContent.setAttribute('tabindex', '-1');
                        mainContent.focus();
                        mainContent.scrollIntoView({ behavior: 'smooth' });
                    }
                });
            }
        },

        // Keyboard navigation support
        setupKeyboardNavigation: function() {
            // Handle keyboard navigation for navigation menu
            const navMenu = document.querySelector('.nav-menu');
            if (navMenu) {
                const navLinks = navMenu.querySelectorAll('a, button');
                navLinks.forEach((link, index) => {
                    link.addEventListener('keydown', function(e) {
                        switch(e.key) {
                            case 'ArrowDown':
                            case 'ArrowRight':
                                e.preventDefault();
                                const nextIndex = (index + 1) % navLinks.length;
                                navLinks[nextIndex].focus();
                                break;
                            case 'ArrowUp':
                            case 'ArrowLeft':
                                e.preventDefault();
                                const prevIndex = (index - 1 + navLinks.length) % navLinks.length;
                                navLinks[prevIndex].focus();
                                break;
                            case 'Home':
                                e.preventDefault();
                                navLinks[0].focus();
                                break;
                            case 'End':
                                e.preventDefault();
                                navLinks[navLinks.length - 1].focus();
                                break;
                        }
                    });
                });
            }
        },

        // Focus management for modals and dialogs
        setupFocusManagement: function() {
            // Trap focus within modals
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                const focusableElements = modal.querySelectorAll(
                    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                );
                
                if (focusableElements.length > 0) {
                    const firstFocusable = focusableElements[0];
                    const lastFocusable = focusableElements[focusableElements.length - 1];
                    
                    modal.addEventListener('keydown', function(e) {
                        if (e.key === 'Tab') {
                            if (e.shiftKey) {
                                if (document.activeElement === firstFocusable) {
                                    e.preventDefault();
                                    lastFocusable.focus();
                                }
                            } else {
                                if (document.activeElement === lastFocusable) {
                                    e.preventDefault();
                                    firstFocusable.focus();
                                }
                            }
                        }
                        
                        if (e.key === 'Escape') {
                            this.closeModal(modal);
                        }
                    }.bind(this));
                }
            });
        },

        // Form validation with accessibility
        setupFormValidation: function() {
            const forms = document.querySelectorAll('form');
            forms.forEach(form => {
                form.addEventListener('submit', function(e) {
                    this.validateForm(form);
                }.bind(this));
                
                // Real-time validation
                const inputs = form.querySelectorAll('input, select, textarea');
                inputs.forEach(input => {
                    input.addEventListener('blur', function() {
                        this.validateField(input);
                    }.bind(this));
                    
                    input.addEventListener('input', function() {
                        this.clearFieldError(input);
                    }.bind(this));
                });
            });
        },

        // Live regions for announcements
        setupLiveRegions: function() {
            // Create live region for announcements
            if (!document.getElementById('announcements')) {
                const liveRegion = document.createElement('div');
                liveRegion.id = 'announcements';
                liveRegion.setAttribute('aria-live', 'polite');
                liveRegion.setAttribute('aria-atomic', 'true');
                liveRegion.className = 'sr-only';
                document.body.appendChild(liveRegion);
            }
        },

        // Mobile menu accessibility
        setupMobileMenu: function() {
            const mobileToggle = document.querySelector('.mobile-menu-toggle');
            const navMenu = document.querySelector('.nav-menu');
            
            if (mobileToggle && navMenu) {
                mobileToggle.addEventListener('click', function() {
                    const isExpanded = mobileToggle.getAttribute('aria-expanded') === 'true';
                    mobileToggle.setAttribute('aria-expanded', !isExpanded);
                    navMenu.classList.toggle('active');
                    
                    // Announce menu state
                    this.announce(isExpanded ? 'Menu closed' : 'Menu opened');
                }.bind(this));
            }
        },

        // Form validation methods
        validateForm: function(form) {
            const inputs = form.querySelectorAll('input, select, textarea');
            let isValid = true;
            
            inputs.forEach(input => {
                if (!this.validateField(input)) {
                    isValid = false;
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                this.announce('Please correct the errors in the form');
            }
        },

        validateField: function(field) {
            const errorElement = document.getElementById(`${field.id}-error`);
            let isValid = true;
            let errorMessage = '';
            
            // Required field validation
            if (field.hasAttribute('required') && !field.value.trim()) {
                errorMessage = `${this.getFieldLabel(field)} is required`;
                isValid = false;
            }
            
            // Email validation
            if (field.type === 'email' && field.value && !this.isValidEmail(field.value)) {
                errorMessage = 'Please enter a valid email address';
                isValid = false;
            }
            
            // Phone validation
            if (field.type === 'tel' && field.value && !this.isValidPhone(field.value)) {
                errorMessage = 'Please enter a valid phone number';
                isValid = false;
            }
            
            // Password validation
            if (field.type === 'password' && field.value && field.value.length < 8) {
                errorMessage = 'Password must be at least 8 characters';
                isValid = false;
            }
            
            // Display error
            if (errorMessage) {
                this.showFieldError(field, errorMessage);
            } else {
                this.clearFieldError(field);
            }
            
            return isValid;
        },

        showFieldError: function(field, message) {
            const errorElement = document.getElementById(`${field.id}-error`);
            if (errorElement) {
                errorElement.textContent = message;
                errorElement.setAttribute('aria-live', 'polite');
                field.setAttribute('aria-invalid', 'true');
                field.setAttribute('aria-describedby', `${field.id}-error`);
            }
        },

        clearFieldError: function(field) {
            const errorElement = document.getElementById(`${field.id}-error`);
            if (errorElement) {
                errorElement.textContent = '';
                field.removeAttribute('aria-invalid');
                field.removeAttribute('aria-describedby');
            }
        },

        getFieldLabel: function(field) {
            const label = document.querySelector(`label[for="${field.id}"]`) || 
                         field.closest('label') || 
                         field.previousElementSibling;
            return label ? label.textContent.trim() : 'This field';
        },

        isValidEmail: function(email) {
            return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
        },

        isValidPhone: function(phone) {
            return /^[\d\s\-\+\(\)]+$/.test(phone);
        },

        // Modal management
        openModal: function(modalId) {
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.style.display = 'flex';
                modal.setAttribute('aria-hidden', 'false');
                
                // Focus first focusable element
                const firstFocusable = modal.querySelector('button, [href], input, select, textarea');
                if (firstFocusable) {
                    firstFocusable.focus();
                }
                
                // Announce modal
                this.announce('Modal opened');
            }
        },

        closeModal: function(modal) {
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
            this.announce('Modal closed');
        },

        // Announcement utility
        announce: function(message) {
            const liveRegion = document.getElementById('announcements');
            if (liveRegion) {
                liveRegion.textContent = message;
                setTimeout(() => {
                    liveRegion.textContent = '';
                }, 1000);
            }
        },

        // Utility methods
        trapFocus: function(element) {
            const focusableElements = element.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            if (focusableElements.length > 0) {
                focusableElements[0].focus();
            }
        },

        releaseFocus: function() {
            document.body.focus();
        }
    };

    // Initialize accessibility features when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            Accessibility.init();
        });
    } else {
        Accessibility.init();
    }

    // Export for global use
    window.Accessibility = Accessibility;
})();
