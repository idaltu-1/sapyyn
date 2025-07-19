/**
 * Sapyyn Analytics & UX Tracking
 * Comprehensive tracking for SEO, UX, and conversion optimization
 */

// Configuration - will be overridden by server-side config
const ANALYTICS_CONFIG = window.ANALYTICS_CONFIG || {
    ga4MeasurementId: 'G-XXXXXXXXXX',
    hotjarSiteId: '3842847',
    gtmContainerId: 'GTM-XXXXXXX',
    environment: 'development',
    userId: null,
    userRole: null,
    enableDebug: true
};

// Additional configuration
ANALYTICS_CONFIG.scrollDepthThresholds = [25, 50, 75, 90, 100];
ANALYTICS_CONFIG.timeOnPageThresholds = [10, 30, 60, 120, 300]; // seconds

// Global analytics object
window.SapyynAnalytics = {
    initialized: false,
    startTime: Date.now(),
    maxScrollDepth: 0,
    pageViewId: generateUUID(),
    userInteractions: [],
    
    // Initialize all tracking
    init() {
        if (this.initialized) return;
        
        this.setupScrollDepthTracking();
        this.setupCTATracking();
        this.setupFormTracking();
        this.setupTimeOnPageTracking();
        this.setupNavigationTracking();
        this.setupPerformanceTracking();
        this.setupErrorTracking();
        this.setupUserEngagementTracking();
        
        this.initialized = true;
        this.debug('Analytics initialized');
        
        // Track page view with enhanced data
        this.trackPageView();
    },
    
    // Enhanced page view tracking
    trackPageView() {
        const pageData = {
            page_title: document.title,
            page_location: window.location.href,
            page_path: window.location.pathname,
            referrer: document.referrer,
            user_agent: navigator.userAgent,
            screen_resolution: `${screen.width}x${screen.height}`,
            viewport_size: `${window.innerWidth}x${window.innerHeight}`,
            timestamp: new Date().toISOString(),
            page_view_id: this.pageViewId
        };
        
        // Send to GA4
        if (typeof gtag !== 'undefined') {
            gtag('event', 'page_view', pageData);
        }
        
        // Send to GTM
        if (typeof dataLayer !== 'undefined') {
            dataLayer.push({
                event: 'enhanced_page_view',
                ...pageData
            });
        }
        
        this.debug('Page view tracked', pageData);
    },
    
    // Scroll depth tracking
    setupScrollDepthTracking() {
        let ticking = false;
        const trackedDepths = new Set();
        
        const trackScrollDepth = () => {
            const scrollTop = window.pageYOffset;
            const docHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollPercent = Math.round((scrollTop / docHeight) * 100);
            
            // Update max scroll depth
            if (scrollPercent > this.maxScrollDepth) {
                this.maxScrollDepth = scrollPercent;
            }
            
            // Track milestone thresholds
            ANALYTICS_CONFIG.scrollDepthThresholds.forEach(threshold => {
                if (scrollPercent >= threshold && !trackedDepths.has(threshold)) {
                    trackedDepths.add(threshold);
                    this.trackEvent('scroll_depth', {
                        scroll_depth: threshold,
                        page_height: docHeight,
                        max_scroll_depth: this.maxScrollDepth
                    });
                }
            });
            
            ticking = false;
        };
        
        const onScroll = () => {
            if (!ticking) {
                requestAnimationFrame(trackScrollDepth);
                ticking = true;
            }
        };
        
        window.addEventListener('scroll', onScroll, { passive: true });
        
        // Track scroll on page unload
        window.addEventListener('beforeunload', () => {
            this.trackEvent('final_scroll_depth', {
                final_scroll_depth: this.maxScrollDepth,
                time_on_page: Math.round((Date.now() - this.startTime) / 1000)
            });
        });
    },
    
    // CTA and conversion tracking
    setupCTATracking() {
        const ctaSelectors = [
            'a[href*="get_started"]',
            'a[href*="register"]', 
            'a[href*="login"]',
            'a[href*="dashboard"]',
            'a[href*="new_referral"]',
            '.btn-primary',
            '.btn-outline-primary',
            '.golden-button',
            'button[type="submit"]'
        ];
        
        ctaSelectors.forEach(selector => {
            document.addEventListener('click', (e) => {
                if (e.target.matches(selector) || e.target.closest(selector)) {
                    const element = e.target.matches(selector) ? e.target : e.target.closest(selector);
                    const ctaData = {
                        cta_text: element.textContent.trim(),
                        cta_href: element.href || 'N/A',
                        cta_class: element.className,
                        cta_id: element.id || 'N/A',
                        cta_position: this.getElementPosition(element),
                        page_section: this.getPageSection(element)
                    };
                    
                    this.trackEvent('cta_click', ctaData);
                    
                    // Track as conversion for key CTAs
                    if (this.isKeyConversion(element)) {
                        this.trackConversion('cta_conversion', ctaData);
                    }
                }
            });
        });
    },
    
    // Form interaction tracking
    setupFormTracking() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            const formId = form.id || form.className || 'unnamed_form';
            
            // Track form start
            form.addEventListener('focus', (e) => {
                if (e.target.type !== 'submit') {
                    this.trackEvent('form_start', {
                        form_id: formId,
                        field_name: e.target.name || e.target.id
                    });
                }
            }, { once: true });
            
            // Track form field interactions
            form.addEventListener('input', (e) => {
                this.trackEvent('form_interaction', {
                    form_id: formId,
                    field_name: e.target.name || e.target.id,
                    field_type: e.target.type
                });
            });
            
            // Track form submission
            form.addEventListener('submit', (e) => {
                const formData = new FormData(form);
                const fieldCount = [...formData.keys()].length;
                
                this.trackEvent('form_submit', {
                    form_id: formId,
                    field_count: fieldCount,
                    submission_time: Math.round((Date.now() - this.startTime) / 1000)
                });
                
                // Track as conversion
                this.trackConversion('form_submission', {
                    form_id: formId,
                    conversion_value: this.getFormValue(formId)
                });
            });
        });
    },
    
    // Time on page tracking
    setupTimeOnPageTracking() {
        const trackedTimes = new Set();
        
        const checkTimeThresholds = () => {
            const timeOnPage = Math.round((Date.now() - this.startTime) / 1000);
            
            ANALYTICS_CONFIG.timeOnPageThresholds.forEach(threshold => {
                if (timeOnPage >= threshold && !trackedTimes.has(threshold)) {
                    trackedTimes.add(threshold);
                    this.trackEvent('time_on_page', {
                        time_threshold: threshold,
                        total_time: timeOnPage,
                        engagement_level: this.calculateEngagementLevel(timeOnPage)
                    });
                }
            });
        };
        
        setInterval(checkTimeThresholds, 10000); // Check every 10 seconds
    },
    
    // Navigation tracking
    setupNavigationTracking() {
        document.addEventListener('click', (e) => {
            const link = e.target.closest('a');
            if (link && link.href) {
                const isExternal = !link.href.startsWith(window.location.origin);
                const isDownload = link.hasAttribute('download');
                
                this.trackEvent('navigation_click', {
                    link_text: link.textContent.trim(),
                    link_href: link.href,
                    is_external: isExternal,
                    is_download: isDownload,
                    link_position: this.getElementPosition(link)
                });
            }
        });
    },
    
    // Performance tracking
    setupPerformanceTracking() {
        window.addEventListener('load', () => {
            // Core Web Vitals and performance metrics
            if ('performance' in window) {
                const navigation = performance.getEntriesByType('navigation')[0];
                const paint = performance.getEntriesByType('paint');
                
                const performanceData = {
                    page_load_time: navigation.loadEventEnd - navigation.loadEventStart,
                    dom_content_loaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
                    first_paint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
                    first_contentful_paint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0,
                    navigation_type: navigation.type
                };
                
                this.trackEvent('performance_metrics', performanceData);
            }
            
            // Core Web Vitals with web-vitals library if available
            if (typeof getCLS !== 'undefined') {
                getCLS(this.trackWebVital.bind(this));
                getFID(this.trackWebVital.bind(this));
                getFCP(this.trackWebVital.bind(this));
                getLCP(this.trackWebVital.bind(this));
                getTTFB(this.trackWebVital.bind(this));
            }
        });
    },
    
    // Error tracking
    setupErrorTracking() {
        window.addEventListener('error', (e) => {
            this.trackEvent('javascript_error', {
                error_message: e.message,
                error_source: e.filename,
                error_line: e.lineno,
                error_column: e.colno,
                user_agent: navigator.userAgent
            });
        });
        
        window.addEventListener('unhandledrejection', (e) => {
            this.trackEvent('promise_rejection', {
                error_reason: e.reason?.toString() || 'Unknown',
                error_stack: e.reason?.stack || 'No stack trace'
            });
        });
    },
    
    // User engagement tracking
    setupUserEngagementTracking() {
        let isActive = true;
        let lastActivity = Date.now();
        
        // Track user activity
        ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
            document.addEventListener(event, () => {
                lastActivity = Date.now();
                if (!isActive) {
                    isActive = true;
                    this.trackEvent('user_reengaged', {
                        time_inactive: Math.round((Date.now() - lastActivity) / 1000)
                    });
                }
            }, { passive: true });
        });
        
        // Check for inactivity
        setInterval(() => {
            if (Date.now() - lastActivity > 30000 && isActive) { // 30 seconds
                isActive = false;
                this.trackEvent('user_inactive', {
                    time_before_inactive: Math.round((lastActivity - this.startTime) / 1000)
                });
            }
        }, 10000);
    },
    
    // Generic event tracking
    trackEvent(eventName, parameters = {}) {
        const eventData = {
            event_name: eventName,
            page_view_id: this.pageViewId,
            timestamp: new Date().toISOString(),
            ...parameters
        };
        
        // Send to GA4
        if (typeof gtag !== 'undefined') {
            gtag('event', eventName, eventData);
        }
        
        // Send to GTM
        if (typeof dataLayer !== 'undefined') {
            dataLayer.push({
                event: eventName,
                ...eventData
            });
        }
        
        // Send to Hotjar if available
        if (typeof hj !== 'undefined') {
            hj('event', eventName);
        }
        
        this.debug('Event tracked:', eventName, eventData);
        this.userInteractions.push(eventData);
    },
    
    // Conversion tracking
    trackConversion(conversionName, parameters = {}) {
        const conversionData = {
            conversion_name: conversionName,
            conversion_id: generateUUID(),
            ...parameters
        };
        
        // Send to GA4 as conversion
        if (typeof gtag !== 'undefined') {
            gtag('event', 'conversion', {
                send_to: ANALYTICS_CONFIG.ga4MeasurementId,
                ...conversionData
            });
        }
        
        this.trackEvent('conversion', conversionData);
        this.debug('Conversion tracked:', conversionName, conversionData);
    },
    
    // Web Vitals tracking
    trackWebVital(metric) {
        this.trackEvent('web_vital', {
            metric_name: metric.name,
            metric_value: metric.value,
            metric_id: metric.id,
            metric_delta: metric.delta
        });
    },
    
    // Utility functions
    getElementPosition(element) {
        const rect = element.getBoundingClientRect();
        return {
            x: Math.round(rect.left + window.scrollX),
            y: Math.round(rect.top + window.scrollY),
            viewport_x: Math.round(rect.left),
            viewport_y: Math.round(rect.top)
        };
    },
    
    getPageSection(element) {
        const sections = ['header', 'nav', 'main', 'footer', 'aside'];
        let current = element;
        
        while (current && current !== document.body) {
            const tagName = current.tagName?.toLowerCase();
            if (sections.includes(tagName)) {
                return tagName;
            }
            
            const className = current.className?.toLowerCase() || '';
            const foundSection = sections.find(section => className.includes(section));
            if (foundSection) {
                return foundSection;
            }
            
            current = current.parentElement;
        }
        
        return 'unknown';
    },
    
    isKeyConversion(element) {
        const conversionIndicators = [
            'get_started', 'register', 'signup', 'subscribe',
            'create_account', 'new_referral', 'upload'
        ];
        
        const href = element.href?.toLowerCase() || '';
        const text = element.textContent?.toLowerCase() || '';
        const className = element.className?.toLowerCase() || '';
        
        return conversionIndicators.some(indicator => 
            href.includes(indicator) || text.includes(indicator) || className.includes(indicator)
        );
    },
    
    getFormValue(formId) {
        // Assign values to different forms for conversion tracking
        const formValues = {
            'subscription': 50,
            'registration': 100,
            'referral': 200,
            'contact': 25
        };
        
        return Object.keys(formValues).find(key => 
            formId.toLowerCase().includes(key)
        ) ? formValues[Object.keys(formValues).find(key => 
            formId.toLowerCase().includes(key)
        )] : 0;
    },
    
    calculateEngagementLevel(timeOnPage) {
        if (timeOnPage < 10) return 'low';
        if (timeOnPage < 60) return 'medium';
        if (timeOnPage < 300) return 'high';
        return 'very_high';
    },
    
    debug(...args) {
        if (ANALYTICS_CONFIG.enableDebug) {
            console.log('[Sapyyn Analytics]', ...args);
        }
    }
};

// Utility function to generate UUID
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c == 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.SapyynAnalytics.init();
    });
} else {
    window.SapyynAnalytics.init();
}

// Export for manual usage
window.trackEvent = window.SapyynAnalytics.trackEvent.bind(window.SapyynAnalytics);
window.trackConversion = window.SapyynAnalytics.trackConversion.bind(window.SapyynAnalytics);