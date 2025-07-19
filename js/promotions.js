// Promotions settings handling

document.addEventListener('DOMContentLoaded', function() {
    // Handle promotion settings form submission
    const promotionSettingsForm = document.getElementById('promotion-settings-form');
    if (promotionSettingsForm) {
        promotionSettingsForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const optOut = document.getElementById('opt_out').checked;
            const csrfToken = document.querySelector('input[name="csrf_token"]').value;
            
            // Submit settings via API
            fetch('/api/user/promotion-settings', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    opt_out: optOut,
                    csrf_token: csrfToken
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Show success message
                showMessage('Promotion settings updated successfully', 'success');
            })
            .catch(error => {
                console.error('Error updating promotion settings:', error);
                showMessage('Failed to update promotion settings: ' + error.message, 'danger');
            });
        });
    }
    
    // Load current promotion settings
    function loadPromotionSettings() {
        fetch('/api/user/promotion-settings')
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                
                // Update form
                document.getElementById('opt_out').checked = data.opt_out;
            })
            .catch(error => {
                console.error('Error loading promotion settings:', error);
            });
    }
    
    // Show message
    function showMessage(message, type) {
        // Create alert element
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.setAttribute('role', 'alert');
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        `;
        
        // Add to page
        const cardBody = document.querySelector('#promotion-settings .card-body');
        cardBody.insertBefore(alert, cardBody.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alert.classList.remove('show');
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    }
    
    // Load settings when tab is shown
    const promotionTab = document.querySelector('a[href="#promotion-settings"]');
    if (promotionTab) {
        promotionTab.addEventListener('shown.bs.tab', function() {
            loadPromotionSettings();
        });
    }
});