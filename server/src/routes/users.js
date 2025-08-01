import express from 'express';
import { body, validationResult } from 'express-validator';
import { PrismaClient } from '@prisma/client';
import bcrypt from 'bcryptjs';
import { auditLog } from '../services/auditService.js';

const router = express.Router();
const prisma = new PrismaClient();

// Get current user profile
router.get('/profile', async (req, res) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.user.userId },
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
    console.error('Get profile error:', error);
    res.status(500).json({ message: 'Failed to get user profile' });
  }
});

// Update user profile
router.put('/profile', [
  body('firstName').optional().trim().isLength({ min: 1 }),
  body('lastName').optional().trim().isLength({ min: 1 }),
  body('phone').optional().trim(),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { firstName, lastName, phone } = req.body;
    const updateData = {};

    if (firstName) updateData.firstName = firstName;
    if (lastName) updateData.lastName = lastName;
    if (phone) updateData.phone = phone;

    const user = await prisma.user.update({
      where: { id: req.user.userId },
      data: updateData,
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
        }
      }
    });

    // Remove sensitive information
    const { password, resetPasswordToken, verificationToken, ...userProfile } = user;

    // Audit log
    await auditLog('UPDATE_PROFILE', 'USER', user.id, null, updateData, req.ip, req.get('User-Agent'));

    res.json(userProfile);
  } catch (error) {
    console.error('Update profile error:', error);
    res.status(500).json({ message: 'Failed to update user profile' });
  }
});

// Update patient profile
router.put('/patient-profile', [
  body('dateOfBirth').optional().isISO8601(),
  body('gender').optional().trim(),
  body('address').optional().trim(),
  body('city').optional().trim(),
  body('state').optional().trim(),
  body('zipCode').optional().trim(),
  body('emergencyContact').optional().trim(),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { dateOfBirth, gender, address, city, state, zipCode, emergencyContact, medicalHistory, insuranceInfo } = req.body;

    const profile = await prisma.patientProfile.upsert({
      where: { userId: req.user.userId },
      update: {
        dateOfBirth: dateOfBirth ? new Date(dateOfBirth) : undefined,
        gender,
        address,
        city,
        state,
        zipCode,
        emergencyContact,
        medicalHistory,
        insuranceInfo
      },
      create: {
        userId: req.user.userId,
        dateOfBirth: dateOfBirth ? new Date(dateOfBirth) : null,
        gender,
        address,
        city,
        state,
        zipCode,
        emergencyContact,
        medicalHistory,
        insuranceInfo
      }
    });

    // Audit log
    await auditLog('UPDATE_PATIENT_PROFILE', 'PATIENT_PROFILE', profile.id, null, req.body, req.ip, req.get('User-Agent'));

    res.json(profile);
  } catch (error) {
    console.error('Update patient profile error:', error);
    res.status(500).json({ message: 'Failed to update patient profile' });
  }
});

// Update dentist profile
router.put('/dentist-profile', [
  body('licenseNumber').optional().trim().isLength({ min: 1 }),
  body('specializations').optional().isArray(),
  body('yearsExperience').optional().isInt({ min: 0 }),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { licenseNumber, practiceId, specializations, yearsExperience, education, certifications } = req.body;

    const profile = await prisma.dentistProfile.upsert({
      where: { userId: req.user.userId },
      update: {
        licenseNumber,
        practiceId,
        specializations,
        yearsExperience,
        education,
        certifications
      },
      create: {
        userId: req.user.userId,
        licenseNumber: licenseNumber || `TEMP_${req.user.userId}`,
        dentistCode: `D${Math.random().toString().substr(2, 6)}`, // Will be generated properly by service
        practiceId,
        specializations: specializations || [],
        yearsExperience,
        education,
        certifications: certifications || []
      },
      include: { practice: true }
    });

    // Audit log
    await auditLog('UPDATE_DENTIST_PROFILE', 'DENTIST_PROFILE', profile.id, null, req.body, req.ip, req.get('User-Agent'));

    res.json(profile);
  } catch (error) {
    console.error('Update dentist profile error:', error);
    res.status(500).json({ message: 'Failed to update dentist profile' });
  }
});

// Update specialist profile
router.put('/specialist-profile', [
  body('licenseNumber').optional().trim().isLength({ min: 1 }),
  body('specialization').optional().trim().isLength({ min: 1 }),
  body('subSpecializations').optional().isArray(),
  body('yearsExperience').optional().isInt({ min: 0 }),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { licenseNumber, practiceId, specialization, subSpecializations, yearsExperience, education, certifications } = req.body;

    const profile = await prisma.specialistProfile.upsert({
      where: { userId: req.user.userId },
      update: {
        licenseNumber,
        practiceId,
        specialization,
        subSpecializations,
        yearsExperience,
        education,
        certifications
      },
      create: {
        userId: req.user.userId,
        licenseNumber: licenseNumber || `TEMP_${req.user.userId}`,
        specialistCode: `S${Math.random().toString().substr(2, 6)}`, // Will be generated properly by service
        practiceId,
        specialization: specialization || '',
        subSpecializations: subSpecializations || [],
        yearsExperience,
        education,
        certifications: certifications || []
      },
      include: { practice: true }
    });

    // Audit log
    await auditLog('UPDATE_SPECIALIST_PROFILE', 'SPECIALIST_PROFILE', profile.id, null, req.body, req.ip, req.get('User-Agent'));

    res.json(profile);
  } catch (error) {
    console.error('Update specialist profile error:', error);
    res.status(500).json({ message: 'Failed to update specialist profile' });
  }
});

// Change password
router.put('/change-password', [
  body('currentPassword').isLength({ min: 1 }),
  body('newPassword').isLength({ min: 8 }),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { currentPassword, newPassword } = req.body;

    const user = await prisma.user.findUnique({
      where: { id: req.user.userId }
    });

    if (!user) {
      return res.status(404).json({ message: 'User not found' });
    }

    const isCurrentPasswordValid = await bcrypt.compare(currentPassword, user.password);
    if (!isCurrentPasswordValid) {
      return res.status(400).json({ message: 'Current password is incorrect' });
    }

    const hashedNewPassword = await bcrypt.hash(newPassword, parseInt(process.env.BCRYPT_ROUNDS) || 12);

    await prisma.user.update({
      where: { id: req.user.userId },
      data: { password: hashedNewPassword }
    });

    // Audit log
    await auditLog('CHANGE_PASSWORD', 'USER', user.id, null, null, req.ip, req.get('User-Agent'));

    res.json({ message: 'Password changed successfully' });
  } catch (error) {
    console.error('Change password error:', error);
    res.status(500).json({ message: 'Failed to change password' });
  }
});

// Get user notifications
router.get('/notifications', async (req, res) => {
  try {
    const { page = 1, limit = 20 } = req.query;
    const skip = (page - 1) * limit;

    const notifications = await prisma.notification.findMany({
      where: { userId: req.user.userId },
      orderBy: { createdAt: 'desc' },
      skip: parseInt(skip),
      take: parseInt(limit)
    });

    const total = await prisma.notification.count({
      where: { userId: req.user.userId }
    });

    res.json({
      notifications,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    console.error('Get notifications error:', error);
    res.status(500).json({ message: 'Failed to get notifications' });
  }
});

// Mark notification as read
router.put('/notifications/:id/read', async (req, res) => {
  try {
    const notification = await prisma.notification.update({
      where: { 
        id: req.params.id,
        userId: req.user.userId 
      },
      data: { 
        isRead: true,
        readAt: new Date()
      }
    });

    res.json(notification);
  } catch (error) {
    console.error('Mark notification read error:', error);
    res.status(500).json({ message: 'Failed to mark notification as read' });
  }
});

export default router;