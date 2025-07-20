const express = require('express');
const router = express.Router();
const NoCodeBackendService = require('../services/NoCodeBackendService');
const { authenticateToken, authorize } = require('../middleware/auth');

const noCodeService = new NoCodeBackendService();

// Health check for all no-code integrations
router.get('/health', authenticateToken, authorize('super_admin'), async (req, res) => {
    try {
        const healthStatus = await noCodeService.healthCheck();
        res.json({
            status: 'ok',
            timestamp: new Date().toISOString(),
            services: healthStatus
        });
    } catch (error) {
        console.error('Health check error:', error);
        res.status(500).json({ error: 'Health check failed' });
    }
});

// Sync data to Airtable
router.post('/airtable/sync', authenticateToken, authorize('super_admin'), async (req, res) => {
    try {
        const { tableName, records } = req.body;
        
        if (!tableName || !records) {
            return res.status(400).json({ error: 'Table name and records are required' });
        }

        const results = [];
        
        for (const record of records) {
            try {
                const result = await noCodeService.createAirtableRecord(tableName, record);
                results.push({ success: true, id: result.id, record: result });
            } catch (error) {
                results.push({ success: false, error: error.message, record });
            }
        }

        res.json({
            message: 'Sync completed',
            results,
            successful: results.filter(r => r.success).length,
            failed: results.filter(r => !r.success).length
        });

    } catch (error) {
        console.error('Airtable sync error:', error);
        res.status(500).json({ error: 'Sync failed' });
    }
});

// Get Airtable records
router.get('/airtable/:tableName', authenticateToken, authorize('super_admin'), async (req, res) => {
    try {
        const { tableName } = req.params;
        const { filterByFormula, maxRecords, sort } = req.query;
        
        const filters = {};
        if (filterByFormula) filters.filterByFormula = filterByFormula;
        if (maxRecords) filters.maxRecords = parseInt(maxRecords);
        if (sort) filters.sort = JSON.parse(sort);

        const records = await noCodeService.getAirtableRecords(tableName, filters);
        
        res.json({
            records,
            count: records.length
        });

    } catch (error) {
        console.error('Airtable fetch error:', error);
        res.status(500).json({ error: 'Failed to fetch records' });
    }
});

// Update Airtable record
router.put('/airtable/:tableName/:recordId', authenticateToken, authorize('super_admin'), async (req, res) => {
    try {
        const { tableName, recordId } = req.params;
        const { fields } = req.body;

        if (!fields) {
            return res.status(400).json({ error: 'Fields are required' });
        }

        const result = await noCodeService.updateAirtableRecord(tableName, recordId, fields);
        
        res.json({
            message: 'Record updated successfully',
            record: result
        });

    } catch (error) {
        console.error('Airtable update error:', error);
        res.status(500).json({ error: 'Failed to update record' });
    }
});

// Trigger Zapier webhook
router.post('/zapier/trigger', authenticateToken, async (req, res) => {
    try {
        const { data, webhookUrl } = req.body;

        if (!data) {
            return res.status(400).json({ error: 'Data is required' });
        }

        const result = await noCodeService.triggerZapierWebhook(data, webhookUrl);
        
        res.json({
            message: 'Zapier webhook triggered successfully',
            result
        });

    } catch (error) {
        console.error('Zapier trigger error:', error);
        res.status(500).json({ error: 'Failed to trigger Zapier webhook' });
    }
});

// Trigger N8N workflow
router.post('/n8n/trigger', authenticateToken, async (req, res) => {
    try {
        const { workflowData, workflowId } = req.body;

        if (!workflowData) {
            return res.status(400).json({ error: 'Workflow data is required' });
        }

        const result = await noCodeService.triggerN8NWorkflow(workflowData, workflowId);
        
        res.json({
            message: 'N8N workflow triggered successfully',
            result
        });

    } catch (error) {
        console.error('N8N trigger error:', error);
        res.status(500).json({ error: 'Failed to trigger N8N workflow' });
    }
});

// Create Notion page
router.post('/notion/pages', authenticateToken, authorize('super_admin'), async (req, res) => {
    try {
        const { databaseId, properties } = req.body;

        if (!properties) {
            return res.status(400).json({ error: 'Properties are required' });
        }

        const result = await noCodeService.createNotionPage(databaseId, properties);
        
        res.json({
            message: 'Notion page created successfully',
            page: result
        });

    } catch (error) {
        console.error('Notion create error:', error);
        res.status(500).json({ error: 'Failed to create Notion page' });
    }
});

// Update Notion page
router.put('/notion/pages/:pageId', authenticateToken, authorize('super_admin'), async (req, res) => {
    try {
        const { pageId } = req.params;
        const { properties } = req.body;

        if (!properties) {
            return res.status(400).json({ error: 'Properties are required' });
        }

        const result = await noCodeService.updateNotionPage(pageId, properties);
        
        res.json({
            message: 'Notion page updated successfully',
            page: result
        });

    } catch (error) {
        console.error('Notion update error:', error);
        res.status(500).json({ error: 'Failed to update Notion page' });
    }
});

// Trigger Make.com scenario
router.post('/make/trigger', authenticateToken, async (req, res) => {
    try {
        const { data, scenarioId } = req.body;

        if (!data) {
            return res.status(400).json({ error: 'Data is required' });
        }

        const result = await noCodeService.triggerMakeScenario(data, scenarioId);
        
        res.json({
            message: 'Make scenario triggered successfully',
            result
        });

    } catch (error) {
        console.error('Make trigger error:', error);
        res.status(500).json({ error: 'Failed to trigger Make scenario' });
    }
});

// Generic webhook trigger
router.post('/webhook/trigger', authenticateToken, async (req, res) => {
    try {
        const { url, data, headers } = req.body;

        if (!url || !data) {
            return res.status(400).json({ error: 'URL and data are required' });
        }

        const result = await noCodeService.triggerGenericWebhook(url, data, headers);
        
        res.json({
            message: 'Webhook triggered successfully',
            result
        });

    } catch (error) {
        console.error('Generic webhook error:', error);
        res.status(500).json({ error: 'Failed to trigger webhook' });
    }
});

// Bulk sync referrals to external platforms
router.post('/sync/referrals', authenticateToken, authorize('super_admin'), async (req, res) => {
    try {
        const Referral = require('../models/Referral');
        const User = require('../models/User');
        
        const { limit = 100, startDate, endDate } = req.body;
        
        // Build query
        const query = {};
        if (startDate || endDate) {
            query.createdAt = {};
            if (startDate) query.createdAt.$gte = new Date(startDate);
            if (endDate) query.createdAt.$lte = new Date(endDate);
        }

        const referrals = await Referral.find(query)
            .populate('patientId', 'firstName lastName email phone')
            .populate('referringDentistId', 'firstName lastName email')
            .populate('specialistId', 'firstName lastName email')
            .limit(limit)
            .sort({ createdAt: -1 });

        const syncResults = {
            airtable: [],
            zapier: [],
            notion: []
        };

        for (const referral of referrals) {
            // Sync to Airtable
            try {
                const airtableResult = await noCodeService.syncReferralToAirtable(referral);
                syncResults.airtable.push({ referralId: referral.referralId, result: airtableResult });
            } catch (error) {
                syncResults.airtable.push({ referralId: referral.referralId, error: error.message });
            }

            // Trigger workflows
            try {
                const workflowResult = await noCodeService.triggerReferralWorkflow(referral, 'sync');
                syncResults.zapier.push({ referralId: referral.referralId, result: workflowResult });
            } catch (error) {
                syncResults.zapier.push({ referralId: referral.referralId, error: error.message });
            }
        }

        res.json({
            message: 'Bulk sync completed',
            processed: referrals.length,
            results: syncResults
        });

    } catch (error) {
        console.error('Bulk sync error:', error);
        res.status(500).json({ error: 'Bulk sync failed' });
    }
});

// Analytics sync
router.post('/sync/analytics', authenticateToken, authorize('super_admin'), async (req, res) => {
    try {
        const Referral = require('../models/Referral');
        const User = require('../models/User');
        const Reward = require('../models/Reward');

        // Generate analytics data
        const totalReferrals = await Referral.countDocuments();
        const completedReferrals = await Referral.countDocuments({ status: 'completed' });
        const activeUsers = await User.countDocuments({ isActive: true });
        const totalRewardPoints = await Reward.aggregate([
            { $group: { _id: null, total: { $sum: '$points' } } }
        ]);

        const analytics = {
            totalReferrals,
            completedReferrals,
            activeUsers,
            rewardPointsDistributed: totalRewardPoints[0]?.total || 0,
            avgCompletionTime: 24, // hours - would calculate from actual data
            topPerformers: await User.find({ role: 'dentist' })
                .sort({ rewardPoints: -1 })
                .limit(5)
                .select('firstName lastName rewardPoints')
        };

        const syncResults = await noCodeService.syncAnalyticsData(analytics);
        
        res.json({
            message: 'Analytics sync completed',
            analytics,
            syncResults
        });

    } catch (error) {
        console.error('Analytics sync error:', error);
        res.status(500).json({ error: 'Analytics sync failed' });
    }
});

// Configuration endpoints
router.get('/config', authenticateToken, authorize('super_admin'), async (req, res) => {
    try {
        const config = {
            airtable: {
                configured: !!(process.env.AIRTABLE_BASE_ID && process.env.AIRTABLE_API_KEY),
                baseId: process.env.AIRTABLE_BASE_ID ? '***' + process.env.AIRTABLE_BASE_ID.slice(-4) : null
            },
            zapier: {
                configured: !!process.env.ZAPIER_WEBHOOK_URL,
                webhookUrl: process.env.ZAPIER_WEBHOOK_URL ? '***' + process.env.ZAPIER_WEBHOOK_URL.slice(-10) : null
            },
            n8n: {
                configured: !!process.env.N8N_WEBHOOK_URL,
                webhookUrl: process.env.N8N_WEBHOOK_URL ? '***' + process.env.N8N_WEBHOOK_URL.slice(-10) : null
            },
            notion: {
                configured: !!process.env.NOTION_TOKEN,
                databaseId: process.env.NOTION_DATABASE_ID ? '***' + process.env.NOTION_DATABASE_ID.slice(-4) : null
            },
            make: {
                configured: !!process.env.MAKE_WEBHOOK_URL,
                webhookUrl: process.env.MAKE_WEBHOOK_URL ? '***' + process.env.MAKE_WEBHOOK_URL.slice(-10) : null
            }
        };

        res.json(config);
    } catch (error) {
        console.error('Config fetch error:', error);
        res.status(500).json({ error: 'Failed to fetch configuration' });
    }
});

module.exports = router;