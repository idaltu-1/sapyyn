/**
 * PWA Install Prompt Handler
 * Manages the install prompt and user interactions
 */

(function() {
    'use strict';

    let deferredPrompt;
    const installPrompt = document.getElementById('install-prompt');
    const installBtn = document.getElementById('install-btn');
    const installDismiss = document.getElementById('install-dismiss');

    // Check if PWA is already installed
    function isPWAInstalled() {
        return window.matchMedia('(display-mode: standalone)').matches || 
               window.navigator.standalone || 
               document.referrer.includes('android-app://');
    }

    // Show install prompt
    function showInstallPrompt() {
        if (installPrompt) {
            installPrompt.style.display = 'block';
            installPrompt.setAttribute('aria-hidden', 'false');
        }
    }

    // Hide install prompt
    function hideInstallPrompt() {
        if (installPrompt) {
            installPrompt.style.display = 'none';
            installPrompt.setAttribute('aria-hidden', 'true');
        }
    }

    // Handle install button click
    function handleInstallClick() {
        if (deferredPrompt) {
            deferredPrompt.prompt();
            deferredPrompt.userChoice.then((choiceResult) => {
                if (choiceResult.outcome === 'accepted') {
                    console.log('User accepted the install prompt');
                    // Track installation in analytics
                    gtag('event', 'install', {
                        'event_category': 'pwa',
                        'event_label': 'install_accepted'
                    });
                } else {
                    console.log('User dismissed the install prompt');
                    // Track dismissal in analytics
                    gtag('event', 'install', {
                        'event_category': 'pwa',
                        'event_label': 'install_dismissed'
                    });
                }
                deferredPrompt = null;
                hideInstallPrompt();
            });
        }
    }

    // Handle dismiss button click
    function handleDismissClick() {
        hideInstallPrompt();
        // Store dismissal in localStorage to prevent showing again for 7 days
        localStorage.setItem('pwaInstallDismissed', Date.now().toString());
    }

    // Check if we should show install prompt
    function shouldShowInstallPrompt() {
        const dismissed = localStorage.getItem('pwaInstallDismissed');
        if (dismissed) {
            const dismissedTime = parseInt(dismissed);
            const daysSinceDismissed = (Date.now() - dismissedTime) / (1000 * 60 * 60 * 24);
            return daysSinceDismissed > 7;
        }
        return true;
    }

    // Initialize install prompt
    function initInstallPrompt() {
        // Listen for beforeinstallprompt event
        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            
            // Only show if not already installed and not recently dismissed
            if (!isPWAInstalled() && shouldShowInstallPrompt()) {
                // Show after 3 seconds of user engagement
                setTimeout(showInstallPrompt, 3000);
            }
        });

        // Handle install button clicks
        if (installBtn) {
            installBtn.addEventListener('click', handleInstallClick);
        }

        if (installDismiss) {
            installDismiss.addEventListener('click', handleDismissClick);
        }

        // Handle app installed event
        window.addEventListener('appinstalled', () => {
            console.log('PWA was installed');
            hideInstallPrompt();
            // Track successful installation
            gtag('event', 'install', {
                'event_category': 'pwa',
                'event_label': 'app_installed'
            });
        });
    }

    // Manual install for iOS
    function showiOSInstallInstructions() {
        if (/iPad|iPhone|iPod/.test(navigator.userAgent) && !window.navigator.standalone) {
            // Create iOS install instructions
            const iosPrompt = document.createElement('div');
            iosPrompt.className = 'ios-install-prompt';
            iosPrompt.innerHTML = `
                <div class="ios-install-content">
                    <h3>Install Sapyyn</h3>
                    <p>To install Sapyyn on your device:</p>
                    <ol>
                        <li>Tap the share button <span aria-hidden="true">⤴</span></li>
                        <li>Scroll down and tap "Add to Home Screen"</li>
                        <li>Tap "Add" in the top right corner</li>
                    </ol>
                    <button class="ios-install-close" aria-label="Close install instructions">Got it</button>
                </div>
            `;
            
            document.body.appendChild(iosPrompt);
            
            const closeBtn = iosPrompt.querySelector('.ios-install-close');
            closeBtn.addEventListener('click', () => {
                document.body.removeChild(iosPrompt);
            });
        }
    }

    // Check if we should show iOS instructions
    function checkiOSInstall() {
        if (/iPad|iPhone|iPod/.test(navigator.userAgent) && 
            !window.navigator.standalone && 
            shouldShowInstallPrompt()) {
            setTimeout(showiOSInstallInstructions, 5000);
        }
    }

    // Initialize when DOM is ready
    function init() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => {
                initInstallPrompt();
                checkiOSInstall();
            });
        } else {
            initInstallPrompt();
            checkiOSInstall();
        }
    }

    // Export for global use
    window.PWAInstall = {
        init: init,
        showInstallPrompt: showInstallPrompt,
        hideInstallPrompt: hideInstallPrompt
    };

    // Initialize
    init();
})();
