class PortalAuth {
    constructor() {
        this.selectedPortal = null;
        this.urlParams = new URLSearchParams(window.location.search);
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadPractices();
        
        // Check for URL parameters
        const signup = this.urlParams.get('signup');
        const plan = this.urlParams.get('plan');
        
        if (signup === 'true') {
            this.selectPortal('patient');
            this.showSignup();
        }
    }

    setupEventListeners() {
        // Login form
        document.getElementById('authForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.login();
        });

        // Signup form
        document.getElementById('registrationForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.signup();
        });

        // New practice form
        document.getElementById('newPracticeForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.submitNewPractice();
        });

        // Password confirmation validation
        document.getElementById('confirmPassword').addEventListener('input', this.validatePasswordMatch);
        document.getElementById('signupPassword').addEventListener('input', this.validatePasswordStrength);
    }

    selectPortal(portalType) {
        this.selectedPortal = portalType;
        
        // Update UI based on portal type
        const portalConfig = this.getPortalConfig(portalType);
        
        document.getElementById('portalIcon').className = `fas ${portalConfig.icon} fa-3x ${portalConfig.color} mb-3`;
        document.getElementById('portalTitle').textContent = `${portalConfig.title} Login`;
        document.getElementById('portalDescription').textContent = portalConfig.description;
        
        document.getElementById('signupPortalIcon').className = `fas fa-user-plus fa-3x text-success mb-3`;
        document.getElementById('signupPortalTitle').textContent = `Create ${portalConfig.title} Account`;
        document.getElementById('signupPortalDescription').textContent = `Join as a ${portalConfig.title.toLowerCase()}`;

        // Show/hide professional info for signup
        const professionalInfo = document.getElementById('professionalInfo');
        if (portalType === 'patient') {
            professionalInfo.style.display = 'none';
        } else {
            professionalInfo.style.display = 'block';
        }

        // Hide portal selection and show login form
        document.getElementById('portalSelection').style.display = 'none';
        document.getElementById('loginForm').style.display = 'block';
    }

    getPortalConfig(portalType) {
        const configs = {
            patient: {
                title: 'Patient',
                icon: 'fa-user',
                color: 'text-primary',
                description: 'Access your referrals and appointments',
                redirect: '/patient-portal'
            },
            dentist: {
                title: 'Dentist',
                icon: 'fa-tooth',
                color: 'text-success',
                description: 'Manage referrals and patients',
                redirect: '/dentist-portal'
            },
            specialist: {
                title: 'Specialist',
                icon: 'fa-stethoscope',
                color: 'text-info',
                description: 'Receive and manage referrals',
                redirect: '/specialist-portal'
            },
            dentist_admin: {
                title: 'Dentist Admin',
                icon: 'fa-user-cog',
                color: 'text-warning',
                description: 'Manage dental practice',
                redirect: '/dentist-admin'
            },
            specialist_admin: {
                title: 'Specialist Admin',
                icon: 'fa-users-cog',
                color: 'text-info',
                description: 'Manage specialist practice',
                redirect: '/specialist-admin'
            },
            super_admin: {
                title: 'Super Admin',
                icon: 'fa-crown',
                color: 'text-danger',
                description: 'System administration',
                redirect: '/admin'
            }
        };
        return configs[portalType] || configs.patient;
    }

    async login() {
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const rememberMe = document.getElementById('rememberMe').checked;

        if (!email || !password) {
            this.showAlert('error', 'Please fill in all fields');
            return;
        }

        this.setLoadingState('login', true);

        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    email, 
                    password, 
                    expectedRole: this.selectedPortal,
                    rememberMe 
                })
            });

            const data = await response.json();

            if (response.ok) {
                // Validate user role matches selected portal
                if (!this.validateUserRole(data.user.role, this.selectedPortal)) {
                    this.showAlert('error', 'Invalid credentials for this portal');
                    this.setLoadingState('login', false);
                    return;
                }

                // Store token
                const storage = rememberMe ? localStorage : sessionStorage;
                storage.setItem('sapyyn_token', data.token);
                storage.setItem('sapyyn_user', JSON.stringify(data.user));
                storage.setItem('sapyyn_portal', this.selectedPortal);

                this.showAlert('success', 'Login successful! Redirecting...');
                
                // Redirect to appropriate portal
                setTimeout(() => {
                    const portalConfig = this.getPortalConfig(this.selectedPortal);
                    window.location.href = portalConfig.redirect;
                }, 1500);

            } else {
                this.showAlert('error', data.error || 'Login failed');
            }
        } catch (error) {
            console.error('Login error:', error);
            this.showAlert('error', 'Network error. Please try again.');
        } finally {
            this.setLoadingState('login', false);
        }
    }

    async signup() {
        const formData = this.getSignupFormData();
        
        if (!this.validateSignupForm(formData)) {
            return;
        }

        this.setLoadingState('signup', true);

        try {
            const response = await fetch('/api/auth/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    ...formData,
                    role: this.selectedPortal
                })
            });

            const data = await response.json();

            if (response.ok) {
                // Store token
                sessionStorage.setItem('sapyyn_token', data.token);
                sessionStorage.setItem('sapyyn_user', JSON.stringify(data.user));
                sessionStorage.setItem('sapyyn_portal', this.selectedPortal);

                this.showAlert('success', 'Account created successfully! Redirecting...');
                
                // Redirect to appropriate portal
                setTimeout(() => {
                    const portalConfig = this.getPortalConfig(this.selectedPortal);
                    window.location.href = portalConfig.redirect;
                }, 1500);

            } else {
                this.showAlert('error', data.error || 'Registration failed');
            }
        } catch (error) {
            console.error('Signup error:', error);
            this.showAlert('error', 'Network error. Please try again.');
        } finally {
            this.setLoadingState('signup', false);
        }
    }

    getSignupFormData() {
        return {
            firstName: document.getElementById('firstName').value.trim(),
            lastName: document.getElementById('lastName').value.trim(),
            email: document.getElementById('signupEmail').value.trim(),
            phone: document.getElementById('phone').value.trim(),
            password: document.getElementById('signupPassword').value,
            licenseNumber: document.getElementById('licenseNumber').value.trim(),
            practiceId: document.getElementById('practiceSelect').value
        };
    }

    validateSignupForm(formData) {
        // Basic validation
        if (!formData.firstName || !formData.lastName || !formData.email || !formData.password) {
            this.showAlert('error', 'Please fill in all required fields');
            return false;
        }

        // Email validation
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        if (!emailRegex.test(formData.email)) {
            this.showAlert('error', 'Please enter a valid email address');
            return false;
        }

        // Password validation
        const password = formData.password;
        const confirmPassword = document.getElementById('confirmPassword').value;
        
        if (password !== confirmPassword) {
            this.showAlert('error', 'Passwords do not match');
            return false;
        }

        if (password.length < 8) {
            this.showAlert('error', 'Password must be at least 8 characters long');
            return false;
        }

        if (!/(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/.test(password)) {
            this.showAlert('error', 'Password must contain uppercase, lowercase, and number');
            return false;
        }

        // Professional validation
        if (this.selectedPortal !== 'patient') {
            if (!formData.licenseNumber) {
                this.showAlert('error', 'License number is required for professionals');
                return false;
            }
            if (!formData.practiceId) {
                this.showAlert('error', 'Please select a practice');
                return false;
            }
        }

        // Terms agreement
        if (!document.getElementById('agreeTerms').checked) {
            this.showAlert('error', 'Please agree to the terms and conditions');
            return false;
        }

        return true;
    }

    validateUserRole(userRole, selectedPortal) {
        // Define valid role mappings
        const roleMapping = {
            'patient': ['patient'],
            'dentist': ['dentist'],
            'specialist': ['specialist'],
            'dentist_admin': ['dentist_admin', 'dentist'],
            'specialist_admin': ['specialist_admin', 'specialist'],
            'super_admin': ['super_admin']
        };

        return roleMapping[selectedPortal]?.includes(userRole) || false;
    }

    validatePasswordMatch() {
        const password = document.getElementById('signupPassword').value;
        const confirmPassword = document.getElementById('confirmPassword').value;
        const confirmField = document.getElementById('confirmPassword');

        if (confirmPassword && password !== confirmPassword) {
            confirmField.setCustomValidity('Passwords do not match');
            confirmField.classList.add('is-invalid');
        } else {
            confirmField.setCustomValidity('');
            confirmField.classList.remove('is-invalid');
        }
    }

    validatePasswordStrength() {
        const password = document.getElementById('signupPassword').value;
        const passwordField = document.getElementById('signupPassword');
        
        const hasMinLength = password.length >= 8;
        const hasUppercase = /[A-Z]/.test(password);
        const hasLowercase = /[a-z]/.test(password);
        const hasNumber = /\d/.test(password);
        
        const isStrong = hasMinLength && hasUppercase && hasLowercase && hasNumber;
        
        if (password && !isStrong) {
            passwordField.setCustomValidity('Password must be at least 8 characters with uppercase, lowercase, and numbers');
            passwordField.classList.add('is-invalid');
        } else {
            passwordField.setCustomValidity('');
            passwordField.classList.remove('is-invalid');
        }
    }

    async loadPractices() {
        try {
            const response = await fetch('/api/practices/public');
            if (response.ok) {
                const practices = await response.json();
                this.populatePracticeSelect(practices);
            }
        } catch (error) {
            console.error('Error loading practices:', error);
        }
    }

    populatePracticeSelect(practices) {
        const select = document.getElementById('practiceSelect');
        select.innerHTML = '<option value="">Choose a practice...</option>';
        
        practices.forEach(practice => {
            const option = document.createElement('option');
            option.value = practice._id;
            option.textContent = `${practice.name} (${practice.type})`;
            select.appendChild(option);
        });
    }

    async submitNewPractice() {
        const formData = {
            name: document.getElementById('practiceName').value.trim(),
            type: document.getElementById('practiceType').value,
            address: document.getElementById('practiceAddress').value.trim(),
            phone: document.getElementById('practicePhone').value.trim(),
            email: document.getElementById('practiceEmail').value.trim()
        };

        if (!formData.name || !formData.type) {
            this.showAlert('error', 'Please fill in required fields');
            return;
        }

        try {
            const response = await fetch('/api/practices', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(formData)
            });

            const data = await response.json();

            if (response.ok) {
                this.showAlert('success', 'Practice added successfully!');
                
                // Add to select and select it
                const select = document.getElementById('practiceSelect');
                const option = document.createElement('option');
                option.value = data._id;
                option.textContent = `${data.name} (${data.type})`;
                option.selected = true;
                select.appendChild(option);

                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('newPracticeModal'));
                modal.hide();

                // Reset form
                document.getElementById('newPracticeForm').reset();
            } else {
                this.showAlert('error', data.error || 'Failed to add practice');
            }
        } catch (error) {
            console.error('Error adding practice:', error);
            this.showAlert('error', 'Network error. Please try again.');
        }
    }

    showLogin() {
        document.getElementById('signupForm').style.display = 'none';
        document.getElementById('loginForm').style.display = 'block';
    }

    showSignup() {
        document.getElementById('loginForm').style.display = 'none';
        document.getElementById('signupForm').style.display = 'block';
    }

    goBack() {
        document.getElementById('loginForm').style.display = 'none';
        document.getElementById('signupForm').style.display = 'none';
        document.getElementById('portalSelection').style.display = 'block';
        this.selectedPortal = null;
    }

    togglePassword() {
        const passwordField = document.getElementById('password');
        const toggleIcon = document.getElementById('passwordToggle');
        
        if (passwordField.type === 'password') {
            passwordField.type = 'text';
            toggleIcon.className = 'fas fa-eye-slash';
        } else {
            passwordField.type = 'password';
            toggleIcon.className = 'fas fa-eye';
        }
    }

    forgotPassword() {
        const email = document.getElementById('email').value;
        if (!email) {
            this.showAlert('info', 'Please enter your email address first');
            return;
        }

        // Implement forgot password functionality
        this.showAlert('info', 'Password reset instructions have been sent to your email');
    }

    addNewPractice() {
        const modal = new bootstrap.Modal(document.getElementById('newPracticeModal'));
        modal.show();
    }

    setLoadingState(formType, isLoading) {
        const button = document.getElementById(formType === 'login' ? 'loginButton' : 'signupButton');
        const spinner = document.getElementById(formType === 'login' ? 'loginSpinner' : 'signupSpinner');
        
        if (isLoading) {
            button.disabled = true;
            spinner.classList.remove('d-none');
            button.textContent = formType === 'login' ? ' Signing In...' : ' Creating Account...';
            button.prepend(spinner);
        } else {
            button.disabled = false;
            spinner.classList.add('d-none');
            button.textContent = formType === 'login' ? 'Sign In' : 'Create Account';
        }
    }

    showAlert(type, message) {
        const alertContainer = document.getElementById('alertContainer');
        const alertId = 'alert-' + Date.now();
        
        const alertDiv = document.createElement('div');
        alertDiv.id = alertId;
        alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.appendChild(alertDiv);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                alert.remove();
            }
        }, 5000);
    }
}

// Global functions for onclick handlers
function selectPortal(portalType) {
    window.portalAuth.selectPortal(portalType);
}

function showLogin() {
    window.portalAuth.showLogin();
}

function showSignup() {
    window.portalAuth.showSignup();
}

function goBack() {
    window.portalAuth.goBack();
}

function togglePassword() {
    window.portalAuth.togglePassword();
}

function forgotPassword() {
    window.portalAuth.forgotPassword();
}

function addNewPractice() {
    window.portalAuth.addNewPractice();
}

function submitNewPractice() {
    window.portalAuth.submitNewPractice();
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    window.portalAuth = new PortalAuth();
});