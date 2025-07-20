// Tab functionality
function showTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });

    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-button');
    tabButtons.forEach(button => {
        button.classList.remove('active');
    });

    // Show selected tab content
    document.getElementById(tabName).classList.add('active');

    // Add active class to clicked button
    event.target.classList.add('active');
}

// Notification system
function showNotification(message, type = 'info') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    notification.classList.add('show');

    setTimeout(() => {
        notification.classList.remove('show');
    }, 4000);
}

// Handle referral form submission
document.getElementById('referralForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const submitButton = this.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    
    try {
        // Show loading state
        submitButton.innerHTML = '<span class="spinner"></span>Submitting...';
        submitButton.disabled = true;
        
        const formData = new FormData(this);
        
        const response = await fetch('/submit-referral', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('Referral submitted successfully!', 'success');
            this.reset();
        } else {
            throw new Error(result.error || 'Failed to submit referral');
        }
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        // Reset button state
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
    }
});

// Handle file upload form submission
document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const submitButton = this.querySelector('button[type="submit"]');
    const originalText = submitButton.textContent;
    
    try {
        // Show loading state
        submitButton.innerHTML = '<span class="spinner"></span>Uploading...';
        submitButton.disabled = true;
        
        const formData = new FormData(this);
        
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            showNotification('File uploaded successfully!', 'success');
            this.reset();
        } else {
            throw new Error(result.error || 'Failed to upload file');
        }
    } catch (error) {
        showNotification(`Error: ${error.message}`, 'error');
    } finally {
        // Reset button state
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;
    }
});

// Load and display referrals
async function loadReferrals() {
    const referralsList = document.getElementById('referralsList');
    
    try {
        referralsList.innerHTML = '<div class="spinner"></div> Loading referrals...';
        
        const response = await fetch('/referrals');
        const referrals = await response.json();
        
        if (referrals.length === 0) {
            referralsList.innerHTML = '<p>No referrals found.</p>';
            return;
        }
        
        const referralsHTML = referrals.map((referral, index) => {
            const urgencyClass = `urgency-${referral.urgency}`;
            const filesText = referral.uploadedFiles?.length > 0 
                ? `${referral.uploadedFiles.length} file(s) attached`
                : 'No files attached';
            
            return `
                <div class="referral-item">
                    <div class="referral-header">
                        <div class="referral-name">${referral.patientName}</div>
                        <div class="referral-urgency ${urgencyClass}">${referral.urgency}</div>
                    </div>
                    <div class="referral-details">
                        <strong>Type:</strong> ${referral.referralType.replace(/_/g, ' ')}<br>
                        <strong>Patient ID:</strong> ${referral.patientId || 'Not provided'}<br>
                        <strong>Date:</strong> ${new Date(referral.timestamp).toLocaleString()}<br>
                        ${referral.notes ? `<strong>Notes:</strong> ${referral.notes}<br>` : ''}
                    </div>
                    <div class="referral-files">${filesText}</div>
                </div>
            `;
        }).join('');
        
        referralsList.innerHTML = referralsHTML;
        
    } catch (error) {
        referralsList.innerHTML = '<p>Error loading referrals. Please try again.</p>';
        showNotification(`Error: ${error.message}`, 'error');
    }
}

// File input validation and preview
document.getElementById('documents').addEventListener('change', function(e) {
    const files = Array.from(e.target.files);
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = ['application/pdf', 'application/msword', 
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                         'image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    
    const invalidFiles = files.filter(file => {
        return file.size > maxSize || !allowedTypes.includes(file.type);
    });
    
    if (invalidFiles.length > 0) {
        showNotification('Some files are too large or have invalid format', 'error');
        e.target.value = '';
        return;
    }
    
    if (files.length > 0) {
        const fileNames = files.map(file => file.name).join(', ');
        showNotification(`Selected ${files.length} file(s): ${fileNames}`, 'info');
    }
});

document.getElementById('file').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const maxSize = 10 * 1024 * 1024; // 10MB
    const allowedTypes = ['application/pdf', 'application/msword', 
                         'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                         'image/jpeg', 'image/jpg', 'image/png', 'image/gif'];
    
    if (file.size > maxSize) {
        showNotification('File is too large. Maximum size is 10MB.', 'error');
        e.target.value = '';
        return;
    }
    
    if (!allowedTypes.includes(file.type)) {
        showNotification('Invalid file type. Please select a PDF, DOC, DOCX, or image file.', 'error');
        e.target.value = '';
        return;
    }
    
    showNotification(`Selected file: ${file.name}`, 'info');
});

// Initialize the page
document.addEventListener('DOMContentLoaded', function() {
    // Load referrals when the view tab is first shown
    const viewTab = document.querySelector('[data-tab="view"]');
    viewTab.addEventListener('click', function() {
        // Small delay to ensure tab is visible
        setTimeout(loadReferrals, 100);
    });
    
    // Add form validation
    const requiredFields = document.querySelectorAll('[required]');
    requiredFields.forEach(field => {
        field.addEventListener('invalid', function(e) {
            showNotification('Please fill in all required fields', 'error');
        });
    });
    
    showNotification('Sapyyn Patient Referral System loaded successfully!', 'success');
});