const express = require('express');
const router = express.Router();
const { authenticateToken } = require('../middleware/auth');
const User = require('../models/User');
const Referral = require('../models/Referral');
const ReferralCode = require('../models/ReferralCode');
const UserProgress = require('../models/UserProgress');
const Reward = require('../models/Reward');

// Get user profile for dashboard
router.get('/profile', authenticateToken, async (req, res) => {
    try {
        const user = await User.findById(req.user.userId)
            .select('-password')
            .populate('practiceId', 'name type address phone');
        
        if (!user) {
            return res.status(404).json({ error: 'User not found' });
        }

        res.json({ user });
    } catch (error) {
        console.error('Get profile error:', error);
        res.status(500).json({ error: 'Failed to fetch profile' });
    }
});

// Get dashboard statistics
router.get('/stats', authenticateToken, async (req, res) => {
    try {
        const userId = req.user.userId;
        const user = await User.findById(userId);
        
        // Calculate date ranges
        const now = new Date();
        const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
        const startOfLastMonth = new Date(now.getFullYear(), now.getMonth() - 1, 1);
        const endOfLastMonth = new Date(now.getFullYear(), now.getMonth(), 0);

        // Get referral statistics
        const totalReferrals = await Referral.countDocuments({ 
            $or: [
                { referringDentistId: userId },
                { specialistId: userId }
            ]
        });

        const completedReferrals = await Referral.countDocuments({ 
            $or: [
                { referringDentistId: userId },
                { specialistId: userId }
            ],
            status: 'completed'
        });

        const monthlyReferrals = await Referral.countDocuments({
            $or: [
                { referringDentistId: userId },
                { specialistId: userId }
            ],
            createdAt: { $gte: startOfMonth }
        });

        const lastMonthReferrals = await Referral.countDocuments({
            $or: [
                { referringDentistId: userId },
                { specialistId: userId }
            ],
            createdAt: { $gte: startOfLastMonth, $lte: endOfLastMonth }
        });

        const lastMonthCompleted = await Referral.countDocuments({
            $or: [
                { referringDentistId: userId },
                { specialistId: userId }
            ],
            status: 'completed',
            updatedAt: { $gte: startOfLastMonth, $lte: endOfLastMonth }
        });

        // Calculate average rating
        const ratingAggregation = await Referral.aggregate([
            {
                $match: {
                    $or: [
                        { referringDentistId: userId },
                        { specialistId: userId }
                    ],
                    rating: { $exists: true, $gte: 1 }
                }
            },
            {
                $group: {
                    _id: null,
                    averageRating: { $avg: '$rating' }
                }
            }
        ]);

        const averageRating = ratingAggregation.length > 0 ? ratingAggregation[0].averageRating : 0;

        // Get learning progress
        const completedCourses = await UserProgress.countDocuments({
            userId: userId,
            status: 'completed'
        });

        // Calculate points earned this month
        const monthlyRewards = await Reward.aggregate([
            {
                $match: {
                    userId: userId,
                    createdAt: { $gte: startOfMonth },
                    type: 'earned'
                }
            },
            {
                $group: {
                    _id: null,
                    totalPoints: { $sum: '$points' }
                }
            }
        ]);

        const pointsEarnedThisMonth = monthlyRewards.length > 0 ? monthlyRewards[0].totalPoints : 0;

        // Get user ranking (simplified)
        const userRank = await User.countDocuments({
            rewardPoints: { $gt: user.rewardPoints },
            role: user.role
        }) + 1;

        const stats = {
            totalReferrals,
            completedReferrals,
            totalPoints: user.rewardPoints,
            averageRating: Math.round(averageRating * 10) / 10,
            monthlyReferrals,
            lastMonthReferrals,
            lastMonthCompleted,
            pointsEarnedThisMonth,
            completedCourses,
            rank: userRank
        };

        res.json(stats);
    } catch (error) {
        console.error('Get dashboard stats error:', error);
        res.status(500).json({ error: 'Failed to fetch dashboard statistics' });
    }
});

// Get notifications
router.get('/notifications', authenticateToken, async (req, res) => {
    try {
        const userId = req.user.userId;
        
        // Mock notifications for now - implement proper notification system later
        const notifications = [
            {
                id: 1,
                title: 'New Referral Received',
                message: 'You have received a new referral from Dr. Smith',
                type: 'referral',
                read: false,
                createdAt: new Date(Date.now() - 2 * 60 * 60 * 1000) // 2 hours ago
            },
            {
                id: 2,
                title: 'Course Completed',
                message: 'Congratulations! You completed "Advanced Dental Procedures"',
                type: 'learning',
                read: false,
                createdAt: new Date(Date.now() - 1 * 24 * 60 * 60 * 1000) // 1 day ago
            },
            {
                id: 3,
                title: 'Reward Earned',
                message: 'You earned 50 points for completing a referral',
                type: 'reward',
                read: true,
                createdAt: new Date(Date.now() - 2 * 24 * 60 * 60 * 1000) // 2 days ago
            }
        ];

        res.json(notifications);
    } catch (error) {
        console.error('Get notifications error:', error);
        res.status(500).json({ error: 'Failed to fetch notifications' });
    }
});

// Get referrals over time chart data
router.get('/charts/referrals-time', authenticateToken, async (req, res) => {
    try {
        const userId = req.user.userId;
        
        // Get last 12 months of data
        const months = [];
        const referralsData = [];
        const completedData = [];
        
        for (let i = 11; i >= 0; i--) {
            const date = new Date();
            date.setMonth(date.getMonth() - i);
            const startOfMonth = new Date(date.getFullYear(), date.getMonth(), 1);
            const endOfMonth = new Date(date.getFullYear(), date.getMonth() + 1, 0);
            
            months.push(date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' }));
            
            const monthlyReferrals = await Referral.countDocuments({
                $or: [
                    { referringDentistId: userId },
                    { specialistId: userId }
                ],
                createdAt: { $gte: startOfMonth, $lte: endOfMonth }
            });
            
            const monthlyCompleted = await Referral.countDocuments({
                $or: [
                    { referringDentistId: userId },
                    { specialistId: userId }
                ],
                status: 'completed',
                updatedAt: { $gte: startOfMonth, $lte: endOfMonth }
            });
            
            referralsData.push(monthlyReferrals);
            completedData.push(monthlyCompleted);
        }
        
        res.json({
            labels: months,
            referrals: referralsData,
            completed: completedData
        });
    } catch (error) {
        console.error('Get referrals time chart error:', error);
        res.status(500).json({ error: 'Failed to fetch chart data' });
    }
});

// Get referral types chart data
router.get('/charts/referral-types', authenticateToken, async (req, res) => {
    try {
        const userId = req.user.userId;
        
        const typeAggregation = await Referral.aggregate([
            {
                $match: {
                    $or: [
                        { referringDentistId: userId },
                        { specialistId: userId }
                    ]
                }
            },
            {
                $group: {
                    _id: '$referralType',
                    count: { $sum: 1 }
                }
            },
            {
                $sort: { count: -1 }
            }
        ]);
        
        const labels = typeAggregation.map(item => item._id || 'Unknown');
        const values = typeAggregation.map(item => item.count);
        
        res.json({ labels, values });
    } catch (error) {
        console.error('Get referral types chart error:', error);
        res.status(500).json({ error: 'Failed to fetch chart data' });
    }
});

// Get recent activity
router.get('/recent-activity', authenticateToken, async (req, res) => {
    try {
        const userId = req.user.userId;
        
        // Get recent referrals
        const recentReferrals = await Referral.find({
            $or: [
                { referringDentistId: userId },
                { specialistId: userId }
            ]
        })
        .sort({ createdAt: -1 })
        .limit(5)
        .populate('patientId', 'firstName lastName')
        .populate('referringDentistId', 'firstName lastName')
        .populate('specialistId', 'firstName lastName');

        // Get recent learning progress
        const recentLearning = await UserProgress.find({ userId })
            .sort({ updatedAt: -1 })
            .limit(3)
            .populate('courseId', 'title pointsValue');

        // Get recent rewards
        const recentRewards = await Reward.find({ 
            userId,
            type: 'earned'
        })
        .sort({ createdAt: -1 })
        .limit(3);

        // Combine and format activities
        const activities = [];

        // Add referral activities
        recentReferrals.forEach(referral => {
            activities.push({
                type: 'referral',
                title: 'New Referral',
                description: `Referral for ${referral.patientId?.firstName || 'Patient'} ${referral.patientId?.lastName || ''}`,
                timestamp: referral.createdAt,
                points: referral.rewardPoints
            });
        });

        // Add learning activities
        recentLearning.forEach(progress => {
            if (progress.status === 'completed') {
                activities.push({
                    type: 'learning',
                    title: 'Course Completed',
                    description: progress.courseId?.title || 'Course',
                    timestamp: progress.completedAt,
                    points: progress.courseId?.pointsValue
                });
            }
        });

        // Add reward activities
        recentRewards.forEach(reward => {
            activities.push({
                type: 'reward',
                title: 'Points Earned',
                description: reward.description,
                timestamp: reward.createdAt,
                points: reward.points
            });
        });

        // Sort by timestamp and limit
        activities.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        const limitedActivities = activities.slice(0, 10);

        res.json(limitedActivities);
    } catch (error) {
        console.error('Get recent activity error:', error);
        res.status(500).json({ error: 'Failed to fetch recent activity' });
    }
});

// Get monthly goals
router.get('/monthly-goals', authenticateToken, async (req, res) => {
    try {
        const userId = req.user.userId;
        const user = await User.findById(userId);
        
        const now = new Date();
        const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1);
        
        // Calculate current month progress
        const monthlyReferrals = await Referral.countDocuments({
            referringDentistId: userId,
            createdAt: { $gte: startOfMonth }
        });

        const monthlyCompleted = await Referral.countDocuments({
            referringDentistId: userId,
            status: 'completed',
            updatedAt: { $gte: startOfMonth }
        });

        const monthlyLearning = await UserProgress.countDocuments({
            userId: userId,
            status: 'completed',
            completedAt: { $gte: startOfMonth }
        });

        // Define goals based on user tier
        const tierGoals = {
            bronze: { referrals: 10, completed: 5, learning: 1 },
            silver: { referrals: 20, completed: 15, learning: 2 },
            gold: { referrals: 35, completed: 25, learning: 3 },
            platinum: { referrals: 50, completed: 40, learning: 4 },
            diamond: { referrals: 75, completed: 60, learning: 5 }
        };

        const userTier = this.getUserTier(user.rewardPoints);
        const goals = tierGoals[userTier] || tierGoals.bronze;

        const monthlyGoals = [
            {
                title: 'Monthly Referrals',
                current: monthlyReferrals,
                target: goals.referrals,
                reward: goals.referrals * 10,
                type: 'referrals'
            },
            {
                title: 'Completed Referrals',
                current: monthlyCompleted,
                target: goals.completed,
                reward: goals.completed * 15,
                type: 'completed'
            },
            {
                title: 'Learning Goals',
                current: monthlyLearning,
                target: goals.learning,
                reward: goals.learning * 100,
                type: 'learning'
            }
        ];

        res.json(monthlyGoals);
    } catch (error) {
        console.error('Get monthly goals error:', error);
        res.status(500).json({ error: 'Failed to fetch monthly goals' });
    }
});

// Helper function to get user tier
function getUserTier(points) {
    if (points >= 5000) return 'diamond';
    if (points >= 3000) return 'platinum';
    if (points >= 1500) return 'gold';
    if (points >= 500) return 'silver';
    return 'bronze';
}

module.exports = router;