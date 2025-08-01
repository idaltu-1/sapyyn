import express from 'express';
import { body, validationResult } from 'express-validator';
import { PrismaClient } from '@prisma/client';
import { auditLog } from '../services/auditService.js';

const router = express.Router();
const prisma = new PrismaClient();

// Create a new referral
router.post('/', [
  body('toUserId').isString().notEmpty(),
  body('patientData').isObject(),
  body('clinicalData').isObject(),
  body('urgency').optional().isIn(['LOW', 'NORMAL', 'HIGH', 'URGENT']),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { toUserId, patientData, clinicalData, urgency = 'NORMAL', scheduledAt, notes } = req.body;

    // Verify the recipient exists and is a specialist
    const recipient = await prisma.user.findUnique({
      where: { id: toUserId },
      include: { specialistProfile: true }
    });

    if (!recipient) {
      return res.status(404).json({ message: 'Recipient not found' });
    }

    if (recipient.role !== 'SPECIALIST') {
      return res.status(400).json({ message: 'Referrals can only be sent to specialists' });
    }

    // Generate unique referral number
    const referralNumber = `REF-${Date.now()}-${Math.random().toString(36).substr(2, 6).toUpperCase()}`;

    const referral = await prisma.referral.create({
      data: {
        referralNumber,
        fromUserId: req.user.userId,
        toUserId,
        patientData,
        clinicalData,
        urgency,
        scheduledAt: scheduledAt ? new Date(scheduledAt) : null,
        notes,
        statusHistory: [{
          status: 'PENDING',
          timestamp: new Date(),
          note: 'Referral created'
        }]
      },
      include: {
        fromUser: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            email: true,
            role: true,
            dentistProfile: {
              select: {
                dentistCode: true,
                practice: {
                  select: { name: true, phone: true }
                }
              }
            }
          }
        },
        toUser: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            email: true,
            role: true,
            specialistProfile: {
              select: {
                specialistCode: true,
                specialization: true,
                practice: {
                  select: { name: true, phone: true }
                }
              }
            }
          }
        }
      }
    });

    // Create notification for recipient
    await prisma.notification.create({
      data: {
        userId: toUserId,
        title: 'New Referral Received',
        message: `You have received a new referral from Dr. ${req.user.firstName} ${req.user.lastName}`,
        type: 'INFO',
        category: 'REFERRAL',
        data: { referralId: referral.id }
      }
    });

    // Audit log
    await auditLog('CREATE_REFERRAL', 'REFERRAL', referral.id, null, referral, req.ip, req.get('User-Agent'));

    res.status(201).json(referral);
  } catch (error) {
    console.error('Create referral error:', error);
    res.status(500).json({ message: 'Failed to create referral' });
  }
});

// Get referrals (sent and received)
router.get('/', async (req, res) => {
  try {
    const { type = 'all', status, page = 1, limit = 20 } = req.query;
    const skip = (page - 1) * limit;

    let whereClause = {};
    
    if (type === 'sent') {
      whereClause.fromUserId = req.user.userId;
    } else if (type === 'received') {
      whereClause.toUserId = req.user.userId;
    } else {
      whereClause.OR = [
        { fromUserId: req.user.userId },
        { toUserId: req.user.userId }
      ];
    }

    if (status) {
      whereClause.status = status;
    }

    const referrals = await prisma.referral.findMany({
      where: whereClause,
      include: {
        fromUser: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            email: true,
            role: true,
            dentistProfile: {
              select: {
                dentistCode: true,
                practice: {
                  select: { name: true, phone: true }
                }
              }
            }
          }
        },
        toUser: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            email: true,
            role: true,
            specialistProfile: {
              select: {
                specialistCode: true,
                specialization: true,
                practice: {
                  select: { name: true, phone: true }
                }
              }
            }
          }
        },
        documents: {
          select: {
            id: true,
            fileName: true,
            originalName: true,
            documentType: true,
            createdAt: true
          }
        },
        _count: {
          select: { messages: true }
        }
      },
      orderBy: { createdAt: 'desc' },
      skip: parseInt(skip),
      take: parseInt(limit)
    });

    const total = await prisma.referral.count({ where: whereClause });

    res.json({
      referrals,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    console.error('Get referrals error:', error);
    res.status(500).json({ message: 'Failed to get referrals' });
  }
});

// Get a specific referral
router.get('/:id', async (req, res) => {
  try {
    const referral = await prisma.referral.findFirst({
      where: {
        id: req.params.id,
        OR: [
          { fromUserId: req.user.userId },
          { toUserId: req.user.userId }
        ]
      },
      include: {
        fromUser: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            email: true,
            role: true,
            dentistProfile: {
              select: {
                dentistCode: true,
                practice: {
                  select: { name: true, phone: true, address: true, city: true, state: true }
                }
              }
            }
          }
        },
        toUser: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            email: true,
            role: true,
            specialistProfile: {
              select: {
                specialistCode: true,
                specialization: true,
                practice: {
                  select: { name: true, phone: true, address: true, city: true, state: true }
                }
              }
            }
          }
        },
        documents: true,
        messages: {
          include: {
            sender: {
              select: {
                id: true,
                firstName: true,
                lastName: true,
                role: true
              }
            }
          },
          orderBy: { createdAt: 'asc' }
        }
      }
    });

    if (!referral) {
      return res.status(404).json({ message: 'Referral not found' });
    }

    res.json(referral);
  } catch (error) {
    console.error('Get referral error:', error);
    res.status(500).json({ message: 'Failed to get referral' });
  }
});

// Update referral status
router.put('/:id/status', [
  body('status').isIn(['PENDING', 'ACCEPTED', 'REJECTED', 'COMPLETED', 'CANCELLED']),
  body('note').optional().trim(),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { status, note } = req.body;

    // Get the current referral
    const currentReferral = await prisma.referral.findFirst({
      where: {
        id: req.params.id,
        OR: [
          { fromUserId: req.user.userId },
          { toUserId: req.user.userId }
        ]
      }
    });

    if (!currentReferral) {
      return res.status(404).json({ message: 'Referral not found' });
    }

    // Update status history
    const newStatusEntry = {
      status,
      timestamp: new Date(),
      note: note || `Status changed to ${status}`,
      userId: req.user.userId
    };

    const updatedStatusHistory = [...(currentReferral.statusHistory || []), newStatusEntry];

    const referral = await prisma.referral.update({
      where: { id: req.params.id },
      data: {
        status,
        statusHistory: updatedStatusHistory,
        completedAt: status === 'COMPLETED' ? new Date() : null
      },
      include: {
        fromUser: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            email: true
          }
        },
        toUser: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            email: true
          }
        }
      }
    });

    // Create notification for the other party
    const notificationUserId = referral.fromUserId === req.user.userId ? referral.toUserId : referral.fromUserId;
    const notificationUser = referral.fromUserId === req.user.userId ? referral.toUser : referral.fromUser;

    await prisma.notification.create({
      data: {
        userId: notificationUserId,
        title: 'Referral Status Updated',
        message: `Referral ${referral.referralNumber} status changed to ${status}`,
        type: 'INFO',
        category: 'REFERRAL',
        data: { referralId: referral.id, status }
      }
    });

    // Audit log
    await auditLog('UPDATE_REFERRAL_STATUS', 'REFERRAL', referral.id, currentReferral, { status, note }, req.ip, req.get('User-Agent'));

    res.json(referral);
  } catch (error) {
    console.error('Update referral status error:', error);
    res.status(500).json({ message: 'Failed to update referral status' });
  }
});

// Add a message to referral
router.post('/:id/messages', [
  body('content').trim().isLength({ min: 1 }),
  body('messageType').optional().isIn(['TEXT', 'FILE', 'IMAGE']),
], async (req, res) => {
  try {
    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    // Verify user has access to this referral
    const referral = await prisma.referral.findFirst({
      where: {
        id: req.params.id,
        OR: [
          { fromUserId: req.user.userId },
          { toUserId: req.user.userId }
        ]
      }
    });

    if (!referral) {
      return res.status(404).json({ message: 'Referral not found' });
    }

    const { content, messageType = 'TEXT', attachments = [] } = req.body;

    const message = await prisma.message.create({
      data: {
        referralId: req.params.id,
        senderId: req.user.userId,
        content,
        messageType,
        attachments
      },
      include: {
        sender: {
          select: {
            id: true,
            firstName: true,
            lastName: true,
            role: true
          }
        }
      }
    });

    // Create notification for the other party
    const recipientId = referral.fromUserId === req.user.userId ? referral.toUserId : referral.fromUserId;
    
    await prisma.notification.create({
      data: {
        userId: recipientId,
        title: 'New Message',
        message: `New message in referral ${referral.referralNumber}`,
        type: 'INFO',
        category: 'REFERRAL',
        data: { referralId: referral.id, messageId: message.id }
      }
    });

    // Audit log
    await auditLog('ADD_MESSAGE', 'MESSAGE', message.id, null, message, req.ip, req.get('User-Agent'));

    res.status(201).json(message);
  } catch (error) {
    console.error('Add message error:', error);
    res.status(500).json({ message: 'Failed to add message' });
  }
});

// Mark messages as read
router.put('/:id/messages/read', async (req, res) => {
  try {
    // Verify user has access to this referral
    const referral = await prisma.referral.findFirst({
      where: {
        id: req.params.id,
        OR: [
          { fromUserId: req.user.userId },
          { toUserId: req.user.userId }
        ]
      }
    });

    if (!referral) {
      return res.status(404).json({ message: 'Referral not found' });
    }

    // Mark all unread messages from other users as read
    await prisma.message.updateMany({
      where: {
        referralId: req.params.id,
        senderId: { not: req.user.userId },
        isRead: false
      },
      data: {
        isRead: true,
        readAt: new Date()
      }
    });

    res.json({ message: 'Messages marked as read' });
  } catch (error) {
    console.error('Mark messages read error:', error);
    res.status(500).json({ message: 'Failed to mark messages as read' });
  }
});

export default router;