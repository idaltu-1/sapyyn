import express from 'express';
import { body, validationResult } from 'express-validator';
import { PrismaClient } from '@prisma/client';
import { auditLog } from '../services/auditService.js';

const router = express.Router();
const prisma = new PrismaClient();

// Create a new practice
router.post('/', [
  body('name').trim().isLength({ min: 1 }),
  body('type').isIn(['DENTAL', 'SPECIALIST']),
  body('address').trim().isLength({ min: 1 }),
  body('city').trim().isLength({ min: 1 }),
  body('state').trim().isLength({ min: 1 }),
  body('zipCode').trim().isLength({ min: 1 }),
  body('phone').trim().isLength({ min: 1 }),
  body('email').optional().isEmail().normalizeEmail(),
  body('website').optional().isURL(),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    // Only allow dentist/specialist admins and super admins to create practices
    if (!['DENTIST_ADMIN', 'SPECIALIST_ADMIN', 'SUPER_ADMIN'].includes(req.user.role)) {
      return res.status(403).json({ message: 'Insufficient permissions to create practice' });
    }

    const { name, type, address, city, state, zipCode, phone, email, website, settings } = req.body;

    const practice = await prisma.practice.create({
      data: {
        name,
        type,
        address,
        city,
        state,
        zipCode,
        phone,
        email,
        website,
        settings
      }
    });

    // If user is an admin, associate them with this practice
    if (['DENTIST_ADMIN', 'SPECIALIST_ADMIN'].includes(req.user.role)) {
      await prisma.adminProfile.upsert({
        where: { userId: req.user.userId },
        update: { practiceId: practice.id },
        create: {
          userId: req.user.userId,
          practiceId: practice.id,
          permissions: ['MANAGE_PRACTICE', 'MANAGE_USERS']
        }
      });
    }

    // Audit log
    await auditLog('CREATE_PRACTICE', 'PRACTICE', practice.id, null, practice, req.ip, req.get('User-Agent'));

    res.status(201).json(practice);
  } catch (error) {
    console.error('Create practice error:', error);
    res.status(500).json({ message: 'Failed to create practice' });
  }
});

// Get practices (for admins and search purposes)
router.get('/', async (req, res) => {
  try {
    const { type, search, page = 1, limit = 20 } = req.query;
    const skip = (page - 1) * limit;

    let whereClause = {};

    if (type) {
      whereClause.type = type;
    }

    if (search) {
      whereClause.OR = [
        { name: { contains: search, mode: 'insensitive' } },
        { city: { contains: search, mode: 'insensitive' } },
        { state: { contains: search, mode: 'insensitive' } }
      ];
    }

    const practices = await prisma.practice.findMany({
      where: whereClause,
      include: {
        _count: {
          select: {
            dentists: true,
            specialists: true,
            admins: true
          }
        }
      },
      orderBy: { name: 'asc' },
      skip: parseInt(skip),
      take: parseInt(limit)
    });

    const total = await prisma.practice.count({ where: whereClause });

    res.json({
      practices,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    console.error('Get practices error:', error);
    res.status(500).json({ message: 'Failed to get practices' });
  }
});

// Get a specific practice
router.get('/:id', async (req, res) => {
  try {
    const practice = await prisma.practice.findUnique({
      where: { id: req.params.id },
      include: {
        dentists: {
          include: {
            user: {
              select: {
                id: true,
                firstName: true,
                lastName: true,
                email: true,
                status: true
              }
            }
          }
        },
        specialists: {
          include: {
            user: {
              select: {
                id: true,
                firstName: true,
                lastName: true,
                email: true,
                status: true
              }
            }
          }
        },
        admins: {
          include: {
            user: {
              select: {
                id: true,
                firstName: true,
                lastName: true,
                email: true,
                status: true
              }
            }
          }
        }
      }
    });

    if (!practice) {
      return res.status(404).json({ message: 'Practice not found' });
    }

    // Check if user has access to view this practice
    const userProfile = await prisma.user.findUnique({
      where: { id: req.user.userId },
      include: {
        dentistProfile: true,
        specialistProfile: true,
        adminProfile: true
      }
    });

    const hasAccess = req.user.role === 'SUPER_ADMIN' ||
      userProfile.dentistProfile?.practiceId === practice.id ||
      userProfile.specialistProfile?.practiceId === practice.id ||
      userProfile.adminProfile?.practiceId === practice.id;

    if (!hasAccess) {
      return res.status(403).json({ message: 'Access denied to this practice' });
    }

    res.json(practice);
  } catch (error) {
    console.error('Get practice error:', error);
    res.status(500).json({ message: 'Failed to get practice' });
  }
});

// Update a practice
router.put('/:id', [
  body('name').optional().trim().isLength({ min: 1 }),
  body('type').optional().isIn(['DENTAL', 'SPECIALIST']),
  body('address').optional().trim().isLength({ min: 1 }),
  body('city').optional().trim().isLength({ min: 1 }),
  body('state').optional().trim().isLength({ min: 1 }),
  body('zipCode').optional().trim().isLength({ min: 1 }),
  body('phone').optional().trim().isLength({ min: 1 }),
  body('email').optional().isEmail().normalizeEmail(),
  body('website').optional().isURL(),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    // Check if user has permission to update this practice
    const practice = await prisma.practice.findUnique({
      where: { id: req.params.id }
    });

    if (!practice) {
      return res.status(404).json({ message: 'Practice not found' });
    }

    const userProfile = await prisma.user.findUnique({
      where: { id: req.user.userId },
      include: {
        adminProfile: true
      }
    });

    const hasPermission = req.user.role === 'SUPER_ADMIN' ||
      (userProfile.adminProfile?.practiceId === practice.id && 
       userProfile.adminProfile?.permissions?.includes('MANAGE_PRACTICE'));

    if (!hasPermission) {
      return res.status(403).json({ message: 'Insufficient permissions to update this practice' });
    }

    const { name, type, address, city, state, zipCode, phone, email, website, settings } = req.body;

    const updatedPractice = await prisma.practice.update({
      where: { id: req.params.id },
      data: {
        ...(name && { name }),
        ...(type && { type }),
        ...(address && { address }),
        ...(city && { city }),
        ...(state && { state }),
        ...(zipCode && { zipCode }),
        ...(phone && { phone }),
        ...(email && { email }),
        ...(website && { website }),
        ...(settings && { settings })
      }
    });

    // Audit log
    await auditLog('UPDATE_PRACTICE', 'PRACTICE', practice.id, practice, updatedPractice, req.ip, req.get('User-Agent'));

    res.json(updatedPractice);
  } catch (error) {
    console.error('Update practice error:', error);
    res.status(500).json({ message: 'Failed to update practice' });
  }
});

// Get users by practice
router.get('/:id/users', async (req, res) => {
  try {
    const { role, page = 1, limit = 20 } = req.query;
    const skip = (page - 1) * limit;

    // Check if user has access to view this practice
    const practice = await prisma.practice.findUnique({
      where: { id: req.params.id }
    });

    if (!practice) {
      return res.status(404).json({ message: 'Practice not found' });
    }

    const userProfile = await prisma.user.findUnique({
      where: { id: req.user.userId },
      include: {
        dentistProfile: true,
        specialistProfile: true,
        adminProfile: true
      }
    });

    const hasAccess = req.user.role === 'SUPER_ADMIN' ||
      userProfile.dentistProfile?.practiceId === practice.id ||
      userProfile.specialistProfile?.practiceId === practice.id ||
      userProfile.adminProfile?.practiceId === practice.id;

    if (!hasAccess) {
      return res.status(403).json({ message: 'Access denied to this practice' });
    }

    let users = [];
    let total = 0;

    if (!role || role === 'DENTIST') {
      const dentists = await prisma.dentistProfile.findMany({
        where: { practiceId: req.params.id },
        include: {
          user: {
            select: {
              id: true,
              firstName: true,
              lastName: true,
              email: true,
              phone: true,
              status: true,
              createdAt: true
            }
          }
        },
        skip: parseInt(skip),
        take: parseInt(limit)
      });

      users = [...users, ...dentists.map(d => ({ ...d.user, profile: d, role: 'DENTIST' }))];
      
      if (!role) {
        total += await prisma.dentistProfile.count({ where: { practiceId: req.params.id } });
      } else {
        total = await prisma.dentistProfile.count({ where: { practiceId: req.params.id } });
      }
    }

    if (!role || role === 'SPECIALIST') {
      const specialists = await prisma.specialistProfile.findMany({
        where: { practiceId: req.params.id },
        include: {
          user: {
            select: {
              id: true,
              firstName: true,
              lastName: true,
              email: true,
              phone: true,
              status: true,
              createdAt: true
            }
          }
        },
        skip: role === 'SPECIALIST' ? parseInt(skip) : 0,
        take: role === 'SPECIALIST' ? parseInt(limit) : undefined
      });

      users = [...users, ...specialists.map(s => ({ ...s.user, profile: s, role: 'SPECIALIST' }))];
      
      if (!role) {
        total += await prisma.specialistProfile.count({ where: { practiceId: req.params.id } });
      } else if (role === 'SPECIALIST') {
        total = await prisma.specialistProfile.count({ where: { practiceId: req.params.id } });
      }
    }

    if (!role || role === 'ADMIN') {
      const admins = await prisma.adminProfile.findMany({
        where: { practiceId: req.params.id },
        include: {
          user: {
            select: {
              id: true,
              firstName: true,
              lastName: true,
              email: true,
              phone: true,
              status: true,
              createdAt: true
            }
          }
        },
        skip: role === 'ADMIN' ? parseInt(skip) : 0,
        take: role === 'ADMIN' ? parseInt(limit) : undefined
      });

      users = [...users, ...admins.map(a => ({ ...a.user, profile: a, role: 'ADMIN' }))];
      
      if (!role) {
        total += await prisma.adminProfile.count({ where: { practiceId: req.params.id } });
      } else if (role === 'ADMIN') {
        total = await prisma.adminProfile.count({ where: { practiceId: req.params.id } });
      }
    }

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
    console.error('Get practice users error:', error);
    res.status(500).json({ message: 'Failed to get practice users' });
  }
});

// Add user to practice
router.post('/:id/users', [
  body('userId').isString().notEmpty(),
  body('role').isIn(['DENTIST', 'SPECIALIST', 'ADMIN']),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    // Check if user has permission to add users to this practice
    const practice = await prisma.practice.findUnique({
      where: { id: req.params.id }
    });

    if (!practice) {
      return res.status(404).json({ message: 'Practice not found' });
    }

    const userProfile = await prisma.user.findUnique({
      where: { id: req.user.userId },
      include: {
        adminProfile: true
      }
    });

    const hasPermission = req.user.role === 'SUPER_ADMIN' ||
      (userProfile.adminProfile?.practiceId === practice.id && 
       userProfile.adminProfile?.permissions?.includes('MANAGE_USERS'));

    if (!hasPermission) {
      return res.status(403).json({ message: 'Insufficient permissions to add users to this practice' });
    }

    const { userId, role } = req.body;

    // Verify the user exists
    const targetUser = await prisma.user.findUnique({
      where: { id: userId }
    });

    if (!targetUser) {
      return res.status(404).json({ message: 'User not found' });
    }

    // Update or create the appropriate profile
    let updatedProfile;

    if (role === 'DENTIST') {
      updatedProfile = await prisma.dentistProfile.upsert({
        where: { userId },
        update: { practiceId: req.params.id },
        create: {
          userId,
          practiceId: req.params.id,
          dentistCode: `D${Math.random().toString().substr(2, 6)}`,
          licenseNumber: `TEMP_${userId}`
        }
      });
    } else if (role === 'SPECIALIST') {
      updatedProfile = await prisma.specialistProfile.upsert({
        where: { userId },
        update: { practiceId: req.params.id },
        create: {
          userId,
          practiceId: req.params.id,
          specialistCode: `S${Math.random().toString().substr(2, 6)}`,
          licenseNumber: `TEMP_${userId}`,
          specialization: ''
        }
      });
    } else if (role === 'ADMIN') {
      updatedProfile = await prisma.adminProfile.upsert({
        where: { userId },
        update: { practiceId: req.params.id },
        create: {
          userId,
          practiceId: req.params.id,
          permissions: ['VIEW_PRACTICE']
        }
      });
    }

    // Update user role if necessary
    if (targetUser.role !== role) {
      await prisma.user.update({
        where: { id: userId },
        data: { role }
      });
    }

    // Audit log
    await auditLog('ADD_USER_TO_PRACTICE', 'PRACTICE', practice.id, null, { userId, role }, req.ip, req.get('User-Agent'));

    res.json({ message: 'User added to practice successfully', profile: updatedProfile });
  } catch (error) {
    console.error('Add user to practice error:', error);
    res.status(500).json({ message: 'Failed to add user to practice' });
  }
});

export default router;