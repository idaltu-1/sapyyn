/**
 * Navigation Testing Script
 * This script verifies that all navigation links are working correctly
 */

document.addEventListener('DOMContentLoaded', function() {
    console.log('Navigation test script loaded');
    
    // Test function to verify all links
    function testNavLinks() {
        const links = document.querySelectorAll('nav a');
        const results = {
            total: links.length,
            valid: 0,
            invalid: [],
            authenticated: 0,
            public: 0
        };
        
        links.forEach(link => {
            const href = link.getAttribute('href');
            const text = link.textContent.trim();
            
            // Skip empty or javascript links
            if (!href || href === '#' || href.startsWith('javascript:')) {
                return;
            }
            
            // Check if link is valid
            if (href.startsWith('/') || href.startsWith('http')) {
                results.valid++;
                
                // Check if link is authenticated
                if (href.includes('dashboard') || 
                    href.includes('profile') || 
                    href.includes('referral') || 
                    href.includes('document') || 
                    href.includes('message') || 
                    href.includes('setting') || 
                    href.includes('admin')) {
                    results.authenticated++;
                } else {
                    results.public++;
                }
            } else {
                results.invalid.push({ text, href });
            }
        });
        
        console.log('Navigation Test Results:', results);
        
        // Check for mobile responsiveness
        const navbarToggler = document.querySelector('.navbar-toggler');
        const navbarCollapse = document.querySelector('.navbar-collapse');
        
        if (navbarToggler && navbarCollapse) {
            console.log('Mobile navigation: OK');
        } else {
            console.warn('Mobile navigation: Missing toggler or collapse element');
        }
        
        // Check for dropdown menus
        const dropdowns = document.querySelectorAll('.dropdown-menu');
        console.log(`Found ${dropdowns.length} dropdown menus`);
        
        return results;
    }
    
    // Run test after a short delay to ensure all elements are loaded
    setTimeout(testNavLinks, 1000);
    
    // Add test button to footer for manual testing
    const footer = document.querySelector('footer');
    if (footer) {
        const testButton = document.createElement('button');
        testButton.textContent = 'Test Navigation';
        testButton.className = 'btn btn-sm btn-outline-secondary mt-2';
        testButton.style.display = 'none'; // Hidden by default
        testButton.addEventListener('click', testNavLinks);
        
        // Only show in development mode
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            testButton.style.display = 'inline-block';
        }
        
        footer.appendChild(testButton);
    }
});