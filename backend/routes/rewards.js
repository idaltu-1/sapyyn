const express = require('express');
const router = express.Router();
const { authenticateToken } = require('../middleware/auth');
const User = require('../models/User');
const Reward = require('../models/Reward');

// Get user reward profile
router.get('/profile', authenticateToken, async (req, res) => {
    try {
        const user = await User.findById(req.user.userId).select('-password');
        
        if (!user) {
            return res.status(404).json({ error: 'User not found' });
        }

        // Calculate additional reward metrics
        const totalRedemptions = await Reward.countDocuments({
            userId: user._id,
            type: 'redeemed'
        });

        const monthlyReferrals = await this.getMonthlyReferrals(user._id);
        const tier = this.getUserTier(user.rewardPoints);

        const rewards = {
            points: user.rewardPoints,
            tier,
            totalRedemptions,
            monthlyReferrals
        };

        res.json({ user, rewards });
    } catch (error) {
        console.error('Get reward profile error:', error);
        res.status(500).json({ error: 'Failed to fetch reward profile' });
    }
});

// Get reward catalog
router.get('/catalog', authenticateToken, async (req, res) => {
    try {
        const { category = 'all' } = req.query;
        
        // Mock reward catalog - in production this would come from database
        let rewards = [
            {
                _id: '1',
                title: '$25 Amazon Gift Card',
                description: 'Redeem for Amazon purchases, books, electronics, and more',
                pointsCost: 500,
                category: 'gift_cards',
                imageUrl: '/images/rewards/amazon-gift-card.jpg',
                stock: 100,
                estimatedDelivery: 'Instant',
                isActive: true
            },
            {
                _id: '2',
                title: '$50 Restaurant Voucher',
                description: 'Enjoy dining at popular local restaurants',
                pointsCost: 1000,
                category: 'experiences',
                imageUrl: '/images/rewards/restaurant-voucher.jpg',
                stock: 50,
                estimatedDelivery: '1-2 business days',
                isActive: true
            },
            {
                _id: '3',
                title: 'Dental Conference Ticket',
                description: 'Annual dental conference with CE credits',
                pointsCost: 2500,
                category: 'professional',
                imageUrl: '/images/rewards/conference-ticket.jpg',
                stock: 20,
                estimatedDelivery: '2 weeks before event',
                isActive: true
            },
            {
                _id: '4',
                title: 'Charity Donation - $100',
                description: 'Donate to children\'s dental health charity',
                pointsCost: 1500,
                category: 'donations',
                imageUrl: '/images/rewards/charity-donation.jpg',
                stock: 999,
                estimatedDelivery: 'Instant',
                isActive: true
            },
            {
                _id: '5',
                title: 'Premium Dental Kit',
                description: 'Professional dental tools and equipment',
                pointsCost: 3000,
                category: 'professional',
                imageUrl: '/images/rewards/dental-kit.jpg',
                stock: 15,
                estimatedDelivery: '3-5 business days',
                isActive: true
            }
        ];

        // Filter by category
        if (category !== 'all') {
            rewards = rewards.filter(reward => reward.category === category);
        }

        // Sort by popularity (mock)
        rewards.sort((a, b) => a.pointsCost - b.pointsCost);

        res.json(rewards);
    } catch (error) {
        console.error('Get reward catalog error:', error);
        res.status(500).json({ error: 'Failed to fetch reward catalog' });
    }
});

// Get specific reward details
router.get('/catalog/:rewardId', authenticateToken, async (req, res) => {
    try {
        const { rewardId } = req.params;
        
        // Mock reward details - in production this would come from database
        const rewards = {
            '1': {
                _id: '1',
                title: '$25 Amazon Gift Card',
                description: 'Redeem for Amazon purchases, books, electronics, and more. Gift card code will be sent to your email instantly.',
                pointsCost: 500,
                category: 'gift_cards',
                imageUrl: '/images/rewards/amazon-gift-card.jpg',
                stock: 100,
                estimatedDelivery: 'Instant',
                terms: 'Valid for 1 year from date of issue. Cannot be exchanged for cash.',
                isActive: true
            }
        };

        const reward = rewards[rewardId];
        if (!reward) {
            return res.status(404).json({ error: 'Reward not found' });
        }

        res.json(reward);
    } catch (error) {
        console.error('Get reward details error:', error);
        res.status(500).json({ error: 'Failed to fetch reward details' });
    }
});

// Redeem reward
router.post('/redeem', authenticateToken, async (req, res) => {
    try {
        const { rewardId } = req.body;
        const userId = req.user.userId;

        const user = await User.findById(userId);
        if (!user) {
            return res.status(404).json({ error: 'User not found' });
        }

        // Mock reward lookup
        const rewardCosts = {
            '1': 500,
            '2': 1000,
            '3': 2500,
            '4': 1500,
            '5': 3000
        };

        const pointsCost = rewardCosts[rewardId];
        if (!pointsCost) {
            return res.status(404).json({ error: 'Reward not found' });
        }

        // Check if user has enough points
        if (user.rewardPoints < pointsCost) {
            return res.status(400).json({ error: 'Insufficient points' });
        }

        // Deduct points
        user.rewardPoints -= pointsCost;
        await user.save();

        // Create reward record
        const reward = new Reward({
            userId: user._id,
            type: 'redeemed',
            points: -pointsCost,
            description: `Redeemed reward: ${rewardId}`,
            metadata: {
                rewardId,
                redemptionDate: new Date()
            }
        });

        await reward.save();

        res.json({
            message: 'Reward redeemed successfully',
            remainingPoints: user.rewardPoints,
            redemptionId: reward._id
        });
    } catch (error) {
        console.error('Redeem reward error:', error);
        res.status(500).json({ error: 'Failed to redeem reward' });
    }
});

// Get daily challenges
router.get('/challenges/daily', authenticateToken, async (req, res) => {
    try {
        const userId = req.user.userId;
        
        // Mock daily challenges
        const challenges = [
            {
                id: 'daily_referral',
                title: 'Submit a Referral',
                target: 1,
                currentProgress: 0,
                unit: 'referral',
                reward: 25,
                isCompleted: false
            },
            {
                id: 'daily_learning',
                title: 'Watch 30 Minutes of Content',
                target: 30,
                currentProgress: 15,
                unit: 'minutes',
                reward: 50,
                isCompleted: false
            },
            {
                id: 'daily_login',
                title: 'Daily Login Streak',
                target: 1,
                currentProgress: 1,
                unit: 'day',
                reward: 10,
                isCompleted: true
            }
        ];

        res.json(challenges);
    } catch (error) {
        console.error('Get daily challenges error:', error);
        res.status(500).json({ error: 'Failed to fetch daily challenges' });
    }
});

// Get monthly goals
router.get('/goals/monthly', authenticateToken, async (req, res) => {
    try {
        const userId = req.user.userId;
        
        // Mock monthly goals
        const goals = [
            {
                id: 'monthly_referrals',
                title: 'Submit 10 Referrals',
                target: 10,
                currentProgress: 3,
                reward: 500,
                isCompleted: false
            },
            {
                id: 'monthly_completion',
                title: 'Complete 2 Courses',
                target: 2,
                currentProgress: 1,
                reward: 1000,
                isCompleted: false
            },
            {
                id: 'monthly_rating',
                title: 'Maintain 4.5+ Rating',
                target: 4.5,
                currentProgress: 4.7,
                reward: 750,
                isCompleted: true
            }
        ];

        res.json(goals);
    } catch (error) {
        console.error('Get monthly goals error:', error);
        res.status(500).json({ error: 'Failed to fetch monthly goals' });
    }
});

// Get leaderboard
router.get('/leaderboard', authenticateToken, async (req, res) => {
    try {
        const currentUserId = req.user.userId;
        
        // Get top performers
        const topUsers = await User.find({ isActive: true })
            .select('firstName lastName role rewardPoints')
            .sort({ rewardPoints: -1 })
            .limit(10);

        const leaderboard = topUsers.map(user => ({
            id: user._id,
            name: `${user.firstName} ${user.lastName}`,
            role: user.role,
            points: user.rewardPoints
        }));

        // Get current user's rank
        const currentUser = await User.findById(currentUserId);
        const higherRankedCount = await User.countDocuments({
            rewardPoints: { $gt: currentUser.rewardPoints },
            isActive: true
        });

        const userRank = {
            rank: higherRankedCount + 1,
            points: currentUser.rewardPoints,
            currentRankPoints: 0, // Would calculate based on tier system
            nextRankPoints: this.getNextTierPoints(currentUser.rewardPoints)
        };

        res.json({ leaderboard, userRank });
    } catch (error) {
        console.error('Get leaderboard error:', error);
        res.status(500).json({ error: 'Failed to fetch leaderboard' });
    }
});

// Get reward history
router.get('/history', authenticateToken, async (req, res) => {
    try {
        const userId = req.user.userId;
        const { filter = 'all' } = req.query;
        
        let query = { userId };
        
        if (filter === 'earned') {
            query.type = 'earned';
        } else if (filter === 'redeemed') {
            query.type = 'redeemed';
        }

        const history = await Reward.find(query)
            .sort({ createdAt: -1 })
            .limit(50);

        const formattedHistory = history.map(reward => ({
            date: reward.createdAt,
            type: reward.type,
            description: reward.description,
            points: Math.abs(reward.points),
            status: 'completed' // In production, this might vary
        }));

        res.json(formattedHistory);
    } catch (error) {
        console.error('Get reward history error:', error);
        res.status(500).json({ error: 'Failed to fetch reward history' });
    }
});

// Helper functions
function getUserTier(points) {
    if (points >= 5000) return 'diamond';
    if (points >= 3000) return 'platinum';
    if (points >= 1500) return 'gold';
    if (points >= 500) return 'silver';
    return 'bronze';
}

function getNextTierPoints(currentPoints) {
    if (currentPoints < 500) return 500;
    if (currentPoints < 1500) return 1500;
    if (currentPoints < 3000) return 3000;
    if (currentPoints < 5000) return 5000;
    return null; // Max tier
}

async function getMonthlyReferrals(userId) {
    const now = new Date();
    const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
    
    const Referral = require('../models/Referral');
    
    return await Referral.countDocuments({
        referringDentistId: userId,
        createdAt: { $gte: startOfMonth }
    });
}

module.exports = router;