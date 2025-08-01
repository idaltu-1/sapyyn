import express from 'express';
import multer from 'multer';
import { body, validationResult } from 'express-validator';
import { PrismaClient } from '@prisma/client';
import { auditLog } from '../services/auditService.js';
import path from 'path';
import fs from 'fs';

const router = express.Router();
const prisma = new PrismaClient();

// Configure multer for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => {
    const uploadDir = 'uploads/documents';
    if (!fs.existsSync(uploadDir)) {
      fs.mkdirSync(uploadDir, { recursive: true });
    }
    cb(null, uploadDir);
  },
  filename: (req, file, cb) => {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname));
  }
});

const fileFilter = (req, file, cb) => {
  // Allow specific file types
  const allowedTypes = /jpeg|jpg|png|gif|pdf|doc|docx|txt|csv/;
  const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
  const mimetype = allowedTypes.test(file.mimetype);

  if (mimetype && extname) {
    return cb(null, true);
  } else {
    cb(new Error('Only images, PDFs, and documents are allowed'));
  }
};

const upload = multer({
  storage,
  limits: {
    fileSize: 10 * 1024 * 1024 // 10MB limit
  },
  fileFilter
});

// Upload document
router.post('/upload', upload.single('document'), [
  body('documentType').isIn([
    'MEDICAL_REPORT',
    'INSURANCE_DOCUMENT',
    'QUALIFICATION_DOCUMENT',
    'EXPERIENCE_DOCUMENT',
    'SUPPORTING_DOCUMENT',
    'PROFILE_PICTURE',
    'BROADCAST_FILE',
    'TESTIMONIAL_IMAGE',
    'UPLOADED_FILE'
  ]),
  body('referralId').optional().isString(),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      // Clean up uploaded file if validation fails
      if (req.file) {
        fs.unlinkSync(req.file.path);
      }
      return res.status(400).json({ errors: errors.array() });
    }

    if (!req.file) {
      return res.status(400).json({ message: 'No file uploaded' });
    }

    const { documentType, referralId, metadata } = req.body;

    // If referralId is provided, verify user has access to the referral
    if (referralId) {
      const referral = await prisma.referral.findFirst({
        where: {
          id: referralId,
          OR: [
            { fromUserId: req.user.userId },
            { toUserId: req.user.userId }
          ]
        }
      });

      if (!referral) {
        // Clean up uploaded file
        fs.unlinkSync(req.file.path);
        return res.status(404).json({ message: 'Referral not found or access denied' });
      }
    }

    const document = await prisma.document.create({
      data: {
        userId: req.user.userId,
        referralId: referralId || null,
        fileName: req.file.filename,
        originalName: req.file.originalname,
        filePath: req.file.path,
        fileSize: req.file.size,
        mimeType: req.file.mimetype,
        documentType,
        metadata: metadata ? JSON.parse(metadata) : null
      }
    });

    // Audit log
    await auditLog('UPLOAD_DOCUMENT', 'DOCUMENT', document.id, null, {
      fileName: document.fileName,
      documentType,
      referralId
    }, req.ip, req.get('User-Agent'));

    res.status(201).json(document);
  } catch (error) {
    console.error('Upload document error:', error);
    // Clean up uploaded file on error
    if (req.file) {
      fs.unlinkSync(req.file.path);
    }
    res.status(500).json({ message: 'Failed to upload document' });
  }
});

// Get user's documents
router.get('/', async (req, res) => {
  try {
    const { documentType, referralId, page = 1, limit = 20 } = req.query;
    const skip = (page - 1) * limit;

    let whereClause = { userId: req.user.userId };

    if (documentType) {
      whereClause.documentType = documentType;
    }

    if (referralId) {
      whereClause.referralId = referralId;
    }

    const documents = await prisma.document.findMany({
      where: whereClause,
      include: {
        referral: {
          select: {
            id: true,
            referralNumber: true,
            fromUser: {
              select: {
                firstName: true,
                lastName: true
              }
            },
            toUser: {
              select: {
                firstName: true,
                lastName: true
              }
            }
          }
        }
      },
      orderBy: { createdAt: 'desc' },
      skip: parseInt(skip),
      take: parseInt(limit)
    });

    const total = await prisma.document.count({ where: whereClause });

    res.json({
      documents,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    console.error('Get documents error:', error);
    res.status(500).json({ message: 'Failed to get documents' });
  }
});

// Get a specific document
router.get('/:id', async (req, res) => {
  try {
    const document = await prisma.document.findFirst({
      where: {
        id: req.params.id,
        OR: [
          { userId: req.user.userId },
          {
            referral: {
              OR: [
                { fromUserId: req.user.userId },
                { toUserId: req.user.userId }
              ]
            }
          }
        ]
      },
      include: {
        user: {
          select: {
            firstName: true,
            lastName: true,
            role: true
          }
        },
        referral: {
          select: {
            id: true,
            referralNumber: true,
            fromUser: {
              select: {
                firstName: true,
                lastName: true
              }
            },
            toUser: {
              select: {
                firstName: true,
                lastName: true
              }
            }
          }
        }
      }
    });

    if (!document) {
      return res.status(404).json({ message: 'Document not found' });
    }

    res.json(document);
  } catch (error) {
    console.error('Get document error:', error);
    res.status(500).json({ message: 'Failed to get document' });
  }
});

// Download document
router.get('/:id/download', async (req, res) => {
  try {
    const document = await prisma.document.findFirst({
      where: {
        id: req.params.id,
        OR: [
          { userId: req.user.userId },
          {
            referral: {
              OR: [
                { fromUserId: req.user.userId },
                { toUserId: req.user.userId }
              ]
            }
          }
        ]
      }
    });

    if (!document) {
      return res.status(404).json({ message: 'Document not found' });
    }

    if (!fs.existsSync(document.filePath)) {
      return res.status(404).json({ message: 'File not found on disk' });
    }

    // Audit log
    await auditLog('DOWNLOAD_DOCUMENT', 'DOCUMENT', document.id, null, null, req.ip, req.get('User-Agent'));

    res.download(document.filePath, document.originalName);
  } catch (error) {
    console.error('Download document error:', error);
    res.status(500).json({ message: 'Failed to download document' });
  }
});

// Update document metadata
router.put('/:id', [
  body('documentType').optional().isIn([
    'MEDICAL_REPORT',
    'INSURANCE_DOCUMENT',
    'QUALIFICATION_DOCUMENT',
    'EXPERIENCE_DOCUMENT',
    'SUPPORTING_DOCUMENT',
    'PROFILE_PICTURE',
    'BROADCAST_FILE',
    'TESTIMONIAL_IMAGE',
    'UPLOADED_FILE'
  ]),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { documentType, metadata } = req.body;

    const document = await prisma.document.findFirst({
      where: {
        id: req.params.id,
        userId: req.user.userId
      }
    });

    if (!document) {
      return res.status(404).json({ message: 'Document not found' });
    }

    const updatedDocument = await prisma.document.update({
      where: { id: req.params.id },
      data: {
        documentType: documentType || document.documentType,
        metadata: metadata ? JSON.parse(metadata) : document.metadata
      }
    });

    // Audit log
    await auditLog('UPDATE_DOCUMENT', 'DOCUMENT', document.id, document, updatedDocument, req.ip, req.get('User-Agent'));

    res.json(updatedDocument);
  } catch (error) {
    console.error('Update document error:', error);
    res.status(500).json({ message: 'Failed to update document' });
  }
});

// Delete document
router.delete('/:id', async (req, res) => {
  try {
    const document = await prisma.document.findFirst({
      where: {
        id: req.params.id,
        userId: req.user.userId
      }
    });

    if (!document) {
      return res.status(404).json({ message: 'Document not found' });
    }

    // Delete the file from disk
    if (fs.existsSync(document.filePath)) {
      fs.unlinkSync(document.filePath);
    }

    // Delete from database
    await prisma.document.delete({
      where: { id: req.params.id }
    });

    // Audit log
    await auditLog('DELETE_DOCUMENT', 'DOCUMENT', document.id, document, null, req.ip, req.get('User-Agent'));

    res.json({ message: 'Document deleted successfully' });
  } catch (error) {
    console.error('Delete document error:', error);
    res.status(500).json({ message: 'Failed to delete document' });
  }
});

// Get documents for a referral (accessible by both parties)
router.get('/referral/:referralId', async (req, res) => {
  try {
    const { referralId } = req.params;

    // Verify user has access to this referral
    const referral = await prisma.referral.findFirst({
      where: {
        id: referralId,
        OR: [
          { fromUserId: req.user.userId },
          { toUserId: req.user.userId }
        ]
      }
    });

    if (!referral) {
      return res.status(404).json({ message: 'Referral not found or access denied' });
    }

    const documents = await prisma.document.findMany({
      where: { referralId },
      include: {
        user: {
          select: {
            firstName: true,
            lastName: true,
            role: true
          }
        }
      },
      orderBy: { createdAt: 'desc' }
    });

    res.json(documents);
  } catch (error) {
    console.error('Get referral documents error:', error);
    res.status(500).json({ message: 'Failed to get referral documents' });
  }
});

export default router;