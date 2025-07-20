// Main JavaScript for Sapyyn Landing Page

class SapyynLanding {
    constructor() {
        this.init();
    }

    init() {
        this.setupScrollEffects();
        this.setupNavigation();
        this.setupAnimations();
        this.setupCTATracking();
    }

    // Setup scroll effects for navbar
    setupScrollEffects() {
        const navbar = document.querySelector('.navbar');
        
        window.addEventListener('scroll', () => {
            if (window.scrollY > 100) {
                navbar.classList.add('scrolled');
                navbar.style.background = 'rgba(255, 255, 255, 0.95)';
                navbar.style.backdropFilter = 'blur(10px)';
            } else {
                navbar.classList.remove('scrolled');
                navbar.style.background = '';
                navbar.style.backdropFilter = '';
            }
        });
    }

    // Setup smooth navigation
    setupNavigation() {
        // Smooth scroll for anchor links
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', function (e) {
                e.preventDefault();
                const target = document.querySelector(this.getAttribute('href'));
                if (target) {
                    const offsetTop = target.offsetTop - 80; // Account for navbar height
                    window.scrollTo({
                        top: offsetTop,
                        behavior: 'smooth'
                    });
                }
            });
        });

        // Mobile menu handling
        const navbarToggler = document.querySelector('.navbar-toggler');
        const navbarCollapse = document.querySelector('.navbar-collapse');
        
        if (navbarToggler && navbarCollapse) {
            // Close mobile menu when clicking on links
            navbarCollapse.querySelectorAll('.nav-link').forEach(link => {
                link.addEventListener('click', () => {
                    if (navbarCollapse.classList.contains('show')) {
                        navbarToggler.click();
                    }
                });
            });
        }
    }

    // Setup intersection observer for animations
    setupAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('fade-in');
                }
            });
        }, observerOptions);

        // Observe elements for animation
        document.querySelectorAll('.feature-card, .step-card, .pricing-card').forEach(el => {
            observer.observe(el);
        });
    }

    // Setup CTA tracking
    setupCTATracking() {
        // Track button clicks
        document.querySelectorAll('a[href*="signup"], a[href*="portal"]').forEach(button => {
            button.addEventListener('click', (e) => {
                const buttonText = e.target.textContent.trim();
                const href = e.target.href;
                
                // Analytics tracking would go here
                console.log('CTA clicked:', { buttonText, href });
                
                // Add some visual feedback
                this.addClickFeedback(e.target);
            });
        });

        // Track pricing plan selections
        document.querySelectorAll('a[href*="plan="]').forEach(button => {
            button.addEventListener('click', (e) => {
                const url = new URL(e.target.href);
                const plan = url.searchParams.get('plan');
                
                console.log('Plan selected:', plan);
            });
        });
    }

    // Add visual feedback for button clicks
    addClickFeedback(element) {
        element.style.transform = 'scale(0.95)';
        element.style.transition = 'transform 0.1s ease';
        
        setTimeout(() => {
            element.style.transform = '';
        }, 100);
    }

    // Show notification (can be used for announcements)
    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = `
            top: 20px;
            right: 20px;
            z-index: 9999;
            min-width: 300px;
            max-width: 400px;
        `;
        
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 5000);
    }

    // Utility method to check if element is in viewport
    isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }

    // Handle demo interactions
    setupDemoInteractions() {
        const demoButton = document.querySelector('a[href="/quick-referral"]');
        if (demoButton) {
            demoButton.addEventListener('click', (e) => {
                e.preventDefault();
                this.showQuickReferralDemo();
            });
        }
    }

    // Show quick referral demo modal
    showQuickReferralDemo() {
        const modal = document.createElement('div');
        modal.className = 'modal fade';
        modal.innerHTML = `
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">
                            <i class="fas fa-play-circle me-2"></i>Quick Referral Demo
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="text-center py-4">
                            <i class="fas fa-code fa-4x text-primary mb-3"></i>
                            <h4>Interactive Demo</h4>
                            <p class="text-muted mb-4">
                                Experience how dentists can quickly submit patient referrals using your unique code.
                            </p>
                            <a href="/quick-referral" class="btn btn-primary btn-lg">
                                <i class="fas fa-external-link-alt me-2"></i>Try Live Demo
                            </a>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
        
        // Clean up when modal is closed
        modal.addEventListener('hidden.bs.modal', () => {
            modal.remove();
        });
    }
}

// Form handling utilities
class FormHandler {
    static validateEmail(email) {
        const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return re.test(email);
    }

    static formatPhone(phone) {
        const cleaned = phone.replace(/\D/g, '');
        if (cleaned.length === 10) {
            return `(${cleaned.slice(0,3)}) ${cleaned.slice(3,6)}-${cleaned.slice(6)}`;
        }
        return phone;
    }

    static showFormError(input, message) {
        input.classList.add('is-invalid');
        
        let feedback = input.parentNode.querySelector('.invalid-feedback');
        if (!feedback) {
            feedback = document.createElement('div');
            feedback.className = 'invalid-feedback';
            input.parentNode.appendChild(feedback);
        }
        feedback.textContent = message;
    }

    static clearFormError(input) {
        input.classList.remove('is-invalid');
        const feedback = input.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.remove();
        }
    }
}

// Loading states utility
class LoadingStates {
    static showButtonLoading(button, loadingText = 'Loading...') {
        if (button.dataset.originalText) return; // Already loading
        
        button.dataset.originalText = button.innerHTML;
        button.disabled = true;
        button.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status"></span>
            ${loadingText}
        `;
    }

    static hideButtonLoading(button) {
        if (!button.dataset.originalText) return;
        
        button.disabled = false;
        button.innerHTML = button.dataset.originalText;
        delete button.dataset.originalText;
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const sapyynLanding = new SapyynLanding();
    
    // Setup demo interactions
    sapyynLanding.setupDemoInteractions();
    
    // Add any other initialization here
    console.log('Sapyyn landing page initialized');
});

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { SapyynLanding, FormHandler, LoadingStates };
}