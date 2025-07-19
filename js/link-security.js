/**
 * Link Security and Mapping System for Sapyyn
 * Handles secure link navigation, validation, and vulnerability prevention
 */

class LinkSecurityManager {
    constructor() {
        this.allowedDomains = [
            window.location.hostname,
            'localhost',
            '127.0.0.1',
            'sapyyn.com',
            'www.sapyyn.com'
        ];
        
        this.trustedExternalDomains = [
            'github.com',
            'linkedin.com',
            'twitter.com',
            'facebook.com',
            'youtube.com',
            'vimeo.com',
            'docs.google.com',
            'drive.google.com'
        ];
        
        this.linkMap = new Map();
        this.init();
    }

    init() {
        this.buildLinkMap();
        this.setupLinkValidation();
        this.setupSecurityHeaders();
        this.preventClickjacking();
        this.setupCSRFProtection();
        this.sanitizeLinks();
    }

    // Build comprehensive link mapping
    buildLinkMap() {
        // Internal route mappings with security levels
        const routes = {
            // Public routes
            '/': { security: 'public', title: 'Home', description: 'Sapyyn Homepage' },
            '/login': { security: 'public', title: 'Login', description: 'User Login' },
            '/register': { security: 'public', title: 'Register', description: 'User Registration' },
            '/about': { security: 'public', title: 'About Us', description: 'About Sapyyn' },
            '/contact': { security: 'public', title: 'Contact', description: 'Contact Information' },
            '/pricing': { security: 'public', title: 'Pricing', description: 'Pricing Plans' },
            '/faq': { security: 'public', title: 'FAQ', description: 'Frequently Asked Questions' },
            '/privacy': { security: 'public', title: 'Privacy Policy', description: 'Privacy Policy' },
            '/terms': { security: 'public', title: 'Terms of Service', description: 'Terms of Service' },
            '/hipaa': { security: 'public', title: 'HIPAA Compliance', description: 'HIPAA Information' },
            
            // Authentication required
            '/dashboard': { security: 'authenticated', title: 'Dashboard', description: 'User Dashboard' },
            '/profile': { security: 'authenticated', title: 'Profile', description: 'User Profile' },
            '/settings': { security: 'authenticated', title: 'Settings', description: 'Account Settings' },
            '/new-referral': { security: 'authenticated', title: 'New Referral', description: 'Create New Referral' },
            '/my-referrals': { security: 'authenticated', title: 'My Referrals', description: 'View Referrals' },
            '/upload': { security: 'authenticated', title: 'Upload Documents', description: 'Document Upload' },
            '/documents': { security: 'authenticated', title: 'Documents', description: 'View Documents' },
            '/messages': { security: 'authenticated', title: 'Messages', description: 'Message Center' },
            '/rewards': { security: 'authenticated', title: 'Rewards', description: 'Rewards Dashboard' },
            
            // Role-based access
            '/admin': { security: 'admin', title: 'Admin Panel', description: 'Administration' },
            '/analytics': { security: 'admin', title: 'Analytics', description: 'Analytics Dashboard' },
            '/promotions': { security: 'provider', title: 'Promotions', description: 'Manage Promotions' },
            
            // Portal routes
            '/portal/dashboard': { security: 'authenticated', title: 'Portal Dashboard', description: 'Portal Dashboard' },
            '/portal/appointments': { security: 'authenticated', title: 'Appointments', description: 'Appointment Management' },
            '/portal/referrals': { security: 'authenticated', title: 'Portal Referrals', description: 'Referral Management' }
        };

        // Build the link map
        Object.entries(routes).forEach(([path, config]) => {
            this.linkMap.set(path, config);
        });
    }

    // Validate and secure all links
    setupLinkValidation() {
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a[href]');
            if (!link) return;

            const href = link.getAttribute('href');
            
            // Skip if it's a hash link or javascript: protocol
            if (href.startsWith('#') || href.startsWith('javascript:')) {
                if (href.startsWith('javascript:')) {
                    e.preventDefault();
                    console.warn('JavaScript protocol links are blocked for security');
                }
                return;
            }

            // Validate and secure the link
            if (!this.validateLink(href, link)) {
                e.preventDefault();
                return;
            }

            // Add security attributes to external links
            this.secureExternalLink(link);
        });
    }

    // Validate link security
    validateLink(href, linkElement) {
        try {
            const url = new URL(href, window.location.origin);
            
            // Check for malicious protocols
            if (!['http:', 'https:', 'mailto:', 'tel:'].includes(url.protocol)) {
                console.warn('Blocked potentially malicious protocol:', url.protocol);
                return false;
            }

            // Validate internal links
            if (this.isInternalLink(url)) {
                return this.validateInternalLink(url.pathname, linkElement);
            }

            // Validate external links
            return this.validateExternalLink(url, linkElement);
            
        } catch (error) {
            console.warn('Invalid URL:', href, error);
            return false;
        }
    }

    // Check if link is internal
    isInternalLink(url) {
        return this.allowedDomains.includes(url.hostname);
    }

    // Validate internal links
    validateInternalLink(pathname, linkElement) {
        const routeConfig = this.linkMap.get(pathname);
        
        if (!routeConfig) {
            // Allow dynamic routes (with parameters)
            const dynamicRoutes = [
                '/referral/',
                '/user/',
                '/document/',
                '/promotion/',
                '/track/'
            ];
            
            const isDynamicRoute = dynamicRoutes.some(route => pathname.startsWith(route));
            if (!isDynamicRoute) {
                console.warn('Unknown internal route:', pathname);
            }
            return true;
        }

        // Check security requirements
        return this.checkRouteAccess(routeConfig, linkElement);
    }

    // Check route access permissions
    checkRouteAccess(routeConfig, linkElement) {
        const userRole = this.getCurrentUserRole();
        const isAuthenticated = this.isUserAuthenticated();

        switch (routeConfig.security) {
            case 'public':
                return true;
                
            case 'authenticated':
                if (!isAuthenticated) {
                    this.redirectToLogin(linkElement.href);
                    return false;
                }
                return true;
                
            case 'admin':
                if (!isAuthenticated || !['admin', 'dentist_admin', 'specialist_admin'].includes(userRole)) {
                    this.showAccessDenied();
                    return false;
                }
                return true;
                
            case 'provider':
                if (!isAuthenticated || !['dentist', 'specialist', 'dentist_admin', 'specialist_admin', 'admin'].includes(userRole)) {
                    this.showAccessDenied();
                    return false;
                }
                return true;
                
            default:
                return true;
        }
    }

    // Validate external links
    validateExternalLink(url, linkElement) {
        const hostname = url.hostname;
        
        // Check if domain is in trusted list
        const isTrusted = this.trustedExternalDomains.some(domain => 
            hostname === domain || hostname.endsWith('.' + domain)
        );

        if (!isTrusted) {
            // Show warning for untrusted external links
            return this.confirmExternalNavigation(url.href, linkElement);
        }

        return true;
    }

    // Secure external links
    secureExternalLink(linkElement) {
        const href = linkElement.getAttribute('href');
        
        try {
            const url = new URL(href, window.location.origin);
            
            if (!this.isInternalLink(url)) {
                // Add security attributes
                linkElement.setAttribute('rel', 'noopener noreferrer');
                linkElement.setAttribute('target', '_blank');
                
                // Add security warning icon if not already present
                if (!linkElement.querySelector('.external-link-icon')) {
                    const icon = document.createElement('i');
                    icon.className = 'bi bi-box-arrow-up-right external-link-icon ms-1';
                    icon.style.fontSize = '0.8em';
                    linkElement.appendChild(icon);
                }
            }
        } catch (error) {
            console.warn('Error securing external link:', error);
        }
    }

    // Confirm external navigation
    confirmExternalNavigation(href, linkElement) {
        const confirmed = confirm(
            `You are about to leave Sapyyn and visit an external website:\n\n${href}\n\nDo you want to continue?`
        );
        
        if (confirmed) {
            // Open in new tab with security attributes
            const newWindow = window.open(href, '_blank', 'noopener,noreferrer');
            if (!newWindow) {
                alert('Pop-up blocked. Please allow pop-ups for this site or copy the link manually.');
            }
        }
        
        return false; // Always prevent default to handle manually
    }

    // Get current user role from session/DOM
    getCurrentUserRole() {
        // Try to get from meta tag first
        const roleMeta = document.querySelector('meta[name="user-role"]');
        if (roleMeta) {
            return roleMeta.getAttribute('content');
        }
        
        // Try to get from global variable
        if (window.USER_ROLE) {
            return window.USER_ROLE;
        }
        
        // Try to get from body class
        const bodyClasses = document.body.className;
        const roleMatch = bodyClasses.match(/role-(\w+)/);
        if (roleMatch) {
            return roleMatch[1];
        }
        
        return null;
    }

    // Check if user is authenticated
    isUserAuthenticated() {
        // Check for authentication indicators
        const authMeta = document.querySelector('meta[name="authenticated"]');
        if (authMeta) {
            return authMeta.getAttribute('content') === 'true';
        }
        
        // Check for user ID in global scope
        if (window.USER_ID) {
            return true;
        }
        
        // Check for authentication class on body
        return document.body.classList.contains('authenticated');
    }

    // Redirect to login with return URL
    redirectToLogin(returnUrl) {
        const loginUrl = new URL('/login', window.location.origin);
        if (returnUrl && returnUrl !== window.location.href) {
            loginUrl.searchParams.set('next', returnUrl);
        }
        window.location.href = loginUrl.toString();
    }

    // Show access denied message
    showAccessDenied() {
        if (window.SapyynUI && window.SapyynUI.showAlert) {
            window.SapyynUI.showAlert(
                'Access denied. You do not have permission to access this page.',
                'danger',
                5000
            );
        } else {
            alert('Access denied. You do not have permission to access this page.');
        }
    }

    // Setup security headers
    setupSecurityHeaders() {
        // Add CSP meta tag if not present
        if (!document.querySelector('meta[http-equiv="Content-Security-Policy"]')) {
            const cspMeta = document.createElement('meta');
            cspMeta.setAttribute('http-equiv', 'Content-Security-Policy');
            cspMeta.setAttribute('content', this.getCSPPolicy());
            document.head.appendChild(cspMeta);
        }

        // Add X-Frame-Options protection
        if (!document.querySelector('meta[name="x-frame-options"]')) {
            const frameMeta = document.createElement('meta');
            frameMeta.setAttribute('name', 'x-frame-options');
            frameMeta.setAttribute('content', 'DENY');
            document.head.appendChild(frameMeta);
        }
    }

    // Get Content Security Policy
    getCSPPolicy() {
        return [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://www.googletagmanager.com https://www.google-analytics.com https://static.hotjar.com https://script.hotjar.com https://cdn.jsdelivr.net https://unpkg.com",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com https://cdn.jsdelivr.net",
            "img-src 'self' data: https: blob:",
            "connect-src 'self' https://www.google-analytics.com https://region1.google-analytics.com https://*.hotjar.com https://*.hotjar.io",
            "frame-src 'self' https://www.youtube.com https://www.vimeo.com",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'"
        ].join('; ');
    }

    // Prevent clickjacking
    preventClickjacking() {
        // Check if we're in an iframe
        if (window.self !== window.top) {
            // We're in an iframe, check if it's allowed
            const allowedFrameOrigins = [
                window.location.origin,
                'https://sapyyn.com',
                'https://www.sapyyn.com'
            ];
            
            try {
                const parentOrigin = window.parent.location.origin;
                if (!allowedFrameOrigins.includes(parentOrigin)) {
                    // Break out of unauthorized iframe
                    window.top.location = window.location;
                }
            } catch (e) {
                // Cross-origin iframe detected, break out
                window.top.location = window.location;
            }
        }
    }

    // Setup CSRF protection
    setupCSRFProtection() {
        // Get CSRF token from meta tag
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        
        if (csrfToken) {
            // Add CSRF token to all forms
            document.querySelectorAll('form').forEach(form => {
                if (!form.querySelector('input[name="csrf_token"]')) {
                    const csrfInput = document.createElement('input');
                    csrfInput.type = 'hidden';
                    csrfInput.name = 'csrf_token';
                    csrfInput.value = csrfToken;
                    form.appendChild(csrfInput);
                }
            });

            // Add CSRF token to AJAX requests
            const originalFetch = window.fetch;
            window.fetch = function(url, options = {}) {
                if (options.method && ['POST', 'PUT', 'PATCH', 'DELETE'].includes(options.method.toUpperCase())) {
                    options.headers = options.headers || {};
                    options.headers['X-CSRFToken'] = csrfToken;
                }
                return originalFetch(url, options);
            };
        }
    }

    // Sanitize all links on page
    sanitizeLinks() {
        document.querySelectorAll('a[href]').forEach(link => {
            const href = link.getAttribute('href');
            
            // Remove dangerous protocols
            if (href.match(/^(javascript|data|vbscript):/i)) {
                link.removeAttribute('href');
                link.style.cursor = 'not-allowed';
                link.title = 'This link has been disabled for security reasons';
                console.warn('Removed dangerous link:', href);
            }
            
            // Sanitize href attribute
            const sanitizedHref = this.sanitizeUrl(href);
            if (sanitizedHref !== href) {
                link.setAttribute('href', sanitizedHref);
            }
        });
    }

    // Sanitize URL
    sanitizeUrl(url) {
        if (!url) return '';
        
        // Remove null bytes and control characters
        let sanitized = url.replace(/[\x00-\x1F\x7F]/g, '');
        
        // Remove potentially dangerous characters
        sanitized = sanitized.replace(/[<>"']/g, '');
        
        // Ensure proper encoding
        try {
            const urlObj = new URL(sanitized, window.location.origin);
            return urlObj.toString();
        } catch (e) {
            // If URL is invalid, return empty string
            return '';
        }
    }

    // Input validation and sanitization
    setupInputSanitization() {
        document.addEventListener('input', (e) => {
            if (e.target.matches('input[type="text"], input[type="email"], textarea')) {
                this.sanitizeInput(e.target);
            }
        });
    }

    // Sanitize input values
    sanitizeInput(input) {
        let value = input.value;
        
        // Remove script tags and dangerous content
        value = value.replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '');
        value = value.replace(/javascript:/gi, '');
        value = value.replace(/on\w+\s*=/gi, '');
        
        // Update input if changed
        if (value !== input.value) {
            input.value = value;
            console.warn('Sanitized potentially dangerous input');
        }
    }

    // Rate limiting for form submissions
    setupRateLimiting() {
        const submissionTimes = new Map();
        
        document.addEventListener('submit', (e) => {
            const form = e.target;
            const formId = form.id || form.action || 'anonymous';
            const now = Date.now();
            const lastSubmission = submissionTimes.get(formId);
            
            // Prevent rapid form submissions (1 second cooldown)
            if (lastSubmission && (now - lastSubmission) < 1000) {
                e.preventDefault();
                this.showRateLimitWarning();
                return;
            }
            
            submissionTimes.set(formId, now);
        });
    }

    // Show rate limit warning
    showRateLimitWarning() {
        if (window.SapyynUI && window.SapyynUI.showAlert) {
            window.SapyynUI.showAlert(
                'Please wait before submitting again.',
                'warning',
                3000
            );
        }
    }

    // Monitor for suspicious activity
    setupSecurityMonitoring() {
        let suspiciousActivity = 0;
        
        // Monitor for rapid clicking
        let clickCount = 0;
        let clickTimer = null;
        
        document.addEventListener('click', () => {
            clickCount++;
            
            if (clickTimer) {
                clearTimeout(clickTimer);
            }
            
            clickTimer = setTimeout(() => {
                if (clickCount > 20) {
                    suspiciousActivity++;
                    console.warn('Suspicious clicking activity detected');
                }
                clickCount = 0;
            }, 1000);
        });
        
        // Monitor for console access (basic detection)
        let devtools = false;
        setInterval(() => {
            if (window.outerHeight - window.innerHeight > 200 || window.outerWidth - window.innerWidth > 200) {
                if (!devtools) {
                    devtools = true;
                    console.warn('Developer tools detected');
                }
            } else {
                devtools = false;
            }
        }, 1000);
    }

    // Public method to validate a URL
    static validateUrl(url) {
        try {
            new URL(url);
            return true;
        } catch {
            return false;
        }
    }

    // Public method to get route info
    getRouteInfo(path) {
        return this.linkMap.get(path) || null;
    }

    // Cleanup method
    destroy() {
        // Remove event listeners and cleanup
        this.linkMap.clear();
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.SapyynLinkSecurity = new LinkSecurityManager();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = LinkSecurityManager;
}
