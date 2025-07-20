// Enhanced Reward Center JavaScript
class RewardCenter {
    constructor() {
        this.currentUser = null;
        this.rewardData = {
            points: 0,
            tier: 'bronze',
            rank: 0,
            completedCourses: 0,
            totalReferrals: 0
        };
        this.selectedCategory = 'all';
        this.init();
    }

    async init() {
        await this.loadUserData();
        this.setupEventListeners();
        this.loadRewardCatalog();
        this.loadDailyChallenges();
        this.loadMonthlyGoals();
        this.loadLeaderboard();
        this.loadRewardHistory();
        this.updateProgressDisplay();
    }

    // Load user data and reward information
    async loadUserData() {
        try {
            const token = localStorage.getItem('sapyyn_token') || sessionStorage.getItem('sapyyn_token');
            const response = await fetch('/api/rewards/profile', {
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });

            if (response.ok) {
                const data = await response.json();
                this.currentUser = data.user;
                this.rewardData = { ...this.rewardData, ...data.rewards };
                this.updateUIWithUserData();
            }
        } catch (error) {
            console.error('Error loading user data:', error);
            this.showToast('error', 'Failed to load reward data');
        }
    }

    // Setup event listeners
    setupEventListeners() {
        // Category filter buttons
        document.querySelectorAll('.reward-categories .btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                this.filterRewards(btn.dataset.category);
            });
        });

        // History filter
        const historyFilter = document.getElementById('historyFilter');
        if (historyFilter) {
            historyFilter.addEventListener('change', () => {
                this.loadRewardHistory();
            });
        }

        // Redeem confirmation
        const confirmRedeemBtn = document.getElementById('confirmRedeem');
        if (confirmRedeemBtn) {
            confirmRedeemBtn.addEventListener('click', () => {
                this.confirmRedemption();
            });
        }
    }

    // Update UI with user data
    updateUIWithUserData() {
        // Update points display
        document.getElementById('currentPoints').textContent = this.rewardData.points.toLocaleString();
        document.getElementById('totalPoints').textContent = this.rewardData.points.toLocaleString();
        
        // Update tier
        document.getElementById('tierLevel').textContent = this.getTierDisplayName(this.rewardData.tier);
        
        // Update statistics
        document.getElementById('totalRedemptions').textContent = this.rewardData.totalRedemptions || 0;
        document.getElementById('monthlyProgress').textContent = this.calculateMonthlyProgress() + '%';
        
        // Update tier progress
        this.updateTierProgress();
    }

    // Get tier display name
    getTierDisplayName(tier) {
        const tierNames = {
            bronze: 'Bronze',
            silver: 'Silver',
            gold: 'Gold',
            platinum: 'Platinum',
            diamond: 'Diamond'
        };
        return tierNames[tier] || 'Bronze';
    }

    // Calculate monthly progress
    calculateMonthlyProgress() {
        const monthlyGoal = this.getMonthlyGoal();
        const currentProgress = this.rewardData.monthlyReferrals || 0;
        return Math.min(Math.round((currentProgress / monthlyGoal) * 100), 100);
    }

    // Get monthly goal based on tier
    getMonthlyGoal() {
        const goals = {
            bronze: 10,
            silver: 20,
            gold: 35,
            platinum: 50,
            diamond: 75
        };
        return goals[this.rewardData.tier] || 10;
    }

    // Update tier progress display
    updateTierProgress() {
        const tiers = ['bronze', 'silver', 'gold', 'platinum', 'diamond'];
        const currentTierIndex = tiers.indexOf(this.rewardData.tier);
        const nextTier = tiers[currentTierIndex + 1];
        
        // Update tier items
        document.querySelectorAll('.tier-item').forEach((item, index) => {
            const tierName = item.dataset.tier;
            if (index <= currentTierIndex) {
                item.classList.add('active');
            } else {
                item.classList.remove('active');
            }
        });

        // Update progress bar
        const progressPercentage = this.calculateTierProgress();
        document.getElementById('tierProgressBar').style.width = progressPercentage + '%';
        
        // Update progress text
        const progressText = document.getElementById('progressText');
        if (nextTier) {
            const pointsNeeded = this.getPointsForNextTier() - this.rewardData.points;
            progressText.textContent = `${pointsNeeded} more points to reach ${this.getTierDisplayName(nextTier)}`;
        } else {
            progressText.textContent = 'You\'ve reached the highest tier!';
        }
    }

    // Calculate tier progress percentage
    calculateTierProgress() {
        const tierThresholds = {
            bronze: 0,
            silver: 500,
            gold: 1500,
            platinum: 3000,
            diamond: 5000
        };
        
        const currentTierPoints = tierThresholds[this.rewardData.tier];
        const nextTierPoints = this.getPointsForNextTier();
        
        if (nextTierPoints === currentTierPoints) return 100;
        
        const progress = ((this.rewardData.points - currentTierPoints) / (nextTierPoints - currentTierPoints)) * 100;
        return Math.min(progress, 100);
    }

    // Get points needed for next tier
    getPointsForNextTier() {
        const tierThresholds = {
            bronze: 500,
            silver: 1500,
            gold: 3000,
            platinum: 5000,
            diamond: 5000 // Max tier
        };
        return tierThresholds[this.rewardData.tier] || 5000;
    }

    // Load reward catalog
    async loadRewardCatalog() {
        try {
            const response = await fetch(`/api/rewards/catalog?category=${this.selectedCategory}`);
            if (response.ok) {
                const rewards = await response.json();
                this.displayRewardCatalog(rewards);
            }
        } catch (error) {
            console.error('Error loading reward catalog:', error);
        }
    }

    // Display reward catalog
    displayRewardCatalog(rewards) {
        const catalogContainer = document.getElementById('rewardCatalog');
        if (!catalogContainer) return;

        catalogContainer.innerHTML = '';

        rewards.forEach(reward => {
            const rewardCard = this.createRewardCard(reward);
            catalogContainer.appendChild(rewardCard);
        });
    }

    // Create reward card element
    createRewardCard(reward) {
        const card = document.createElement('div');
        card.className = 'col-lg-4 col-md-6 mb-4';
        
        const canAfford = this.rewardData.points >= reward.pointsCost;
        const isAvailable = reward.stock > 0;
        
        card.innerHTML = `
            <div class="card reward-card h-100">
                <div class="position-relative">
                    <img src="${reward.imageUrl || '/images/default-reward.jpg'}" class="reward-image" alt="${reward.title}">
                    <div class="reward-cost">
                        <i class="fas fa-coins me-1"></i>${reward.pointsCost.toLocaleString()}
                    </div>
                    <div class="reward-category-badge">${reward.category}</div>
                </div>
                <div class="card-body d-flex flex-column">
                    <h6 class="card-title">${reward.title}</h6>
                    <p class="card-text text-muted flex-grow-1">${reward.description}</p>
                    <div class="mt-auto">
                        ${isAvailable ? `
                            <button 
                                class="btn ${canAfford ? 'btn-primary' : 'btn-outline-secondary'} w-100"
                                ${canAfford ? '' : 'disabled'}
                                onclick="rewardCenter.showRedeemModal('${reward._id}')"
                            >
                                ${canAfford ? 'Redeem Now' : 'Insufficient Points'}
                            </button>
                        ` : `
                            <button class="btn btn-outline-danger w-100" disabled>
                                Out of Stock
                            </button>
                        `}
                        <small class="text-muted d-block mt-2">
                            ${reward.estimatedDelivery || 'Instant delivery'}
                        </small>
                    </div>
                </div>
            </div>
        `;
        
        return card;
    }

    // Filter rewards by category
    filterRewards(category) {
        this.selectedCategory = category;
        
        // Update active button
        document.querySelectorAll('.reward-categories .btn').forEach(btn => {
            btn.classList.remove('active');
        });
        document.querySelector(`[data-category="${category}"]`).classList.add('active');
        
        // Reload catalog
        this.loadRewardCatalog();
    }

    // Load daily challenges
    async loadDailyChallenges() {
        try {
            const response = await fetch('/api/rewards/challenges/daily');
            if (response.ok) {
                const challenges = await response.json();
                this.displayDailyChallenges(challenges);
            }
        } catch (error) {
            console.error('Error loading daily challenges:', error);
        }
    }

    // Display daily challenges
    displayDailyChallenges(challenges) {
        const container = document.getElementById('dailyChallenges');
        if (!container) return;

        container.innerHTML = '';

        challenges.forEach(challenge => {
            const challengeItem = document.createElement('div');
            challengeItem.className = 'challenge-item';
            
            const progress = Math.min((challenge.currentProgress / challenge.target) * 100, 100);
            const isCompleted = challenge.isCompleted;
            
            challengeItem.innerHTML = `
                <div class="d-flex align-items-center justify-content-between">
                    <div class="flex-grow-1">
                        <h6 class="mb-1 ${isCompleted ? 'text-success' : ''}">${challenge.title}</h6>
                        <div class="progress mb-1" style="height: 4px;">
                            <div class="progress-bar ${isCompleted ? 'bg-success' : 'bg-primary'}" 
                                 style="width: ${progress}%"></div>
                        </div>
                        <small class="challenge-progress">
                            ${challenge.currentProgress}/${challenge.target} ${challenge.unit}
                        </small>
                    </div>
                    <div class="ms-3">
                        ${isCompleted ? 
                            '<i class="fas fa-check-circle text-success fa-lg"></i>' : 
                            `<span class="challenge-reward">+${challenge.reward}</span>`
                        }
                    </div>
                </div>
            `;
            
            container.appendChild(challengeItem);
        });
    }

    // Load monthly goals
    async loadMonthlyGoals() {
        try {
            const response = await fetch('/api/rewards/goals/monthly');
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
            const goalItem = document.createElement('div');
            goalItem.className = 'mb-3';
            
            const progress = Math.min((goal.currentProgress / goal.target) * 100, 100);
            const isCompleted = goal.isCompleted;
            
            goalItem.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-2">
                    <h6 class="mb-0 ${isCompleted ? 'text-success' : ''}">${goal.title}</h6>
                    <span class="badge ${isCompleted ? 'bg-success' : 'bg-primary'}">
                        +${goal.reward} pts
                    </span>
                </div>
                <div class="progress mb-1" style="height: 6px;">
                    <div class="progress-bar ${isCompleted ? 'bg-success' : 'bg-primary'}" 
                         style="width: ${progress}%"></div>
                </div>
                <small class="text-muted">
                    ${goal.currentProgress}/${goal.target} - ${Math.round(progress)}% complete
                </small>
            `;
            
            container.appendChild(goalItem);
        });
    }

    // Load leaderboard
    async loadLeaderboard() {
        try {
            const response = await fetch('/api/rewards/leaderboard');
            if (response.ok) {
                const data = await response.json();
                this.displayLeaderboard(data.leaderboard);
                this.updateUserRanking(data.userRank);
            }
        } catch (error) {
            console.error('Error loading leaderboard:', error);
        }
    }

    // Display leaderboard
    displayLeaderboard(leaderboard) {
        const container = document.getElementById('leaderboardList');
        if (!container) return;

        container.innerHTML = '';

        leaderboard.forEach((user, index) => {
            const item = document.createElement('div');
            item.className = 'leaderboard-item';
            
            const rankClass = index < 3 ? `top-${index + 1}` : 'other';
            
            item.innerHTML = `
                <div class="leaderboard-rank ${rankClass}">
                    ${index + 1}
                </div>
                <div class="leaderboard-user">
                    <h6 class="mb-0">${user.name}</h6>
                    <small class="text-muted">${user.role}</small>
                </div>
                <div class="leaderboard-points">
                    ${user.points.toLocaleString()}
                </div>
            `;
            
            container.appendChild(item);
        });
    }

    // Update user ranking display
    updateUserRanking(rankData) {
        if (!rankData) return;

        document.getElementById('userRank').textContent = `#${rankData.rank}`;
        
        const progressBar = document.getElementById('rankProgress');
        const progressText = document.getElementById('rankProgressText');
        
        if (rankData.nextRankPoints) {
            const progress = ((rankData.points - rankData.currentRankPoints) / 
                            (rankData.nextRankPoints - rankData.currentRankPoints)) * 100;
            progressBar.style.width = Math.min(progress, 100) + '%';
            
            const pointsNeeded = rankData.nextRankPoints - rankData.points;
            progressText.textContent = `${pointsNeeded} points to next rank`;
        } else {
            progressBar.style.width = '100%';
            progressText.textContent = 'Top performer!';
        }
    }

    // Load reward history
    async loadRewardHistory() {
        try {
            const filter = document.getElementById('historyFilter')?.value || 'all';
            const response = await fetch(`/api/rewards/history?filter=${filter}`);
            
            if (response.ok) {
                const history = await response.json();
                this.displayRewardHistory(history);
            }
        } catch (error) {
            console.error('Error loading reward history:', error);
        }
    }

    // Display reward history
    displayRewardHistory(history) {
        const tbody = document.querySelector('#historyTable tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        history.forEach(transaction => {
            const row = document.createElement('tr');
            
            const typeIcon = transaction.type === 'earned' ? 
                '<i class="fas fa-plus-circle text-success"></i>' : 
                '<i class="fas fa-minus-circle text-danger"></i>';
            
            const statusBadge = transaction.status === 'completed' ?
                '<span class="badge bg-success">Completed</span>' :
                transaction.status === 'pending' ?
                '<span class="badge bg-warning">Pending</span>' :
                '<span class="badge bg-danger">Failed</span>';
            
            row.innerHTML = `
                <td>${new Date(transaction.date).toLocaleDateString()}</td>
                <td>${typeIcon} ${transaction.type}</td>
                <td>${transaction.description}</td>
                <td class="${transaction.type === 'earned' ? 'text-success' : 'text-danger'}">
                    ${transaction.type === 'earned' ? '+' : '-'}${transaction.points}
                </td>
                <td>${statusBadge}</td>
            `;
            
            tbody.appendChild(row);
        });
    }

    // Show redeem modal
    async showRedeemModal(rewardId) {
        try {
            const response = await fetch(`/api/rewards/catalog/${rewardId}`);
            if (response.ok) {
                const reward = await response.json();
                this.displayRedeemModal(reward);
            }
        } catch (error) {
            console.error('Error loading reward details:', error);
            this.showToast('error', 'Failed to load reward details');
        }
    }

    // Display redeem modal
    displayRedeemModal(reward) {
        const modal = document.getElementById('redeemModal');
        if (!modal) return;

        // Update modal content
        document.getElementById('rewardImage').src = reward.imageUrl || '/images/default-reward.jpg';
        document.getElementById('rewardTitle').textContent = reward.title;
        document.getElementById('rewardDescription').textContent = reward.description;
        document.getElementById('rewardCost').textContent = `${reward.pointsCost.toLocaleString()} points`;

        // Store reward ID for confirmation
        this.pendingRedemption = reward;

        // Show modal
        const bootstrapModal = new bootstrap.Modal(modal);
        bootstrapModal.show();
    }

    // Confirm redemption
    async confirmRedemption() {
        if (!this.pendingRedemption) return;

        try {
            const response = await fetch('/api/rewards/redeem', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('sapyyn_token') || sessionStorage.getItem('sapyyn_token')}`
                },
                body: JSON.stringify({
                    rewardId: this.pendingRedemption._id
                })
            });

            if (response.ok) {
                const result = await response.json();
                this.showToast('success', 'Reward redeemed successfully!');
                
                // Update points
                this.rewardData.points -= this.pendingRedemption.pointsCost;
                this.updateUIWithUserData();
                
                // Refresh displays
                this.loadRewardCatalog();
                this.loadRewardHistory();
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('redeemModal'));
                modal.hide();
                
                // Trigger celebration animation
                this.triggerCelebration();
                
            } else {
                const error = await response.json();
                this.showToast('error', error.message || 'Redemption failed');
            }
        } catch (error) {
            console.error('Error redeeming reward:', error);
            this.showToast('error', 'Failed to redeem reward');
        }
    }

    // Trigger celebration animation
    triggerCelebration() {
        // Add points animation
        const pointsDisplay = document.getElementById('totalPoints');
        pointsDisplay.classList.add('points-animation');
        
        setTimeout(() => {
            pointsDisplay.classList.remove('points-animation');
        }, 600);

        // Show confetti or other celebration effects
        this.showConfetti();
    }

    // Show confetti effect
    showConfetti() {
        // Simple confetti implementation
        const colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4', '#feca57'];
        
        for (let i = 0; i < 50; i++) {
            const confetti = document.createElement('div');
            confetti.style.position = 'fixed';
            confetti.style.left = Math.random() * 100 + 'vw';
            confetti.style.top = '-10px';
            confetti.style.width = '10px';
            confetti.style.height = '10px';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.pointerEvents = 'none';
            confetti.style.zIndex = '9999';
            confetti.style.transform = 'rotate(' + Math.random() * 360 + 'deg)';
            
            document.body.appendChild(confetti);
            
            // Animate confetti falling
            confetti.animate([
                { transform: 'translateY(0) rotate(0deg)', opacity: 1 },
                { transform: 'translateY(100vh) rotate(360deg)', opacity: 0 }
            ], {
                duration: 3000 + Math.random() * 2000,
                easing: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)'
            }).addEventListener('finish', () => {
                confetti.remove();
            });
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

    // Update progress display
    updateProgressDisplay() {
        // This method updates various progress indicators
        this.updateTierProgress();
        
        // Update other progress elements as needed
        const monthlyProgress = this.calculateMonthlyProgress();
        document.getElementById('monthlyProgress').textContent = monthlyProgress + '%';
    }
}

// Initialize reward center when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.rewardCenter = new RewardCenter();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = RewardCenter;
}