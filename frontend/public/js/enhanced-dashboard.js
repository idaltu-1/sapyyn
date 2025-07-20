// Enhanced Dashboard JavaScript
class EnhancedDashboard {
    constructor() {
        this.currentUser = null;
        this.dashboardData = {
            totalReferrals: 0,
            completedReferrals: 0,
            totalPoints: 0,
            averageRating: 0,
            myReferralCode: '',
            codeUsageCount: 0
        };
        this.charts = {};
        this.currentSection = 'dashboard';
        this.init();
    }

    async init() {
        await this.loadUserData();
        this.setupEventListeners();
        this.loadDashboardData();
        this.loadMyReferralCode();
        this.loadNotifications();
        this.updateDateDisplay();
        this.initializeCharts();
    }

    // Load user data
    async loadUserData() {
        try {
            const token = localStorage.getItem('sapyyn_token') || sessionStorage.getItem('sapyyn_token');
            const response = await fetch('/api/dashboard/profile', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.currentUser = data.user;
                this.updateUserDisplay();
            }
        } catch (error) {
            console.error('Error loading user data:', error);
        }
    }

    // Setup event listeners
    setupEventListeners() {
        // Navigation links
        document.querySelectorAll('.nav-link[data-section]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchSection(link.dataset.section);
            });
        });

        // Quick actions
        document.addEventListener('click', (e) => {
            if (e.target.closest('[onclick*="showQuickReferral"]')) {
                this.showQuickReferralModal();
            }
            if (e.target.closest('[onclick*="copyReferralCode"]')) {
                this.copyReferralCodeToClipboard();
            }
        });

        // Refresh data every 5 minutes
        setInterval(() => {
            this.refreshDashboardData();
        }, 5 * 60 * 1000);
    }

    // Update user display
    updateUserDisplay() {
        if (this.currentUser) {
            const userNameElements = document.querySelectorAll('#userName, #welcomeUserName');
            userNameElements.forEach(el => {
                if (el) {
                    el.textContent = `Dr. ${this.currentUser.firstName} ${this.currentUser.lastName}`;
                }
            });
        }
    }

    // Load dashboard data
    async loadDashboardData() {
        try {
            const token = localStorage.getItem('sapyyn_token') || sessionStorage.getItem('sapyyn_token');
            const response = await fetch('/api/dashboard/stats', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.dashboardData = { ...this.dashboardData, ...data };
                this.updateDashboardDisplay();
                this.updateSidebarStats();
            }
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }

    // Update dashboard display
    updateDashboardDisplay() {
        // Update KPI cards
        document.getElementById('dashboardTotalReferrals').textContent = this.dashboardData.totalReferrals.toLocaleString();
        document.getElementById('completedReferrals').textContent = this.dashboardData.completedReferrals.toLocaleString();
        document.getElementById('dashboardTotalPoints').textContent = this.dashboardData.totalPoints.toLocaleString();
        document.getElementById('averageRating').textContent = this.dashboardData.averageRating.toFixed(1);

        // Update trends
        this.updateTrendIndicators();

        // Load charts data
        this.loadChartsData();

        // Load recent activity
        this.loadRecentActivity();

        // Load monthly goals
        this.loadMonthlyGoals();
    }

    // Update sidebar stats
    updateSidebarStats() {
        document.getElementById('totalReferrals').textContent = this.dashboardData.totalReferrals;
        document.getElementById('totalPoints').textContent = this.dashboardData.totalPoints.toLocaleString();
        document.getElementById('currentRank').textContent = '#' + (this.dashboardData.rank || '-');
        document.getElementById('completedCourses').textContent = this.dashboardData.completedCourses || 0;
    }

    // Update trend indicators
    updateTrendIndicators() {
        // Calculate trends (this would come from backend in real implementation)
        const referralTrend = this.calculateTrend(this.dashboardData.totalReferrals, this.dashboardData.lastMonthReferrals);
        const completedTrend = this.calculateTrend(this.dashboardData.completedReferrals, this.dashboardData.lastMonthCompleted);
        const pointsTrend = this.dashboardData.pointsEarnedThisMonth || 0;

        document.getElementById('referralTrend').textContent = `+${referralTrend}%`;
        document.getElementById('completedTrend').textContent = `+${completedTrend}%`;
        document.getElementById('pointsTrend').textContent = `+${pointsTrend}`;
        document.getElementById('ratingTrend').textContent = this.dashboardData.averageRating.toFixed(1);
    }

    // Calculate trend percentage
    calculateTrend(current, previous) {
        if (previous === 0) return current > 0 ? 100 : 0;
        return Math.round(((current - previous) / previous) * 100);
    }

    // Load my referral code
    async loadMyReferralCode() {
        try {
            const token = localStorage.getItem('sapyyn_token') || sessionStorage.getItem('sapyyn_token');
            const response = await fetch('/api/referral-codes/my-code', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                document.getElementById('myReferralCode').textContent = data.code;
                document.getElementById('codeUsageCount').textContent = data.usageCount;
            } else {
                // No code exists, show generation option
                document.getElementById('myReferralCode').textContent = 'Generate';
                document.getElementById('myReferralCode').style.cursor = 'pointer';
                document.getElementById('myReferralCode').onclick = () => this.generateReferralCode();
            }
        } catch (error) {
            console.error('Error loading referral code:', error);
        }
    }

    // Generate referral code
    async generateReferralCode() {
        try {
            const token = localStorage.getItem('sapyyn_token') || sessionStorage.getItem('sapyyn_token');
            const response = await fetch('/api/referral-codes/generate', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                document.getElementById('myReferralCode').textContent = data.code;
                document.getElementById('myReferralCode').onclick = null;
                document.getElementById('myReferralCode').style.cursor = 'default';
                this.showToast('success', 'Referral code generated successfully!');
            } else {
                const error = await response.json();
                this.showToast('error', error.error || 'Failed to generate referral code');
            }
        } catch (error) {
            console.error('Error generating referral code:', error);
            this.showToast('error', 'Failed to generate referral code');
        }
    }

    // Copy referral code to clipboard
    async copyReferralCodeToClipboard() {
        const code = document.getElementById('myReferralCode').textContent;
        if (code && code !== 'Generate' && code !== '------') {
            try {
                await navigator.clipboard.writeText(code);
                this.showToast('success', 'Referral code copied to clipboard!');
            } catch (error) {
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = code;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                this.showToast('success', 'Referral code copied to clipboard!');
            }
        }
    }

    // Load notifications
    async loadNotifications() {
        try {
            const token = localStorage.getItem('sapyyn_token') || sessionStorage.getItem('sapyyn_token');
            const response = await fetch('/api/dashboard/notifications', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const notifications = await response.json();
                this.displayNotifications(notifications);
            }
        } catch (error) {
            console.error('Error loading notifications:', error);
        }
    }

    // Display notifications
    displayNotifications(notifications) {
        const badge = document.getElementById('notificationBadge');
        const list = document.getElementById('notificationList');

        if (badge) {
            badge.textContent = notifications.filter(n => !n.read).length;
        }

        if (list) {
            list.innerHTML = '';
            
            if (notifications.length === 0) {
                list.innerHTML = '<div class="dropdown-item text-muted">No new notifications</div>';
                return;
            }

            notifications.slice(0, 5).forEach(notification => {
                const item = document.createElement('div');
                item.className = `dropdown-item ${notification.read ? '' : 'bg-light'}`;
                item.innerHTML = `
                    <div class="d-flex">
                        <div class="flex-grow-1">
                            <h6 class="mb-1">${notification.title}</h6>
                            <p class="mb-1 small text-muted">${notification.message}</p>
                            <small class="text-muted">${this.formatRelativeTime(notification.createdAt)}</small>
                        </div>
                        ${!notification.read ? '<div class="ms-2"><span class="badge bg-primary">New</span></div>' : ''}
                    </div>
                `;
                list.appendChild(item);
            });

            if (notifications.length > 5) {
                const moreItem = document.createElement('div');
                moreItem.className = 'dropdown-item text-center';
                moreItem.innerHTML = '<a href="/notifications" class="text-decoration-none">View all notifications</a>';
                list.appendChild(moreItem);
            }
        }
    }

    // Format relative time
    formatRelativeTime(dateString) {
        const date = new Date(dateString);
        const now = new Date();
        const diffMs = now - date;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMins / 60);
        const diffDays = Math.floor(diffHours / 24);

        if (diffMins < 1) return 'Just now';
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    }

    // Update date display
    updateDateDisplay() {
        const now = new Date();
        const options = { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        };
        document.getElementById('currentDate').textContent = now.toLocaleDateString('en-US', options);
    }

    // Initialize charts
    initializeCharts() {
        this.initReferralsChart();
        this.initTypesChart();
    }

    // Initialize referrals over time chart
    initReferralsChart() {
        const ctx = document.getElementById('referralsChart');
        if (!ctx) return;

        this.charts.referrals = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Referrals',
                    data: [],
                    borderColor: '#007bff',
                    backgroundColor: 'rgba(0, 123, 255, 0.1)',
                    tension: 0.4,
                    fill: true
                }, {
                    label: 'Completed',
                    data: [],
                    borderColor: '#28a745',
                    backgroundColor: 'rgba(40, 167, 69, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }

    // Initialize referral types chart
    initTypesChart() {
        const ctx = document.getElementById('typesChart');
        if (!ctx) return;

        this.charts.types = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [],
                datasets: [{
                    data: [],
                    backgroundColor: [
                        '#007bff',
                        '#28a745',
                        '#ffc107',
                        '#dc3545',
                        '#6f42c1',
                        '#fd7e14'
                    ]
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                }
            }
        });
    }

    // Load charts data
    async loadChartsData() {
        try {
            const token = localStorage.getItem('sapyyn_token') || sessionStorage.getItem('sapyyn_token');
            
            // Load referrals over time
            const timeResponse = await fetch('/api/dashboard/charts/referrals-time', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (timeResponse.ok) {
                const timeData = await timeResponse.json();
                this.updateReferralsChart(timeData);
            }

            // Load referral types
            const typesResponse = await fetch('/api/dashboard/charts/referral-types', {
                headers: { 'Authorization': `Bearer ${token}` }
            });
            
            if (typesResponse.ok) {
                const typesData = await typesResponse.json();
                this.updateTypesChart(typesData);
            }
        } catch (error) {
            console.error('Error loading charts data:', error);
        }
    }

    // Update referrals chart
    updateReferralsChart(data) {
        if (!this.charts.referrals) return;

        this.charts.referrals.data.labels = data.labels;
        this.charts.referrals.data.datasets[0].data = data.referrals;
        this.charts.referrals.data.datasets[1].data = data.completed;
        this.charts.referrals.update();
    }

    // Update types chart
    updateTypesChart(data) {
        if (!this.charts.types) return;

        this.charts.types.data.labels = data.labels;
        this.charts.types.data.datasets[0].data = data.values;
        this.charts.types.update();
    }

    // Load recent activity
    async loadRecentActivity() {
        try {
            const token = localStorage.getItem('sapyyn_token') || sessionStorage.getItem('sapyyn_token');
            const response = await fetch('/api/dashboard/recent-activity', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const activities = await response.json();
                this.displayRecentActivity(activities);
            }
        } catch (error) {
            console.error('Error loading recent activity:', error);
        }
    }

    // Display recent activity
    displayRecentActivity(activities) {
        const container = document.getElementById('recentActivity');
        if (!container) return;

        container.innerHTML = '';

        if (activities.length === 0) {
            container.innerHTML = '<p class="text-muted">No recent activity</p>';
            return;
        }

        activities.forEach(activity => {
            const item = document.createElement('div');
            item.className = 'activity-item d-flex align-items-center p-3 border-bottom';
            
            const icon = this.getActivityIcon(activity.type);
            const color = this.getActivityColor(activity.type);
            
            item.innerHTML = `
                <div class="activity-icon me-3">
                    <i class="fas ${icon} text-${color}"></i>
                </div>
                <div class="flex-grow-1">
                    <h6 class="mb-1">${activity.title}</h6>
                    <p class="mb-0 text-muted small">${activity.description}</p>
                    <small class="text-muted">${this.formatRelativeTime(activity.timestamp)}</small>
                </div>
                ${activity.points ? `<div class="activity-points"><span class="badge bg-success">+${activity.points}</span></div>` : ''}
            `;
            
            container.appendChild(item);
        });
    }

    // Get activity icon
    getActivityIcon(type) {
        const icons = {
            referral: 'fa-user-md',
            completion: 'fa-check-circle',
            reward: 'fa-gift',
            learning: 'fa-graduation-cap',
            rating: 'fa-star'
        };
        return icons[type] || 'fa-info-circle';
    }

    // Get activity color
    getActivityColor(type) {
        const colors = {
            referral: 'primary',
            completion: 'success',
            reward: 'warning',
            learning: 'info',
            rating: 'warning'
        };
        return colors[type] || 'secondary';
    }

    // Load monthly goals
    async loadMonthlyGoals() {
        try {
            const token = localStorage.getItem('sapyyn_token') || sessionStorage.getItem('sapyyn_token');
            const response = await fetch('/api/dashboard/monthly-goals', {
                headers: { 'Authorization': `Bearer ${token}` }
            });

            if (response.ok) {
                const goals = await response.json();
                this.displayMonthlyGoals(goals);
            }
        } catch (error) {
            console.error('Error loading monthly goals:', error);
        }
    }

    // Display monthly goals
    displayMonthlyGoals(goals) {
        const container = document.getElementById('monthlyGoals');
        if (!container) return;

        container.innerHTML = '';

        goals.forEach(goal => {
            const progress = Math.min((goal.current / goal.target) * 100, 100);
            
            const goalItem = document.createElement('div');
            goalItem.className = 'goal-item mb-3';
            
            goalItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6 class="mb-0">${goal.title}</h6>
                    <span class="badge bg-primary">${goal.current}/${goal.target}</span>
                </div>
                <div class="progress mb-1" style="height: 8px;">
                    <div class="progress-bar bg-success" style="width: ${progress}%"></div>
                </div>
                <small class="text-muted">${Math.round(progress)}% complete - ${goal.reward} points reward</small>
            `;
            
            container.appendChild(goalItem);
        });
    }

    // Switch section
    switchSection(sectionName) {
        // Update navigation
        document.querySelectorAll('.nav-link').forEach(link => {
            link.classList.remove('active');
        });
        document.querySelector(`[data-section="${sectionName}"]`).classList.add('active');

        // Show/hide sections
        document.querySelectorAll('.content-section').forEach(section => {
            section.style.display = 'none';
        });
        document.getElementById(`${sectionName}-section`).style.display = 'block';

        this.currentSection = sectionName;

        // Load section-specific data
        this.loadSectionData(sectionName);
    }

    // Load section-specific data
    loadSectionData(sectionName) {
        switch (sectionName) {
            case 'referrals':
                this.loadReferralsSection();
                break;
            case 'analytics':
                this.loadAnalyticsSection();
                break;
            case 'rewards':
                this.loadRewardsSection();
                break;
            case 'learning':
                this.loadLearningSection();
                break;
        }
    }

    // Show quick referral modal
    showQuickReferralModal() {
        const modal = document.getElementById('quickReferralModal');
        if (modal) {
            const bootstrapModal = new bootstrap.Modal(modal);
            bootstrapModal.show();
        }
    }

    // Refresh dashboard data
    async refreshDashboardData() {
        await this.loadDashboardData();
        await this.loadNotifications();
        console.log('Dashboard data refreshed');
    }

    // Show toast notification
    showToast(type, message, duration = 5000) {
        const toast = document.createElement('div');
        toast.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, duration);
    }
}

// Global functions
function showQuickReferral() {
    if (window.enhancedDashboard) {
        window.enhancedDashboard.showQuickReferralModal();
    }
}

function copyReferralCode() {
    if (window.enhancedDashboard) {
        window.enhancedDashboard.copyReferralCodeToClipboard();
    }
}

function logout() {
    localStorage.removeItem('sapyyn_token');
    sessionStorage.removeItem('sapyyn_token');
    localStorage.removeItem('sapyyn_user');
    sessionStorage.removeItem('sapyyn_user');
    window.location.href = '/portal';
}

// Initialize enhanced dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.enhancedDashboard = new EnhancedDashboard();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = EnhancedDashboard;
}