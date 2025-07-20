/**
 * Portal JavaScript
 */
document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const portalMenu = document.querySelector('.portal-menu');
    
    if (menuToggle && portalMenu) {
        menuToggle.addEventListener('click', function() {
            portalMenu.classList.toggle('active');
        });
    }
    
    // User profile dropdown
    const userProfile = document.querySelector('.user-profile');
    const dropdownMenu = userProfile?.querySelector('.dropdown-menu');
    
    if (userProfile && dropdownMenu) {
        // For touch devices
        userProfile.addEventListener('click', function(e) {
            if (window.innerWidth < 992) {
                e.preventDefault();
                dropdownMenu.classList.toggle('show');
            }
        });
        
        // Close dropdown when clicking outside
        document.addEventListener('click', function(e) {
            if (!userProfile.contains(e.target) && dropdownMenu.classList.contains('show')) {
                dropdownMenu.classList.remove('show');
            }
        });
    }
    
    // Notification button
    const notificationBtn = document.querySelector('.notification-btn');
    
    if (notificationBtn) {
        notificationBtn.addEventListener('click', function() {
            // In a real implementation, this would show a notifications panel
            console.log('Notification button clicked');
        });
    }
});