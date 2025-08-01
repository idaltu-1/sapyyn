import express from 'express';
import { body, validationResult } from 'express-validator';
import { PrismaClient } from '@prisma/client';
import { auditLog } from '../services/auditService.js';
import bcrypt from 'bcryptjs';

const router = express.Router();
const prisma = new PrismaClient();

// Middleware to check admin permissions
const requireAdmin = (req, res, next) => {
  if (!['SUPER_ADMIN', 'DENTIST_ADMIN', 'SPECIALIST_ADMIN'].includes(req.user.role)) {
    return res.status(403).json({ message: 'Admin permissions required' });
  }
  next();
};

const requireSuperAdmin = (req, res, next) => {
  if (req.user.role !== 'SUPER_ADMIN') {
    return res.status(403).json({ message: 'Super admin permissions required' });
  }
  next();
};

// Dashboard statistics
router.get('/dashboard', requireAdmin, async (req, res) => {
  try {
    const { startDate, endDate } = req.query;

    let dateFilter = {};
    if (startDate && endDate) {
      dateFilter = {
        gte: new Date(startDate),
        lte: new Date(endDate)
      };
    }

    // User statistics
    const userStats = await prisma.user.groupBy({
      by: ['role', 'status'],
      _count: { id: true },
      where: startDate && endDate ? { createdAt: dateFilter } : undefined
    });

    // Referral statistics
    const referralStats = await prisma.referral.groupBy({
      by: ['status'],
      _count: { id: true },
      where: startDate && endDate ? { createdAt: dateFilter } : undefined
    });

    // Recent activity
    const recentUsers = await prisma.user.findMany({
      take: 10,
      orderBy: { createdAt: 'desc' },
      select: {
        id: true,
        firstName: true,
        lastName: true,
        email: true,
        role: true,
        status: true,
        createdAt: true
      }
    });

    const recentReferrals = await prisma.referral.findMany({
      take: 10,
      orderBy: { createdAt: 'desc' },
      include: {
        fromUser: {
          select: {
            firstName: true,
            lastName: true,
            role: true
          }
        },
        toUser: {
          select: {
            firstName: true,
            lastName: true,
            role: true
          }
        }
      }
    });

    // System statistics
    const totalUsers = await prisma.user.count();
    const totalReferrals = await prisma.referral.count();
    const totalDocuments = await prisma.document.count();
    const totalRewards = await prisma.reward.count();

    res.json({
      userStats,
      referralStats,
      recentUsers,
      recentReferrals,
      totals: {
        users: totalUsers,
        referrals: totalReferrals,
        documents: totalDocuments,
        rewards: totalRewards
      }
    });
  } catch (error) {
    console.error('Get dashboard error:', error);
    res.status(500).json({ message: 'Failed to get dashboard data' });
  }
});

// User management
router.get('/users', requireAdmin, async (req, res) => {
  try {
    const { role, status, search, page = 1, limit = 20 } = req.query;
    const skip = (page - 1) * limit;

    let whereClause = {};

    if (role) whereClause.role = role;
    if (status) whereClause.status = status;
    if (search) {
      whereClause.OR = [
        { firstName: { contains: search, mode: 'insensitive' } },
        { lastName: { contains: search, mode: 'insensitive' } },
        { email: { contains: search, mode: 'insensitive' } }
      ];
    }

    const users = await prisma.user.findMany({
      where: whereClause,
      select: {
        id: true,
        firstName: true,
        lastName: true,
        email: true,
        phone: true,
        role: true,
        status: true,
        lastLoginAt: true,
        createdAt: true,
        updatedAt: true,
        patientProfile: {
          select: {
            dateOfBirth: true,
            city: true,
            state: true
          }
        },
        dentistProfile: {
          select: {
            licenseNumber: true,
            dentistCode: true,
            specializations: true,
            practice: {
              select: { name: true }
            }
          }
        },
        specialistProfile: {
          select: {
            licenseNumber: true,
            specialistCode: true,
            specialization: true,
            practice: {
              select: { name: true }
            }
          }
        }
      },
      orderBy: { createdAt: 'desc' },
      skip: parseInt(skip),
      take: parseInt(limit)
    });

    const total = await prisma.user.count({ where: whereClause });

    res.json({
      users,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    console.error('Get users error:', error);
    res.status(500).json({ message: 'Failed to get users' });
  }
});

// Get specific user
router.get('/users/:id', requireAdmin, async (req, res) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.params.id },
      include: {
        patientProfile: true,
        dentistProfile: {
          include: { practice: true }
        },
        specialistProfile: {
          include: { practice: true }
        },
        adminProfile: {
          include: { practice: true }
        },
        _count: {
          select: {
            sentReferrals: true,
            receivedReferrals: true,
            documents: true,
            rewards: true
          }
        }
      }
    });

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    // Remove sensitive information
    const { password, resetPasswordToken, verificationToken, ...userProfile } = user;

    res.json(userProfile);
  } catch (error) {
    console.error('Get user error:', error);
    res.status(500).json({ message: 'Failed to get user' });
  }
});

// Update user status
router.put('/users/:id/status', requireAdmin, [
  body('status').isIn(['ACTIVE', 'INACTIVE', 'PENDING', 'SUSPENDED']),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { status } = req.body;

    const user = await prisma.user.findUnique({
      where: { id: req.params.id }
    });

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    const updatedUser = await prisma.user.update({
      where: { id: req.params.id },
      data: { status },
      select: {
        id: true,
        firstName: true,
        lastName: true,
        email: true,
        role: true,
        status: true
      }
    });

    // Create notification for user
    await prisma.notification.create({
      data: {
        userId: req.params.id,
        title: 'Account Status Updated',
        message: `Your account status has been changed to ${status}`,
        type: status === 'ACTIVE' ? 'SUCCESS' : 'WARNING',
        category: 'SYSTEM'
      }
    });

    // Audit log
    await auditLog('UPDATE_USER_STATUS', 'USER', user.id, { status: user.status }, { status }, req.ip, req.get('User-Agent'));

    res.json(updatedUser);
  } catch (error) {
    console.error('Update user status error:', error);
    res.status(500).json({ message: 'Failed to update user status' });
  }
});

// Create admin user
router.post('/users', requireSuperAdmin, [
  body('email').isEmail().normalizeEmail(),
  body('password').isLength({ min: 8 }),
  body('firstName').trim().isLength({ min: 1 }),
  body('lastName').trim().isLength({ min: 1 }),
  body('role').isIn(['DENTIST_ADMIN', 'SPECIALIST_ADMIN', 'SUPER_ADMIN']),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { email, password, firstName, lastName, role, phone, practiceId } = req.body;

    // Check if user already exists
    const existingUser = await prisma.user.findUnique({
      where: { email }
    });

    if (existingUser) {
      return res.status(400).json({ message: 'User already exists with this email' });
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, parseInt(process.env.BCRYPT_ROUNDS) || 12);

    // Create user
    const user = await prisma.user.create({
      data: {
        email,
        password: hashedPassword,
        firstName,
        lastName,
        phone,
        role,
        status: 'ACTIVE' // Admin users are active by default
      }
    });

    // Create admin profile
    await prisma.adminProfile.create({
      data: {
        userId: user.id,
        practiceId,
        permissions: role === 'SUPER_ADMIN' ? ['ALL'] : ['MANAGE_PRACTICE', 'MANAGE_USERS', 'VIEW_REPORTS']
      }
    });

    // Audit log
    await auditLog('CREATE_ADMIN_USER', 'USER', user.id, null, { email, role }, req.ip, req.get('User-Agent'));

    res.status(201).json({
      message: 'Admin user created successfully',
      user: {
        id: user.id,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        role: user.role,
        status: user.status
      }
    });
  } catch (error) {
    console.error('Create admin user error:', error);
    res.status(500).json({ message: 'Failed to create admin user' });
  }
});

// System settings
router.get('/settings', requireSuperAdmin, async (req, res) => {
  try {
    const settings = await prisma.systemSettings.findMany({
      orderBy: { key: 'asc' }
    });

    res.json(settings);
  } catch (error) {
    console.error('Get settings error:', error);
    res.status(500).json({ message: 'Failed to get system settings' });
  }
});

// Update system setting
router.put('/settings/:key', requireSuperAdmin, [
  body('value').exists(),
  body('description').optional().trim(),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { key } = req.params;
    const { value, description } = req.body;

    const setting = await prisma.systemSettings.upsert({
      where: { key },
      update: {
        value,
        ...(description && { description })
      },
      create: {
        key,
        value,
        description
      }
    });

    // Audit log
    await auditLog('UPDATE_SYSTEM_SETTING', 'SYSTEM_SETTING', setting.id, null, { key, value }, req.ip, req.get('User-Agent'));

    res.json(setting);
  } catch (error) {
    console.error('Update setting error:', error);
    res.status(500).json({ message: 'Failed to update system setting' });
  }
});

// Audit logs
router.get('/audit-logs', requireAdmin, async (req, res) => {
  try {
    const { action, resource, userId, startDate, endDate, page = 1, limit = 50 } = req.query;
    const skip = (page - 1) * limit;

    let whereClause = {};

    if (action) whereClause.action = action;
    if (resource) whereClause.resource = resource;
    if (userId) whereClause.userId = userId;

    if (startDate && endDate) {
      whereClause.createdAt = {
        gte: new Date(startDate),
        lte: new Date(endDate)
      };
    }

    const auditLogs = await prisma.auditLog.findMany({
      where: whereClause,
      include: {
        user: {
          select: {
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

    const total = await prisma.auditLog.count({ where: whereClause });

    res.json({
      auditLogs,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    console.error('Get audit logs error:', error);
    res.status(500).json({ message: 'Failed to get audit logs' });
  }
});

// System health check
router.get('/health', requireAdmin, async (req, res) => {
  try {
    // Check database connection
    const dbCheck = await prisma.$queryRaw`SELECT 1 as test`;
    
    // Check recent activity
    const recentUsers = await prisma.user.count({
      where: {
        createdAt: {
          gte: new Date(Date.now() - 24 * 60 * 60 * 1000) // Last 24 hours
        }
      }
    });

    const recentReferrals = await prisma.referral.count({
      where: {
        createdAt: {
          gte: new Date(Date.now() - 24 * 60 * 60 * 1000)
        }
      }
    });

    // Check for failed rewards
    const failedRewards = await prisma.reward.count({
      where: { status: 'FAILED' }
    });

    // Check for pending rewards older than 1 hour
    const stuckRewards = await prisma.reward.count({
      where: {
        status: 'PROCESSING',
        processedAt: {
          lt: new Date(Date.now() - 60 * 60 * 1000)
        }
      }
    });

    const health = {
      status: 'OK',
      timestamp: new Date(),
      checks: {
        database: dbCheck ? 'OK' : 'ERROR',
        recentActivity: {
          newUsers24h: recentUsers,
          newReferrals24h: recentReferrals
        },
        rewards: {
          failed: failedRewards,
          stuck: stuckRewards
        }
      }
    };

    // Determine overall health status
    if (!dbCheck || stuckRewards > 10) {
      health.status = 'ERROR';
    } else if (failedRewards > 5 || stuckRewards > 0) {
      health.status = 'WARNING';
    }

    res.json(health);
  } catch (error) {
    console.error('Health check error:', error);
    res.status(500).json({
      status: 'ERROR',
      message: 'Health check failed',
      error: error.message
    });
  }
});

// Bulk operations
router.post('/bulk/update-user-status', requireSuperAdmin, [
  body('userIds').isArray().notEmpty(),
  body('status').isIn(['ACTIVE', 'INACTIVE', 'PENDING', 'SUSPENDED']),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { userIds, status } = req.body;

    const updatedUsers = await prisma.user.updateMany({
      where: {
        id: { in: userIds }
      },
      data: { status }
    });

    // Create notifications for affected users
    await prisma.notification.createMany({
      data: userIds.map(userId => ({
        userId,
        title: 'Account Status Updated',
        message: `Your account status has been changed to ${status}`,
        type: status === 'ACTIVE' ? 'SUCCESS' : 'WARNING',
        category: 'SYSTEM'
      }))
    });

    // Audit log
    await auditLog('BULK_UPDATE_USER_STATUS', 'USER', null, null, { 
      userIds, 
      status, 
      count: updatedUsers.count 
    }, req.ip, req.get('User-Agent'));

    res.json({
      message: `Updated ${updatedUsers.count} users`,
      updatedCount: updatedUsers.count
    });
  } catch (error) {
    console.error('Bulk update user status error:', error);
    res.status(500).json({ message: 'Failed to bulk update user status' });
  }
});

export default router;