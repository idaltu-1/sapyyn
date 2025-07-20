const express = require('express');
const router = express.Router();
const ReferralCode = require('../models/ReferralCode');
const { authenticateToken, authorize } = require('../middleware/auth');
const { body, param, validationResult } = require('express-validator');

// Generate new referral code for doctor
router.post('/generate', 
    authenticateToken,
    authorize('dentist', 'specialist', 'dentist_admin', 'specialist_admin', 'super_admin'),
    [
        body('restrictions.maxUsagePerDay').optional().isInt({ min: 1, max: 100 }),
        body('restrictions.maxUsagePerMonth').optional().isInt({ min: 1, max: 1000 }),
        body('restrictions.allowedSpecialties').optional().isArray(),
        body('restrictions.allowedRegions').optional().isArray()
    ],
    async (req, res) => {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) {
                return res.status(400).json({ error: 'Validation failed', details: errors.array() });
            }

            // Check if user already has an active code
            const existingCode = await ReferralCode.findOne({ 
                doctorId: req.user.userId, 
                isActive: true 
            });

            if (existingCode) {
                return res.status(400).json({ 
                    error: 'You already have an active referral code',
                    code: existingCode.code
                });
            }

            // Generate unique code
            const code = await ReferralCode.generateUniqueCode();

            // Create new referral code
            const referralCode = new ReferralCode({
                code,
                doctorId: req.user.userId,
                metadata: {
                    practiceId: req.user.practiceId,
                    generatedBy: req.user.userId
                },
                restrictions: req.body.restrictions || {}
            });

            await referralCode.save();

            res.status(201).json({
                message: 'Referral code generated successfully',
                code: referralCode.code,
                expiresAt: referralCode.expiresAt,
                restrictions: referralCode.restrictions
            });

        } catch (error) {
            console.error('Generate referral code error:', error);
            res.status(500).json({ error: 'Failed to generate referral code' });
        }
    }
);

// Get doctor's referral code
router.get('/my-code', 
    authenticateToken,
    authorize('dentist', 'specialist', 'dentist_admin', 'specialist_admin'),
    async (req, res) => {
        try {
            const referralCode = await ReferralCode.findOne({ 
                doctorId: req.user.userId 
            }).populate('doctorId', 'firstName lastName email');

            if (!referralCode) {
                return res.status(404).json({ error: 'No referral code found' });
            }

            res.json({
                code: referralCode.code,
                isActive: referralCode.isActive,
                usageCount: referralCode.usageCount,
                lastUsed: referralCode.lastUsed,
                expiresAt: referralCode.expiresAt,
                analytics: referralCode.analytics,
                restrictions: referralCode.restrictions,
                quickFormUrl: `${process.env.FRONTEND_URL || 'http://localhost:3000'}/quick-referral/${referralCode.code}`
            });

        } catch (error) {
            console.error('Get referral code error:', error);
            res.status(500).json({ error: 'Failed to retrieve referral code' });
        }
    }
);

// Validate referral code (public endpoint for quick form)
router.get('/validate/:code',
    [param('code').isLength({ min: 6, max: 6 }).isAlphanumeric()],
    async (req, res) => {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) {
                return res.status(400).json({ error: 'Invalid code format' });
            }

            const { code } = req.params;
            const referralCode = await ReferralCode.findOne({ 
                code: code.toUpperCase() 
            }).populate('doctorId', 'firstName lastName email practiceId')
              .populate('metadata.practiceId', 'name type address phone');

            if (!referralCode) {
                return res.status(404).json({ error: 'Referral code not found' });
            }

            if (!referralCode.isValidForUse()) {
                let reason = 'Referral code is not valid';
                if (!referralCode.isActive) reason = 'Referral code is inactive';
                else if (new Date() >= referralCode.expiresAt) reason = 'Referral code has expired';
                else if (referralCode.isRateLimited()) reason = 'Referral code usage limit exceeded';

                return res.status(400).json({ error: reason });
            }

            res.json({
                valid: true,
                doctor: {
                    name: `Dr. ${referralCode.doctorId.firstName} ${referralCode.doctorId.lastName}`,
                    email: referralCode.doctorId.email
                },
                practice: referralCode.metadata.practiceId ? {
                    name: referralCode.metadata.practiceId.name,
                    type: referralCode.metadata.practiceId.type,
                    address: referralCode.metadata.practiceId.address,
                    phone: referralCode.metadata.practiceId.phone
                } : null,
                restrictions: {
                    allowedSpecialties: referralCode.restrictions.allowedSpecialties,
                    allowedRegions: referralCode.restrictions.allowedRegions
                }
            });

        } catch (error) {
            console.error('Validate referral code error:', error);
            res.status(500).json({ error: 'Failed to validate referral code' });
        }
    }
);

// Use referral code (called when quick form is submitted)
router.post('/use/:code',
    [
        param('code').isLength({ min: 6, max: 6 }).isAlphanumeric(),
        body('referralData').isObject()
    ],
    async (req, res) => {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) {
                return res.status(400).json({ error: 'Validation failed', details: errors.array() });
            }

            const { code } = req.params;
            const { referralData } = req.body;

            const referralCode = await ReferralCode.findOne({ 
                code: code.toUpperCase() 
            }).populate('doctorId');

            if (!referralCode || !referralCode.isValidForUse()) {
                return res.status(400).json({ error: 'Invalid or expired referral code' });
            }

            // Record usage
            await referralCode.recordUsage();

            // Create the referral (this would integrate with your existing referral creation logic)
            const referral = await createReferralFromQuickForm(referralCode.doctorId._id, referralData);

            // Update analytics
            referralCode.analytics.lastReferralDate = new Date();
            await referralCode.save();

            res.json({
                message: 'Referral submitted successfully',
                referralId: referral.referralId,
                trackingUrl: `${process.env.FRONTEND_URL}/track-referral/${referral.referralId}`
            });

        } catch (error) {
            console.error('Use referral code error:', error);
            res.status(500).json({ error: 'Failed to process referral' });
        }
    }
);

// Get referral code analytics
router.get('/analytics/:code',
    authenticateToken,
    [param('code').isLength({ min: 6, max: 6 }).isAlphanumeric()],
    async (req, res) => {
        try {
            const { code } = req.params;
            const referralCode = await ReferralCode.findOne({ 
                code: code.toUpperCase(),
                doctorId: req.user.userId // Ensure user can only see their own analytics
            });

            if (!referralCode) {
                return res.status(404).json({ error: 'Referral code not found' });
            }

            // Get detailed analytics (could expand this with more data)
            const analytics = {
                ...referralCode.analytics,
                usageStats: {
                    totalUses: referralCode.usageCount,
                    lastUsed: referralCode.lastUsed,
                    dailyUsage: referralCode.usageCount, // Simplified - would need daily tracking
                    monthlyUsage: referralCode.usageCount // Simplified - would need monthly tracking
                },
                performance: {
                    successRate: referralCode.analytics.totalReferrals > 0 ? 
                        Math.round((referralCode.analytics.successfulReferrals / referralCode.analytics.totalReferrals) * 100) : 0,
                    averageRating: referralCode.analytics.averageRating
                }
            };

            res.json(analytics);

        } catch (error) {
            console.error('Get analytics error:', error);
            res.status(500).json({ error: 'Failed to retrieve analytics' });
        }
    }
);

// Update referral code settings
router.put('/settings',
    authenticateToken,
    authorize('dentist', 'specialist', 'dentist_admin', 'specialist_admin'),
    [
        body('restrictions.maxUsagePerDay').optional().isInt({ min: 1, max: 100 }),
        body('restrictions.maxUsagePerMonth').optional().isInt({ min: 1, max: 1000 }),
        body('restrictions.allowedSpecialties').optional().isArray(),
        body('restrictions.allowedRegions').optional().isArray()
    ],
    async (req, res) => {
        try {
            const errors = validationResult(req);
            if (!errors.isEmpty()) {
                return res.status(400).json({ error: 'Validation failed', details: errors.array() });
            }

            const referralCode = await ReferralCode.findOne({ 
                doctorId: req.user.userId 
            });

            if (!referralCode) {
                return res.status(404).json({ error: 'Referral code not found' });
            }

            // Update restrictions
            if (req.body.restrictions) {
                referralCode.restrictions = {
                    ...referralCode.restrictions,
                    ...req.body.restrictions
                };
            }

            await referralCode.save();

            res.json({
                message: 'Referral code settings updated successfully',
                restrictions: referralCode.restrictions
            });

        } catch (error) {
            console.error('Update settings error:', error);
            res.status(500).json({ error: 'Failed to update settings' });
        }
    }
);

// Deactivate referral code
router.post('/deactivate',
    authenticateToken,
    authorize('dentist', 'specialist', 'dentist_admin', 'specialist_admin'),
    async (req, res) => {
        try {
            const referralCode = await ReferralCode.findOne({ 
                doctorId: req.user.userId 
            });

            if (!referralCode) {
                return res.status(404).json({ error: 'Referral code not found' });
            }

            referralCode.isActive = false;
            await referralCode.save();

            res.json({ message: 'Referral code deactivated successfully' });

        } catch (error) {
            console.error('Deactivate code error:', error);
            res.status(500).json({ error: 'Failed to deactivate referral code' });
        }
    }
);

// Admin: Get all referral codes
router.get('/admin/all',
    authenticateToken,
    authorize('super_admin'),
    async (req, res) => {
        try {
            const page = parseInt(req.query.page) || 1;
            const limit = parseInt(req.query.limit) || 50;
            const skip = (page - 1) * limit;

            const referralCodes = await ReferralCode.find()
                .populate('doctorId', 'firstName lastName email role')
                .populate('metadata.practiceId', 'name type')
                .sort({ createdAt: -1 })
                .skip(skip)
                .limit(limit);

            const total = await ReferralCode.countDocuments();

            res.json({
                referralCodes,
                pagination: {
                    page,
                    limit,
                    total,
                    pages: Math.ceil(total / limit)
                }
            });

        } catch (error) {
            console.error('Get all codes error:', error);
            res.status(500).json({ error: 'Failed to retrieve referral codes' });
        }
    }
);

// Helper function to create referral from quick form
async function createReferralFromQuickForm(doctorId, referralData) {
    const Referral = require('../models/Referral');
    const User = require('../models/User');
    
    // This would integrate with your existing referral creation logic
    const referralId = 'REF-' + Date.now() + '-' + Math.random().toString(36).substr(2, 9);
    
    const referral = new Referral({
        referralId,
        patientName: referralData.patientName,
        patientPhone: referralData.patientPhone,
        patientEmail: referralData.patientEmail,
        referringDentistId: doctorId,
        referralType: referralData.referralType,
        urgency: referralData.urgency || 'routine',
        clinicalNotes: referralData.clinicalNotes,
        source: 'quick_form',
        rewardPoints: 25 // Points for quick form referral
    });

    await referral.save();
    
    // Award points to referring doctor
    await User.findByIdAndUpdate(doctorId, { $inc: { rewardPoints: 25 } });
    
    return referral;
}

module.exports = router;