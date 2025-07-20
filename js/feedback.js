/**
 * User Feedback Collection System
 * Collects qualitative feedback for UX optimization
 */

class UserFeedbackSystem {
    constructor() {
        this.isVisible = false;
        this.feedbackData = [];
        this.init();
    }
    
    init() {
        this.createFeedbackWidget();
        this.setupTriggers();
        this.setupEventListeners();
    }
    
    createFeedbackWidget() {
        // Create feedback button
        const feedbackButton = document.createElement('div');
        feedbackButton.id = 'feedback-button';
        feedbackButton.innerHTML = `
            <button class="btn btn-primary" title="Give Feedback">
                <i class="bi bi-chat-square-text"></i>
                <span>Feedback</span>
            </button>
        `;
        feedbackButton.style.cssText = `
            position: fixed;
            right: 20px;
            bottom: 20px;
            z-index: 1000;
            border-radius: 50px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            transition: all 0.3s ease;
        `;
        
        // Create feedback modal
        const feedbackModal = document.createElement('div');
        feedbackModal.id = 'feedback-modal';
        feedbackModal.innerHTML = this.createModalHTML();
        feedbackModal.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1001;
            display: none;
            align-items: center;
            justify-content: center;
        `;
        
        document.body.appendChild(feedbackButton);
        document.body.appendChild(feedbackModal);
    }
    
    createModalHTML() {
        return `
            <div class="feedback-content" style="
                background: white;
                border-radius: 12px;
                padding: 30px;
                max-width: 500px;
                width: 90%;
                max-height: 80vh;
                overflow-y: auto;
                position: relative;
            ">
                <button class="close-feedback" style="
                    position: absolute;
                    right: 15px;
                    top: 15px;
                    background: none;
                    border: none;
                    font-size: 24px;
                    cursor: pointer;
                    color: #666;
                ">&times;</button>
                
                <h3 style="margin-bottom: 20px; color: #333;">
                    <i class="bi bi-chat-square-text me-2"></i>
                    Help Us Improve Sapyyn
                </h3>
                
                <form id="feedback-form">
                    <div class="mb-3">
                        <label class="form-label">What brings you to Sapyyn today?</label>
                        <select class="form-select" name="visit_purpose" required>
                            <option value="">Select purpose...</option>
                            <option value="create_referral">Create a patient referral</option>
                            <option value="track_referral">Track existing referral</option>
                            <option value="upload_documents">Upload documents</option>
                            <option value="learn_about_service">Learn about the service</option>
                            <option value="manage_account">Manage my account</option>
                            <option value="other">Other</option>
                        </select>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">How easy was it to find what you needed?</label>
                        <div class="btn-group" role="group" style="width: 100%;">
                            <input type="radio" class="btn-check" name="ease_of_use" value="very_easy" id="ease1">
                            <label class="btn btn-outline-success" for="ease1">Very Easy</label>
                            
                            <input type="radio" class="btn-check" name="ease_of_use" value="easy" id="ease2">
                            <label class="btn btn-outline-success" for="ease2">Easy</label>
                            
                            <input type="radio" class="btn-check" name="ease_of_use" value="neutral" id="ease3">
                            <label class="btn btn-outline-warning" for="ease3">Neutral</label>
                            
                            <input type="radio" class="btn-check" name="ease_of_use" value="difficult" id="ease4">
                            <label class="btn btn-outline-danger" for="ease4">Difficult</label>
                            
                            <input type="radio" class="btn-check" name="ease_of_use" value="very_difficult" id="ease5">
                            <label class="btn btn-outline-danger" for="ease5">Very Difficult</label>
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Is there anything confusing or missing on this page?</label>
                        <textarea class="form-control" name="confusion_feedback" rows="3" 
                                  placeholder="Tell us what could be clearer or what information you expected to find..."></textarea>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">How likely are you to recommend Sapyyn to a colleague?</label>
                        <div class="nps-scale" style="display: flex; gap: 5px; margin-top: 10px;">
                            ${Array.from({length: 11}, (_, i) => `
                                <label style="flex: 1; text-align: center;">
                                    <input type="radio" name="nps_score" value="${i}" style="display: none;">
                                    <div class="nps-button" data-value="${i}" style="
                                        padding: 8px 4px;
                                        border: 1px solid #ddd;
                                        border-radius: 4px;
                                        cursor: pointer;
                                        font-weight: bold;
                                        text-align: center;
                                        background: #f8f9fa;
                                        transition: all 0.2s;
                                    ">${i}</div>
                                    <small style="font-size: 10px; display: block; margin-top: 2px;">
                                        ${i === 0 ? 'Not likely' : i === 10 ? 'Very likely' : ''}
                                    </small>
                                </label>
                            `).join('')}
                        </div>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Any additional comments?</label>
                        <textarea class="form-control" name="additional_comments" rows="3" 
                                  placeholder="Share any other thoughts or suggestions..."></textarea>
                    </div>
                    
                    <div class="mb-3">
                        <label class="form-label">Contact Information (Optional)</label>
                        <input type="email" class="form-control" name="contact_email" 
                               placeholder="your.email@example.com">
                        <small class="form-text text-muted">Only if you'd like us to follow up with you</small>
                    </div>
                    
                    <div class="d-grid gap-2 d-md-flex justify-content-md-end">
                        <button type="button" class="btn btn-secondary me-md-2 close-feedback">Skip</button>
                        <button type="submit" class="btn btn-primary">Submit Feedback</button>
                    </div>
                </form>
                
                <div id="feedback-success" style="display: none; text-align: center; padding: 20px;">
                    <i class="bi bi-check-circle-fill text-success" style="font-size: 48px;"></i>
                    <h4 class="mt-3">Thank you!</h4>
                    <p>Your feedback helps us improve Sapyyn for everyone.</p>
                </div>
            </div>
        `;
    }
    
    setupTriggers() {
        // Show feedback widget after 30 seconds
        setTimeout(() => {
            this.showFeedbackButton();
        }, 30000);
        
        // Show feedback on exit intent
        let exitIntentShown = false;
        document.addEventListener('mouseleave', (e) => {
            if (e.clientY <= 0 && !exitIntentShown && !this.isVisible) {
                exitIntentShown = true;
                this.showFeedbackModal();
            }
        });
        
        // Show feedback after significant scroll
        let scrollFeedbackShown = false;
        window.addEventListener('scroll', () => {
            if (!scrollFeedbackShown && this.getScrollPercentage() > 80) {
                scrollFeedbackShown = true;
                setTimeout(() => {
                    if (!this.isVisible) {
                        this.showFeedbackButton();
                    }
                }, 5000);
            }
        });
    }
    
    setupEventListeners() {
        // Feedback button click
        document.addEventListener('click', (e) => {
            if (e.target.closest('#feedback-button')) {
                this.showFeedbackModal();
            }
            
            if (e.target.closest('.close-feedback') || e.target.id === 'feedback-modal') {
                this.hideFeedbackModal();
            }
        });
        
        // Prevent modal from closing when clicking inside content
        document.addEventListener('click', (e) => {
            if (e.target.closest('.feedback-content')) {
                e.stopPropagation();
            }
        });
        
        // NPS scale interaction
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('nps-button')) {
                const npsButtons = document.querySelectorAll('.nps-button');
                npsButtons.forEach(btn => {
                    btn.style.background = '#f8f9fa';
                    btn.style.color = '#333';
                });
                
                e.target.style.background = '#0d6efd';
                e.target.style.color = 'white';
                
                const radioInput = e.target.parentElement.querySelector('input[type="radio"]');
                radioInput.checked = true;
            }
        });
        
        // Form submission
        document.addEventListener('submit', (e) => {
            if (e.target.id === 'feedback-form') {
                e.preventDefault();
                this.submitFeedback(e.target);
            }
        });
        
        // Escape key to close modal
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isVisible) {
                this.hideFeedbackModal();
            }
        });
    }
    
    showFeedbackButton() {
        const button = document.getElementById('feedback-button');
        if (button) {
            button.style.display = 'block';
            button.style.animation = 'slideInRight 0.5s ease-out';
        }
    }
    
    showFeedbackModal() {
        const modal = document.getElementById('feedback-modal');
        if (modal) {
            modal.style.display = 'flex';
            this.isVisible = true;
            
            // Track feedback modal shown
            if (window.trackEvent) {
                window.trackEvent('feedback_modal_shown', {
                    trigger: 'user_initiated',
                    page_url: window.location.href
                });
            }
        }
    }
    
    hideFeedbackModal() {
        const modal = document.getElementById('feedback-modal');
        if (modal) {
            modal.style.display = 'none';
            this.isVisible = false;
        }
    }
    
    async submitFeedback(form) {
        const formData = new FormData(form);
        const feedbackData = Object.fromEntries(formData.entries());
        
        // Add page context
        feedbackData.page_url = window.location.href;
        feedbackData.page_title = document.title;
        feedbackData.timestamp = new Date().toISOString();
        feedbackData.user_agent = navigator.userAgent;
        feedbackData.screen_resolution = `${screen.width}x${screen.height}`;
        feedbackData.session_duration = Math.round((Date.now() - window.SapyynAnalytics?.startTime || Date.now()) / 1000);
        
        try {
            // Send to server
            const response = await fetch('/api/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(feedbackData)
            });
            
            if (response.ok) {
                this.showSuccessMessage();
                
                // Track successful feedback submission
                if (window.trackEvent) {
                    window.trackEvent('feedback_submitted', {
                        visit_purpose: feedbackData.visit_purpose,
                        ease_of_use: feedbackData.ease_of_use,
                        nps_score: feedbackData.nps_score,
                        has_confusion_feedback: !!feedbackData.confusion_feedback,
                        has_additional_comments: !!feedbackData.additional_comments,
                        provided_email: !!feedbackData.contact_email
                    });
                }
                
                // Auto-hide after success
                setTimeout(() => {
                    this.hideFeedbackModal();
                }, 3000);
                
            } else {
                throw new Error('Failed to submit feedback');
            }
            
        } catch (error) {
            console.error('Error submitting feedback:', error);
            alert('Sorry, there was an error submitting your feedback. Please try again.');
            
            // Track feedback submission error
            if (window.trackEvent) {
                window.trackEvent('feedback_submission_error', {
                    error_message: error.message
                });
            }
        }
    }
    
    showSuccessMessage() {
        const form = document.getElementById('feedback-form');
        const success = document.getElementById('feedback-success');
        if (form && success) {
            form.style.display = 'none';
            success.style.display = 'block';
        }
    }
    
    getScrollPercentage() {
        const scrollTop = window.pageYOffset;
        const docHeight = document.documentElement.scrollHeight - window.innerHeight;
        return Math.round((scrollTop / docHeight) * 100);
    }
}

// Initialize feedback system when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        new UserFeedbackSystem();
    });
} else {
    new UserFeedbackSystem();
}

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }
    
    #feedback-button:hover {
        transform: scale(1.05);
    }
    
    .nps-button:hover {
        background: #e9ecef !important;
        border-color: #0d6efd !important;
    }
`;
document.head.appendChild(style);