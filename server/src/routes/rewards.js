import express from 'express';
import { body, validationResult } from 'express-validator';
import { PrismaClient } from '@prisma/client';
import { auditLog } from '../services/auditService.js';

const router = express.Router();
const prisma = new PrismaClient();

// Get user's rewards
router.get('/', async (req, res) => {
  try {
    const { status, type, page = 1, limit = 20 } = req.query;
    const skip = (page - 1) * limit;

    let whereClause = { userId: req.user.userId };

    if (status) {
      whereClause.status = status;
    }

    if (type) {
      whereClause.type = type;
    }

    const rewards = await prisma.reward.findMany({
      where: whereClause,
      orderBy: { createdAt: 'desc' },
      skip: parseInt(skip),
      take: parseInt(limit)
    });

    const total = await prisma.reward.count({ where: whereClause });

    // Calculate totals by status
    const statusSummary = await prisma.reward.groupBy({
      by: ['status'],
      where: { userId: req.user.userId },
      _sum: {
        amount: true
      },
      _count: {
        id: true
      }
    });

    res.json({
      rewards,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / limit)
      },
      summary: statusSummary
    });
  } catch (error) {
    console.error('Get rewards error:', error);
    res.status(500).json({ message: 'Failed to get rewards' });
  }
});

// Get a specific reward
router.get('/:id', async (req, res) => {
  try {
    const reward = await prisma.reward.findFirst({
      where: {
        id: req.params.id,
        userId: req.user.userId
      }
    });

    if (!reward) {
      return res.status(404).json({ message: 'Reward not found' });
    }

    res.json(reward);
  } catch (error) {
    console.error('Get reward error:', error);
    res.status(500).json({ message: 'Failed to get reward' });
  }
});

// Create a reward (typically called by system processes)
router.post('/', [
  body('type').isString().notEmpty(),
  body('amount').isFloat({ min: 0 }),
  body('provider').isIn(['TANGO', 'TREMENDOUS', 'MANUAL']),
  body('currency').optional().isString(),
], async (req, res) => {
  try {
    // Only allow super admins or system to create rewards
    if (req.user.role !== 'SUPER_ADMIN') {
      return res.status(403).json({ message: 'Insufficient permissions to create rewards' });
    }

    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { 
      userId = req.user.userId,
      type, 
      amount, 
      provider, 
      currency = 'USD', 
      externalId, 
      rewardData 
    } = req.body;

    // Verify the target user exists
    const targetUser = await prisma.user.findUnique({
      where: { id: userId }
    });

    if (!targetUser) {
      return res.status(404).json({ message: 'Target user not found' });
    }

    const reward = await prisma.reward.create({
      data: {
        userId,
        type,
        amount,
        currency,
        provider,
        externalId,
        rewardData,
        statusHistory: [{
          status: 'PENDING',
          timestamp: new Date(),
          note: 'Reward created'
        }]
      }
    });

    // Create notification for the user
    await prisma.notification.create({
      data: {
        userId,
        title: 'New Reward Available',
        message: `You have earned a ${currency} ${amount} reward for ${type}`,
        type: 'SUCCESS',
        category: 'REWARD',
        data: { rewardId: reward.id }
      }
    });

    // Audit log
    await auditLog('CREATE_REWARD', 'REWARD', reward.id, null, reward, req.ip, req.get('User-Agent'));

    res.status(201).json(reward);
  } catch (error) {
    console.error('Create reward error:', error);
    res.status(500).json({ message: 'Failed to create reward' });
  }
});

// Update reward status (typically for processing rewards)
router.put('/:id/status', [
  body('status').isIn(['PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED']),
  body('note').optional().trim(),
  body('failureReason').optional().trim(),
], async (req, res) => {
  try {
    // Only allow super admins or system to update reward status
    if (req.user.role !== 'SUPER_ADMIN') {
      return res.status(403).json({ message: 'Insufficient permissions to update reward status' });
    }

    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { status, note, failureReason, externalId, rewardData } = req.body;

    const currentReward = await prisma.reward.findUnique({
      where: { id: req.params.id }
    });

    if (!currentReward) {
      return res.status(404).json({ message: 'Reward not found' });
    }

    // Update status history
    const newStatusEntry = {
      status,
      timestamp: new Date(),
      note: note || `Status changed to ${status}`,
      updatedBy: req.user.userId
    };

    const updatedStatusHistory = [...(currentReward.statusHistory || []), newStatusEntry];

    const reward = await prisma.reward.update({
      where: { id: req.params.id },
      data: {
        status,
        statusHistory: updatedStatusHistory,
        failureReason: status === 'FAILED' ? failureReason : null,
        processedAt: ['PROCESSING', 'COMPLETED', 'FAILED'].includes(status) ? new Date() : currentReward.processedAt,
        completedAt: status === 'COMPLETED' ? new Date() : null,
        ...(externalId && { externalId }),
        ...(rewardData && { rewardData })
      }
    });

    // Create notification for status update
    let notificationMessage = '';
    let notificationType = 'INFO';

    switch (status) {
      case 'PROCESSING':
        notificationMessage = `Your ${reward.currency} ${reward.amount} reward is being processed`;
        notificationType = 'INFO';
        break;
      case 'COMPLETED':
        notificationMessage = `Your ${reward.currency} ${reward.amount} reward has been completed`;
        notificationType = 'SUCCESS';
        break;
      case 'FAILED':
        notificationMessage = `Your ${reward.currency} ${reward.amount} reward processing failed`;
        notificationType = 'ERROR';
        break;
      case 'CANCELLED':
        notificationMessage = `Your ${reward.currency} ${reward.amount} reward has been cancelled`;
        notificationType = 'WARNING';
        break;
    }

    if (notificationMessage) {
      await prisma.notification.create({
        data: {
          userId: reward.userId,
          title: 'Reward Status Update',
          message: notificationMessage,
          type: notificationType,
          category: 'REWARD',
          data: { rewardId: reward.id, status }
        }
      });
    }

    // Audit log
    await auditLog('UPDATE_REWARD_STATUS', 'REWARD', reward.id, currentReward, { status, note, failureReason }, req.ip, req.get('User-Agent'));

    res.json(reward);
  } catch (error) {
    console.error('Update reward status error:', error);
    res.status(500).json({ message: 'Failed to update reward status' });
  }
});

// Get reward statistics (for admins)
router.get('/admin/statistics', async (req, res) => {
  try {
    if (!['SUPER_ADMIN', 'DENTIST_ADMIN', 'SPECIALIST_ADMIN'].includes(req.user.role)) {
      return res.status(403).json({ message: 'Insufficient permissions to view reward statistics' });
    }

    const { startDate, endDate, userId } = req.query;

    let whereClause = {};

    if (startDate && endDate) {
      whereClause.createdAt = {
        gte: new Date(startDate),
        lte: new Date(endDate)
      };
    }

    if (userId) {
      whereClause.userId = userId;
    }

    // Get statistics by status
    const statusStats = await prisma.reward.groupBy({
      by: ['status'],
      where: whereClause,
      _sum: {
        amount: true
      },
      _count: {
        id: true
      }
    });

    // Get statistics by type
    const typeStats = await prisma.reward.groupBy({
      by: ['type'],
      where: whereClause,
      _sum: {
        amount: true
      },
      _count: {
        id: true
      }
    });

    // Get statistics by provider
    const providerStats = await prisma.reward.groupBy({
      by: ['provider'],
      where: whereClause,
      _sum: {
        amount: true
      },
      _count: {
        id: true
      }
    });

    // Get monthly trends if date range is provided
    let monthlyTrends = [];
    if (startDate && endDate) {
      monthlyTrends = await prisma.$queryRaw`
        SELECT 
          DATE_TRUNC('month', "createdAt") as month,
          COUNT(*)::int as count,
          SUM(amount)::float as total_amount
        FROM rewards 
        WHERE "createdAt" >= ${new Date(startDate)} 
          AND "createdAt" <= ${new Date(endDate)}
        GROUP BY DATE_TRUNC('month', "createdAt")
        ORDER BY month
      `;
    }

    res.json({
      statusStats,
      typeStats,
      providerStats,
      monthlyTrends
    });
  } catch (error) {
    console.error('Get reward statistics error:', error);
    res.status(500).json({ message: 'Failed to get reward statistics' });
  }
});

// Get all rewards (for admins)
router.get('/admin/all', async (req, res) => {
  try {
    if (!['SUPER_ADMIN', 'DENTIST_ADMIN', 'SPECIALIST_ADMIN'].includes(req.user.role)) {
      return res.status(403).json({ message: 'Insufficient permissions to view all rewards' });
    }

    const { status, type, provider, userId, page = 1, limit = 20 } = req.query;
    const skip = (page - 1) * limit;

    let whereClause = {};

    if (status) whereClause.status = status;
    if (type) whereClause.type = type;
    if (provider) whereClause.provider = provider;
    if (userId) whereClause.userId = userId;

    const rewards = await prisma.reward.findMany({
      where: whereClause,
      include: {
        user: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            email: true,
            role: true
          }
        }
      },
      orderBy: { createdAt: 'desc' },
      skip: parseInt(skip),
      take: parseInt(limit)
    });

    const total = await prisma.reward.count({ where: whereClause });

    res.json({
      rewards,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    console.error('Get all rewards error:', error);
    res.status(500).json({ message: 'Failed to get rewards' });
  }
});

// Process pending rewards (system endpoint)
router.post('/process-pending', async (req, res) => {
  try {
    if (req.user.role !== 'SUPER_ADMIN') {
      return res.status(403).json({ message: 'Insufficient permissions to process rewards' });
    }

    const { provider, limit = 10 } = req.body;

    let whereClause = { status: 'PENDING' };
    if (provider) whereClause.provider = provider;

    const pendingRewards = await prisma.reward.findMany({
      where: whereClause,
      take: parseInt(limit),
      include: {
        user: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            email: true
          }
        }
      }
    });

    const processedRewards = [];

    for (const reward of pendingRewards) {
      try {
        // Update status to processing
        const updatedReward = await prisma.reward.update({
          where: { id: reward.id },
          data: {
            status: 'PROCESSING',
            processedAt: new Date(),
            statusHistory: [
              ...(reward.statusHistory || []),
              {
                status: 'PROCESSING',
                timestamp: new Date(),
                note: 'Reward processing started',
                updatedBy: req.user.userId
              }
            ]
          }
        });

        processedRewards.push(updatedReward);

        // Here you would integrate with actual reward providers
        // For now, we'll just mark as completed after a delay
        setTimeout(async () => {
          try {
            await prisma.reward.update({
              where: { id: reward.id },
              data: {
                status: 'COMPLETED',
                completedAt: new Date(),
                statusHistory: [
                  ...(updatedReward.statusHistory || []),
                  {
                    status: 'COMPLETED',
                    timestamp: new Date(),
                    note: 'Reward processing completed',
                    updatedBy: 'SYSTEM'
                  }
                ]
              }
            });
          } catch (completionError) {
            console.error('Error completing reward:', completionError);
          }
        }, 5000); // Simulate processing delay

      } catch (processError) {
        console.error('Error processing reward:', processError);
        
        // Mark as failed
        await prisma.reward.update({
          where: { id: reward.id },
          data: {
            status: 'FAILED',
            processedAt: new Date(),
            failureReason: processError.message,
            statusHistory: [
              ...(reward.statusHistory || []),
              {
                status: 'FAILED',
                timestamp: new Date(),
                note: `Processing failed: ${processError.message}`,
                updatedBy: req.user.userId
              }
            ]
          }
        });
      }
    }

    // Audit log
    await auditLog('PROCESS_PENDING_REWARDS', 'REWARD', null, null, { 
      processedCount: processedRewards.length,
      provider 
    }, req.ip, req.get('User-Agent'));

    res.json({
      message: `Started processing ${processedRewards.length} rewards`,
      processedRewards
    });
  } catch (error) {
    console.error('Process pending rewards error:', error);
    res.status(500).json({ message: 'Failed to process pending rewards' });
  }
});

export default router;