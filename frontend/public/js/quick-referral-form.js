// Quick Referral Form JavaScript
class QuickReferralForm {
    constructor() {
        this.currentStep = 'verification';
        this.referralCode = null;
        this.doctorInfo = null;
        this.formData = {};
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupFormValidation();
        this.loadCodeFromUrl();
    }

    // Setup event listeners
    setupEventListeners() {
        // Code verification form
        const codeForm = document.getElementById('codeForm');
        if (codeForm) {
            codeForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.verifyReferralCode();
            });
        }

        // Quick referral form
        const referralForm = document.getElementById('quickReferralForm');
        if (referralForm) {
            referralForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.submitReferral();
            });
        }

        // Code input formatting
        const codeInput = document.getElementById('referralCode');
        if (codeInput) {
            codeInput.addEventListener('input', (e) => {
                this.formatCodeInput(e.target);
            });
        }

        // Phone number formatting
        const phoneInput = document.getElementById('patientPhone');
        if (phoneInput) {
            phoneInput.addEventListener('input', (e) => {
                this.formatPhoneNumber(e.target);
            });
        }
    }

    // Setup form validation
    setupFormValidation() {
        const forms = document.querySelectorAll('form[novalidate]');
        forms.forEach(form => {
            form.addEventListener('submit', event => {
                if (!form.checkValidity()) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            });
        });
    }

    // Load code from URL parameter
    loadCodeFromUrl() {
        const urlParams = new URLSearchParams(window.location.search);
        const code = urlParams.get('code');
        
        if (code) {
            document.getElementById('referralCode').value = code;
            this.verifyReferralCode();
        }
    }

    // Format code input
    formatCodeInput(input) {
        let value = input.value.toUpperCase().replace(/[^A-Z0-9]/g, '');
        if (value.length > 6) {
            value = value.substring(0, 6);
        }
        input.value = value;
    }

    // Format phone number
    formatPhoneNumber(input) {
        let value = input.value.replace(/\D/g, '');
        
        if (value.length >= 6) {
            value = `(${value.slice(0, 3)}) ${value.slice(3, 6)}-${value.slice(6, 10)}`;
        } else if (value.length >= 3) {
            value = `(${value.slice(0, 3)}) ${value.slice(3)}`;
        }
        
        input.value = value;
    }

    // Verify referral code
    async verifyReferralCode() {
        const code = document.getElementById('referralCode').value.trim();
        
        if (!code || code.length !== 6) {
            this.showFieldError(document.getElementById('referralCode'), 'Please enter a valid 6-digit code');
            return;
        }

        this.setLoadingState('verify', true);

        try {
            const response = await fetch(`/api/referral-codes/validate/${code}`);
            const data = await response.json();

            if (response.ok) {
                this.referralCode = code;
                this.doctorInfo = data;
                this.showDoctorInfo(data);
                this.showReferralForm();
                this.showToast('success', 'Code verified successfully!');
            } else {
                this.showFieldError(document.getElementById('referralCode'), data.error || 'Invalid referral code');
            }
        } catch (error) {
            console.error('Code verification error:', error);
            this.showToast('error', 'Network error. Please try again.');
        } finally {
            this.setLoadingState('verify', false);
        }
    }

    // Show doctor information
    showDoctorInfo(data) {
        document.getElementById('doctorName').textContent = data.doctor.name;
        document.getElementById('practiceName').textContent = data.practice?.name || 'N/A';
        document.getElementById('practicePhone').textContent = data.practice?.phone || 'N/A';
        document.getElementById('practiceAddress').textContent = data.practice?.address || 'N/A';
        
        document.getElementById('doctorInfo').style.display = 'block';
    }

    // Show referral form
    showReferralForm() {
        document.getElementById('referralForm').style.display = 'block';
        
        // Scroll to form
        document.getElementById('referralForm').scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }

    // Submit referral
    async submitReferral() {
        if (!this.validateReferralForm()) {
            return;
        }

        this.collectFormData();
        this.setLoadingState('submit', true);

        try {
            const response = await fetch(`/api/referral-codes/use/${this.referralCode}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    referralData: this.formData
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.showSuccessMessage(data);
                this.hideReferralForm();
            } else {
                this.showToast('error', data.error || 'Failed to submit referral');
            }
        } catch (error) {
            console.error('Referral submission error:', error);
            this.showToast('error', 'Network error. Please try again.');
        } finally {
            this.setLoadingState('submit', false);
        }
    }

    // Validate referral form
    validateReferralForm() {
        const form = document.getElementById('quickReferralForm');
        const isValid = form.checkValidity();
        
        if (!isValid) {
            form.classList.add('was-validated');
            
            // Find first invalid field and focus on it
            const firstInvalid = form.querySelector(':invalid');
            if (firstInvalid) {
                firstInvalid.focus();
            }
            
            this.showToast('error', 'Please fill in all required fields');
        }
        
        return isValid;
    }

    // Collect form data
    collectFormData() {
        this.formData = {
            patientName: `${document.getElementById('patientFirstName').value.trim()} ${document.getElementById('patientLastName').value.trim()}`,
            patientPhone: document.getElementById('patientPhone').value.trim(),
            patientEmail: document.getElementById('patientEmail').value.trim(),
            patientDOB: document.getElementById('patientDOB').value,
            patientInsurance: document.getElementById('patientInsurance').value.trim(),
            referralType: document.getElementById('referralType').value,
            urgency: document.getElementById('urgencyLevel').value,
            preferredSpecialist: document.getElementById('preferredSpecialist').value.trim(),
            clinicalNotes: document.getElementById('clinicalNotes').value.trim(),
            timeframe: document.getElementById('timeframe').value,
            patientConsent: document.getElementById('patientConsent').checked,
            followUpRequired: document.getElementById('followUpRequired').checked,
            additionalNotes: document.getElementById('additionalNotes').value.trim(),
            submissionDate: new Date().toISOString()
        };
    }

    // Show success message
    showSuccessMessage(data) {
        document.getElementById('submittedReferralId').textContent = data.referralId;
        document.getElementById('submittedPatientName').textContent = this.formData.patientName;
        document.getElementById('submittedReferralType').textContent = this.formData.referralType;
        
        // Set up tracking link
        const trackBtn = document.getElementById('trackReferralBtn');
        if (trackBtn && data.trackingUrl) {
            trackBtn.href = data.trackingUrl;
        }
        
        document.getElementById('successMessage').style.display = 'block';
        
        // Scroll to success message
        document.getElementById('successMessage').scrollIntoView({ 
            behavior: 'smooth',
            block: 'start'
        });
    }

    // Hide referral form
    hideReferralForm() {
        document.getElementById('referralForm').style.display = 'none';
        document.getElementById('doctorInfo').style.display = 'none';
        document.getElementById('codeVerification').style.display = 'none';
    }

    // Reset form for new referral
    resetForm() {
        // Reset all forms
        document.querySelectorAll('form').forEach(form => {
            form.reset();
            form.classList.remove('was-validated');
        });

        // Reset state
        this.referralCode = null;
        this.doctorInfo = null;
        this.formData = {};
        this.currentStep = 'verification';

        // Show initial form
        document.getElementById('codeVerification').style.display = 'block';
        document.getElementById('doctorInfo').style.display = 'none';
        document.getElementById('referralForm').style.display = 'none';
        document.getElementById('successMessage').style.display = 'none';

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    // Show field error
    showFieldError(field, message) {
        field.classList.add('is-invalid');
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.textContent = message;
        }
    }

    // Clear field error
    clearFieldError(field) {
        field.classList.remove('is-invalid');
    }

    // Set loading state
    setLoadingState(buttonType, isLoading) {
        const button = document.getElementById(`${buttonType}Button`);
        const spinner = document.getElementById(`${buttonType}Spinner`);
        
        if (button) {
            button.disabled = isLoading;
        }
        
        if (spinner) {
            if (isLoading) {
                spinner.classList.remove('d-none');
            } else {
                spinner.classList.add('d-none');
            }
        }

        // Update button text
        if (buttonType === 'verify') {
            const buttonText = button?.querySelector('span:not(.spinner-border)');
            if (buttonText) {
                buttonText.textContent = isLoading ? 'Verifying...' : 'Verify Code';
            }
        } else if (buttonType === 'submit') {
            const buttonText = button?.querySelector('span:not(.spinner-border)');
            if (buttonText) {
                buttonText.textContent = isLoading ? 'Submitting...' : 'Submit Referral';
            }
        }
    }

    // Show toast notification
    showToast(type, message, duration = 5000) {
        const toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) return;

        const toastId = 'toast-' + Date.now();
        const iconClass = type === 'success' ? 'fa-check-circle text-success' : 'fa-exclamation-triangle text-danger';
        const headerText = type === 'success' ? 'Success' : 'Error';

        const toastHtml = `
            <div id="${toastId}" class="toast show" role="alert">
                <div class="toast-header">
                    <i class="fas ${iconClass} me-2"></i>
                    <strong class="me-auto">${headerText}</strong>
                    <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
                </div>
                <div class="toast-body">
                    ${message}
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);

        // Auto-remove
        setTimeout(() => {
            const toast = document.getElementById(toastId);
            if (toast) {
                toast.remove();
            }
        }, duration);
    }

    // Show help modal or tooltip
    showHelp(topic) {
        let helpContent = '';
        
        switch (topic) {
            case 'referralCode':
                helpContent = 'The referral code is a 6-digit alphanumeric code provided by your doctor. It allows you to submit a referral request directly to specialists.';
                break;
            case 'urgencyLevel':
                helpContent = `
                    <strong>Routine:</strong> Standard referral, usually scheduled within 2-4 weeks<br>
                    <strong>Urgent:</strong> Needs attention within 1-2 weeks<br>
                    <strong>Emergency:</strong> Requires immediate attention within 24-48 hours
                `;
                break;
            case 'clinicalNotes':
                helpContent = 'Please provide detailed information about symptoms, current condition, relevant medical history, and any specific requirements for the specialist.';
                break;
            default:
                helpContent = 'Help information not available for this topic.';
        }
        
        this.showToast('info', helpContent, 8000);
    }
}

// Global functions
function resetForm() {
    if (window.quickReferralForm) {
        window.quickReferralForm.resetForm();
    }
}

function showHelp(topic) {
    if (window.quickReferralForm) {
        window.quickReferralForm.showHelp(topic);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.quickReferralForm = new QuickReferralForm();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = QuickReferralForm;
}