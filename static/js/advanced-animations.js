/**
 * Advanced Animation System for Sapyyn
 * Enhanced animations, transitions, and interactive effects
 */

class AdvancedAnimations {
    constructor() {
        this.observers = new Map();
        this.animationQueue = [];
        this.isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.init();
    }

    init() {
        this.setupIntersectionObserver();
        this.setupScrollAnimations();
        this.setupHoverEffects();
        this.setupPageTransitions();
        this.setupLoadingAnimations();
        this.setupMicroInteractions();
        this.setupParallaxEffects();
    }

    // Intersection Observer for scroll-triggered animations
    setupIntersectionObserver() {
        if (this.isReducedMotion) return;

        const observerOptions = {
            threshold: [0.1, 0.3, 0.5, 0.7, 0.9],
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    this.triggerAnimation(entry.target);
                }
            });
        }, observerOptions);

        // Observe elements with animation classes
        document.querySelectorAll('[data-animate]').forEach(el => {
            observer.observe(el);
        });

        this.observers.set('intersection', observer);
    }

    // Trigger animations based on data attributes
    triggerAnimation(element) {
        const animationType = element.dataset.animate;
        const delay = parseInt(element.dataset.delay) || 0;
        const duration = parseInt(element.dataset.duration) || 600;

        setTimeout(() => {
            switch (animationType) {
                case 'fadeInUp':
                    this.fadeInUp(element, duration);
                    break;
                case 'fadeInLeft':
                    this.fadeInLeft(element, duration);
                    break;
                case 'fadeInRight':
                    this.fadeInRight(element, duration);
                    break;
                case 'scaleIn':
                    this.scaleIn(element, duration);
                    break;
                case 'slideInUp':
                    this.slideInUp(element, duration);
                    break;
                case 'rotateIn':
                    this.rotateIn(element, duration);
                    break;
                case 'bounceIn':
                    this.bounceIn(element, duration);
                    break;
                case 'typewriter':
                    this.typewriter(element, duration);
                    break;
                default:
                    this.fadeIn(element, duration);
            }
        }, delay);
    }

    // Animation methods
    fadeInUp(element, duration = 600) {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        element.style.transition = `all ${duration}ms cubic-bezier(0.4, 0, 0.2, 1)`;
        
        requestAnimationFrame(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateY(0)';
        });
    }

    fadeInLeft(element, duration = 600) {
        element.style.opacity = '0';
        element.style.transform = 'translateX(-30px)';
        element.style.transition = `all ${duration}ms cubic-bezier(0.4, 0, 0.2, 1)`;
        
        requestAnimationFrame(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateX(0)';
        });
    }

    fadeInRight(element, duration = 600) {
        element.style.opacity = '0';
        element.style.transform = 'translateX(30px)';
        element.style.transition = `all ${duration}ms cubic-bezier(0.4, 0, 0.2, 1)`;
        
        requestAnimationFrame(() => {
            element.style.opacity = '1';
            element.style.transform = 'translateX(0)';
        });
    }

    scaleIn(element, duration = 600) {
        element.style.opacity = '0';
        element.style.transform = 'scale(0.8)';
        element.style.transition = `all ${duration}ms cubic-bezier(0.34, 1.56, 0.64, 1)`;
        
        requestAnimationFrame(() => {
            element.style.opacity = '1';
            element.style.transform = 'scale(1)';
        });
    }

    slideInUp(element, duration = 600) {
        element.style.transform = 'translateY(100%)';
        element.style.transition = `transform ${duration}ms cubic-bezier(0.4, 0, 0.2, 1)`;
        
        requestAnimationFrame(() => {
            element.style.transform = 'translateY(0)';
        });
    }

    rotateIn(element, duration = 600) {
        element.style.opacity = '0';
        element.style.transform = 'rotate(-180deg) scale(0.8)';
        element.style.transition = `all ${duration}ms cubic-bezier(0.4, 0, 0.2, 1)`;
        
        requestAnimationFrame(() => {
            element.style.opacity = '1';
            element.style.transform = 'rotate(0deg) scale(1)';
        });
    }

    bounceIn(element, duration = 600) {
        element.style.opacity = '0';
        element.style.transform = 'scale(0.3)';
        element.style.transition = `all ${duration}ms cubic-bezier(0.68, -0.55, 0.265, 1.55)`;
        
        requestAnimationFrame(() => {
            element.style.opacity = '1';
            element.style.transform = 'scale(1)';
        });
    }

    fadeIn(element, duration = 600) {
        element.style.opacity = '0';
        element.style.transition = `opacity ${duration}ms ease-out`;
        
        requestAnimationFrame(() => {
            element.style.opacity = '1';
        });
    }

    typewriter(element, duration = 2000) {
        const text = element.textContent;
        element.textContent = '';
        element.style.borderRight = '2px solid #667eea';
        
        let i = 0;
        const speed = duration / text.length;
        
        const typeInterval = setInterval(() => {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
            } else {
                clearInterval(typeInterval);
                setTimeout(() => {
                    element.style.borderRight = 'none';
                }, 500);
            }
        }, speed);
    }

    // Scroll-based animations
    setupScrollAnimations() {
        if (this.isReducedMotion) return;

        let ticking = false;

        const updateScrollAnimations = () => {
            const scrollY = window.scrollY;
            const windowHeight = window.innerHeight;

            // Parallax backgrounds
            document.querySelectorAll('[data-parallax]').forEach(el => {
                const speed = parseFloat(el.dataset.parallax) || 0.5;
                const yPos = -(scrollY * speed);
                el.style.transform = `translateY(${yPos}px)`;
            });

            // Fade elements based on scroll
            document.querySelectorAll('[data-scroll-fade]').forEach(el => {
                const rect = el.getBoundingClientRect();
                const elementTop = rect.top;
                const elementHeight = rect.height;
                
                if (elementTop < windowHeight && elementTop + elementHeight > 0) {
                    const opacity = Math.max(0, Math.min(1, 
                        (windowHeight - elementTop) / (windowHeight * 0.5)
                    ));
                    el.style.opacity = opacity;
                }
            });

            ticking = false;
        };

        const requestScrollUpdate = () => {
            if (!ticking) {
                requestAnimationFrame(updateScrollAnimations);
                ticking = true;
            }
        };

        window.addEventListener('scroll', requestScrollUpdate, { passive: true });
    }

    // Enhanced hover effects
    setupHoverEffects() {
        // Magnetic effect for buttons
        document.querySelectorAll('.btn-magnetic').forEach(btn => {
            btn.addEventListener('mousemove', (e) => {
                const rect = btn.getBoundingClientRect();
                const x = e.clientX - rect.left - rect.width / 2;
                const y = e.clientY - rect.top - rect.height / 2;
                
                btn.style.transform = `translate(${x * 0.1}px, ${y * 0.1}px)`;
            });

            btn.addEventListener('mouseleave', () => {
                btn.style.transform = 'translate(0, 0)';
            });
        });

        // Ripple effect for buttons
        document.querySelectorAll('.btn-ripple').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const rect = btn.getBoundingClientRect();
                const size = Math.max(rect.width, rect.height);
                const x = e.clientX - rect.left - size / 2;
                const y = e.clientY - rect.top - size / 2;
                
                const ripple = document.createElement('span');
                ripple.style.cssText = `
                    position: absolute;
                    width: ${size}px;
                    height: ${size}px;
                    left: ${x}px;
                    top: ${y}px;
                    background: rgba(255, 255, 255, 0.5);
                    border-radius: 50%;
                    transform: scale(0);
                    animation: ripple 0.6s linear;
                    pointer-events: none;
                `;
                
                btn.style.position = 'relative';
                btn.style.overflow = 'hidden';
                btn.appendChild(ripple);
                
                setTimeout(() => ripple.remove(), 600);
            });
        });

        // Tilt effect for cards
        document.querySelectorAll('.card-tilt').forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const rect = card.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;
                
                const centerX = rect.width / 2;
                const centerY = rect.height / 2;
                
                const rotateX = (y - centerY) / centerY * -10;
                const rotateY = (x - centerX) / centerX * 10;
                
                card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(1.05, 1.05, 1.05)`;
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = 'perspective(1000px) rotateX(0deg) rotateY(0deg) scale3d(1, 1, 1)';
            });
        });
    }

    // Page transition animations
    setupPageTransitions() {
        // Smooth page transitions
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href]');
            if (link && link.hostname === window.location.hostname && !link.hasAttribute('target')) {
                e.preventDefault();
                
                const href = link.getAttribute('href');
                this.transitionToPage(href);
            }
        });
    }

    transitionToPage(href) {
        if (this.isReducedMotion) {
            window.location.href = href;
            return;
        }

        // Create overlay
        const overlay = document.createElement('div');
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            z-index: 9999;
            opacity: 0;
            transition: opacity 0.3s ease;
        `;
        
        document.body.appendChild(overlay);
        
        requestAnimationFrame(() => {
            overlay.style.opacity = '1';
        });
        
        setTimeout(() => {
            window.location.href = href;
        }, 300);
    }

    // Loading animations
    setupLoadingAnimations() {
        // Skeleton loading for images
        document.querySelectorAll('img[data-skeleton]').forEach(img => {
            const skeleton = document.createElement('div');
            skeleton.className = 'skeleton-loader';
            skeleton.style.cssText = `
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
                background-size: 200% 100%;
                animation: skeleton-loading 1.5s infinite;
            `;
            
            img.parentNode.style.position = 'relative';
            img.parentNode.appendChild(skeleton);
            
            img.addEventListener('load', () => {
                skeleton.style.opacity = '0';
                setTimeout(() => skeleton.remove(), 300);
            });
        });

        // Progressive content loading
        this.setupProgressiveLoading();
    }

    setupProgressiveLoading() {
        const loadContent = (entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    const src = element.dataset.src;
                    
                    if (src) {
                        element.src = src;
                        element.removeAttribute('data-src');
                    }
                    
                    this.observers.get('lazy').unobserve(element);
                }
            });
        };

        const lazyObserver = new IntersectionObserver(loadContent, {
            rootMargin: '50px'
        });

        document.querySelectorAll('[data-src]').forEach(el => {
            lazyObserver.observe(el);
        });

        this.observers.set('lazy', lazyObserver);
    }

    // Micro-interactions
    setupMicroInteractions() {
        // Button press animation
        document.querySelectorAll('.btn').forEach(btn => {
            btn.addEventListener('mousedown', () => {
                btn.style.transform = 'scale(0.98)';
            });

            btn.addEventListener('mouseup', () => {
                btn.style.transform = '';
            });

            btn.addEventListener('mouseleave', () => {
                btn.style.transform = '';
            });
        });

        // Form field focus animations
        document.querySelectorAll('.form-control').forEach(field => {
            field.addEventListener('focus', () => {
                const parent = field.closest('.form-floating, .form-group');
                if (parent) {
                    parent.classList.add('focused');
                }
            });

            field.addEventListener('blur', () => {
                const parent = field.closest('.form-floating, .form-group');
                if (parent) {
                    parent.classList.remove('focused');
                }
            });
        });

        // Success/error state animations
        this.setupFormStateAnimations();
    }

    setupFormStateAnimations() {
        // Animate form validation states
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    const element = mutation.target;
                    
                    if (element.classList.contains('is-valid')) {
                        this.animateSuccess(element);
                    } else if (element.classList.contains('is-invalid')) {
                        this.animateError(element);
                    }
                }
            });
        });

        document.querySelectorAll('.form-control').forEach(el => {
            observer.observe(el, { attributes: true });
        });
    }

    animateSuccess(element) {
        element.style.animation = 'successPulse 0.6s ease-out';
        setTimeout(() => {
            element.style.animation = '';
        }, 600);
    }

    animateError(element) {
        element.style.animation = 'errorShake 0.6s ease-out';
        setTimeout(() => {
            element.style.animation = '';
        }, 600);
    }

    // Parallax effects
    setupParallaxEffects() {
        if (this.isReducedMotion) return;

        // Mouse parallax for hero sections
        document.querySelectorAll('.parallax-mouse').forEach(section => {
            section.addEventListener('mousemove', (e) => {
                const rect = section.getBoundingClientRect();
                const x = (e.clientX - rect.left) / rect.width;
                const y = (e.clientY - rect.top) / rect.height;
                
                const layers = section.querySelectorAll('.parallax-layer');
                layers.forEach((layer, index) => {
                    const speed = (index + 1) * 0.5;
                    const xMove = (x - 0.5) * speed * 20;
                    const yMove = (y - 0.5) * speed * 20;
                    
                    layer.style.transform = `translate(${xMove}px, ${yMove}px)`;
                });
            });

            section.addEventListener('mouseleave', () => {
                const layers = section.querySelectorAll('.parallax-layer');
                layers.forEach(layer => {
                    layer.style.transform = 'translate(0, 0)';
                });
            });
        });
    }

    // Public methods for manual animation triggering
    animateElement(element, animation, options = {}) {
        const duration = options.duration || 600;
        const delay = options.delay || 0;
        
        setTimeout(() => {
            this[animation](element, duration);
        }, delay);
    }

    // Cleanup method
    destroy() {
        this.observers.forEach(observer => observer.disconnect());
        this.observers.clear();
    }
}

// CSS animations to be injected
const animationCSS = `
@keyframes ripple {
    to {
        transform: scale(4);
        opacity: 0;
    }
}

@keyframes skeleton-loading {
    0% {
        background-position: -200% 0;
    }
    100% {
        background-position: 200% 0;
    }
}

@keyframes successPulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); box-shadow: 0 0 20px rgba(40, 167, 69, 0.4); }
    100% { transform: scale(1); }
}

@keyframes errorShake {
    0%, 100% { transform: translateX(0); }
    10%, 30%, 50%, 70%, 90% { transform: translateX(-5px); }
    20%, 40%, 60%, 80% { transform: translateX(5px); }
}

.focused {
    transform: translateY(-2px);
    transition: transform 0.3s ease;
}

.btn-magnetic {
    transition: transform 0.1s ease;
}

.btn-ripple {
    overflow: hidden;
    position: relative;
}

.card-tilt {
    transition: transform 0.1s ease;
}

.parallax-layer {
    transition: transform 0.1s ease;
}
`;

// Inject CSS
const style = document.createElement('style');
style.textContent = animationCSS;
document.head.appendChild(style);

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.SapyynAnimations = new AdvancedAnimations();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AdvancedAnimations;
}
