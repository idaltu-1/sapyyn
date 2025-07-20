import express from 'express';
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { body, validationResult } from 'express-validator';
import { PrismaClient } from '@prisma/client';
import { generateCode } from '../utils/codeGenerator.js';
import { sendEmail } from '../services/emailService.js';
import { auditLog } from '../services/auditService.js';

const router = express.Router();
const prisma = new PrismaClient();

// Register
router.post('/register', [
  body('email').isEmail().normalizeEmail(),
  body('password').isLength({ min: 8 }),
  body('firstName').trim().isLength({ min: 1 }),
  body('lastName').trim().isLength({ min: 1 }),
  body('role').isIn(['PATIENT', 'DENTIST', 'SPECIALIST']),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { email, password, firstName, lastName, role, phone } = req.body;

    // Check if user exists
    const existingUser = await prisma.user.findUnique({
      where: { email }
    });

    if (existingUser) {
      return res.status(400).json({ message: 'User already exists with this email' });
    }

    // Hash password
    const hashedPassword = await bcrypt.hash(password, parseInt(process.env.BCRYPT_ROUNDS) || 12);

    // Generate verification token
    const verificationToken = jwt.sign({ email }, process.env.JWT_SECRET, { expiresIn: '24h' });

    // Create user
    const user = await prisma.user.create({
      data: {
        email,
        password: hashedPassword,
        firstName,
        lastName,
        phone,
        role,
        verificationToken
      }
    });

    // Create profile based on role
    let profile = null;
    if (role === 'PATIENT') {
      profile = await prisma.patientProfile.create({
        data: { userId: user.id }
      });
    } else if (role === 'DENTIST') {
      const dentistCode = await generateCode('DENTIST');
      profile = await prisma.dentistProfile.create({
        data: { 
          userId: user.id,
          dentistCode,
          licenseNumber: `TEMP_${user.id}` // Will be updated later
        }
      });
    } else if (role === 'SPECIALIST') {
      const specialistCode = await generateCode('SPECIALIST');
      profile = await prisma.specialistProfile.create({
        data: { 
          userId: user.id,
          specialistCode,
          licenseNumber: `TEMP_${user.id}` // Will be updated later
        }
      });
    }

    // Send verification email
    await sendEmail(
      email,
      'Welcome to Sapyyn - Please Verify Your Account',
      `Please click the following link to verify your account: ${process.env.MAIN_WEBSITE_URL}/verify?token=${verificationToken}`
    );

    // Audit log
    await auditLog('REGISTER', 'USER', user.id, null, { email, role }, req.ip, req.get('User-Agent'));

    res.status(201).json({
      message: 'User registered successfully. Please check your email to verify your account.',
      userId: user.id
    });

  } catch (error) {
    console.error('Registration error:', error);
    res.status(500).json({ message: 'Registration failed' });
  }
});

// Login
router.post('/login', [
  body('email').isEmail().normalizeEmail(),
  body('password').exists(),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { email, password } = req.body;

    // Find user with profile data
    const user = await prisma.user.findUnique({
      where: { email },
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
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    if (user.status !== 'ACTIVE') {
      return res.status(401).json({ message: 'Account not active. Please verify your email.' });
    }

    // Check password
    const isPasswordValid = await bcrypt.compare(password, user.password);
    if (!isPasswordValid) {
      return res.status(401).json({ message: 'Invalid credentials' });
    }

    // Update last login
    await prisma.user.update({
      where: { id: user.id },
      data: { lastLoginAt: new Date() }
    });

    // Generate JWT
    const token = jwt.sign(
      { 
        userId: user.id, 
        email: user.email, 
        role: user.role 
      }, 
      process.env.JWT_SECRET, 
      { expiresIn: process.env.JWT_EXPIRE || '7d' }
    );

    // Audit log
    await auditLog('LOGIN', 'USER', user.id, null, null, req.ip, req.get('User-Agent'));

    res.json({
      token,
      user: {
        id: user.id,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        role: user.role,
        status: user.status,
        profile: user.patientProfile || user.dentistProfile || user.specialistProfile || user.adminProfile
      }
    });

  } catch (error) {
    console.error('Login error:', error);
    res.status(500).json({ message: 'Login failed' });
  }
});

// Verify email
router.post('/verify', [
  body('token').exists(),
], async (req, res) => {
  try {
    const { token } = req.body;

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    
    const user = await prisma.user.findUnique({
      where: { email: decoded.email }
    });

    if (!user || user.verificationToken !== token) {
      return res.status(400).json({ message: 'Invalid verification token' });
    }

    await prisma.user.update({
      where: { id: user.id },
      data: {
        status: 'ACTIVE',
        verificationToken: null
      }
    });

    res.json({ message: 'Account verified successfully' });

  } catch (error) {
    console.error('Verification error:', error);
    res.status(400).json({ message: 'Invalid or expired verification token' });
  }
});

// Forgot password
router.post('/forgot-password', [
  body('email').isEmail().normalizeEmail(),
], async (req, res) => {
  try {
    const { email } = req.body;

    const user = await prisma.user.findUnique({
      where: { email }
    });

    if (!user) {
      // Don't reveal if user exists
      return res.json({ message: 'If an account with that email exists, we sent a password reset link.' });
    }

    const resetToken = jwt.sign({ userId: user.id }, process.env.JWT_SECRET, { expiresIn: '1h' });
    const resetExpires = new Date(Date.now() + 3600000); // 1 hour

    await prisma.user.update({
      where: { id: user.id },
      data: {
        resetPasswordToken: resetToken,
        resetPasswordExpires: resetExpires
      }
    });

    await sendEmail(
      email,
      'Sapyyn - Password Reset Request',
      `Please click the following link to reset your password: ${process.env.MAIN_WEBSITE_URL}/reset-password?token=${resetToken}`
    );

    res.json({ message: 'If an account with that email exists, we sent a password reset link.' });

  } catch (error) {
    console.error('Forgot password error:', error);
    res.status(500).json({ message: 'Failed to process request' });
  }
});

// Reset password
router.post('/reset-password', [
  body('token').exists(),
  body('password').isLength({ min: 8 }),
], async (req, res) => {
  try {
    const { token, password } = req.body;

    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    
    const user = await prisma.user.findUnique({
      where: { id: decoded.userId }
    });

    if (!user || user.resetPasswordToken !== token || user.resetPasswordExpires < new Date()) {
      return res.status(400).json({ message: 'Invalid or expired reset token' });
    }

    const hashedPassword = await bcrypt.hash(password, parseInt(process.env.BCRYPT_ROUNDS) || 12);

    await prisma.user.update({
      where: { id: user.id },
      data: {
        password: hashedPassword,
        resetPasswordToken: null,
        resetPasswordExpires: null
      }
    });

    res.json({ message: 'Password reset successfully' });

  } catch (error) {
    console.error('Reset password error:', error);
    res.status(400).json({ message: 'Invalid or expired reset token' });
  }
});

export default router;