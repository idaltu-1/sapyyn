import express from 'express';
import { body, validationResult } from 'express-validator';
import { PrismaClient } from '@prisma/client';
import { auditLog } from '../services/auditService.js';
import crypto from 'crypto';

const router = express.Router();
const prisma = new PrismaClient();

// Encryption helper functions
const encrypt = (text) => {
  const algorithm = 'aes-256-gcm';
  const key = Buffer.from(process.env.ENCRYPTION_KEY || 'default-32-character-secret-key!', 'utf8');
  const iv = crypto.randomBytes(16);
  
  const cipher = crypto.createCipher(algorithm, key);
  let encrypted = cipher.update(text, 'utf8', 'hex');
  encrypted += cipher.final('hex');
  
  return {
    iv: iv.toString('hex'),
    encryptedData: encrypted
  };
};

const decrypt = (encryptedObj) => {
  const algorithm = 'aes-256-gcm';
  const key = Buffer.from(process.env.ENCRYPTION_KEY || 'default-32-character-secret-key!', 'utf8');
  
  const decipher = crypto.createDecipher(algorithm, key);
  let decrypted = decipher.update(encryptedObj.encryptedData, 'hex', 'utf8');
  decrypted += decipher.final('utf8');
  
  return decrypted;
};

// Get all integrations
router.get('/', async (req, res) => {
  try {
    if (!['SUPER_ADMIN', 'DENTIST_ADMIN', 'SPECIALIST_ADMIN'].includes(req.user.role)) {
      return res.status(403).json({ message: 'Insufficient permissions to view integrations' });
    }

    const { type, isActive, page = 1, limit = 20 } = req.query;
    const skip = (page - 1) * limit;

    let whereClause = {};

    if (type) {
      whereClause.type = type;
    }

    if (isActive !== undefined) {
      whereClause.isActive = isActive === 'true';
    }

    const integrations = await prisma.integration.findMany({
      where: whereClause,
      select: {
        id: true,
        name: true,
        type: true,
        config: true,
        isActive: true,
        lastSync: true,
        createdAt: true,
        updatedAt: true
        // credentials excluded for security
      },
      orderBy: { name: 'asc' },
      skip: parseInt(skip),
      take: parseInt(limit)
    });

    const total = await prisma.integration.count({ where: whereClause });

    res.json({
      integrations,
      pagination: {
        page: parseInt(page),
        limit: parseInt(limit),
        total,
        pages: Math.ceil(total / limit)
      }
    });
  } catch (error) {
    console.error('Get integrations error:', error);
    res.status(500).json({ message: 'Failed to get integrations' });
  }
});

// Get a specific integration
router.get('/:id', async (req, res) => {
  try {
    if (!['SUPER_ADMIN', 'DENTIST_ADMIN', 'SPECIALIST_ADMIN'].includes(req.user.role)) {
      return res.status(403).json({ message: 'Insufficient permissions to view integration' });
    }

    const integration = await prisma.integration.findUnique({
      where: { id: req.params.id },
      select: {
        id: true,
        name: true,
        type: true,
        config: true,
        isActive: true,
        lastSync: true,
        createdAt: true,
        updatedAt: true
        // credentials excluded for security
      }
    });

    if (!integration) {
      return res.status(404).json({ message: 'Integration not found' });
    }

    res.json(integration);
  } catch (error) {
    console.error('Get integration error:', error);
    res.status(500).json({ message: 'Failed to get integration' });
  }
});

// Create a new integration
router.post('/', [
  body('name').trim().isLength({ min: 1 }),
  body('type').isIn(['ZAPIER', 'N8N', 'SMS_IT', 'EMAIL_SERVICE', 'CALENDAR', 'PAYMENT_GATEWAY', 'CRM', 'OTHER']),
  body('config').isObject(),
  body('credentials').optional().isObject(),
], async (req, res) => {
  try {
    if (req.user.role !== 'SUPER_ADMIN') {
      return res.status(403).json({ message: 'Only super admins can create integrations' });
    }

    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const { name, type, config, credentials, isActive = true } = req.body;

    // Check if integration name already exists
    const existingIntegration = await prisma.integration.findUnique({
      where: { name }
    });

    if (existingIntegration) {
      return res.status(400).json({ message: 'Integration with this name already exists' });
    }

    // Encrypt credentials if provided
    let encryptedCredentials = null;
    if (credentials) {
      try {
        encryptedCredentials = encrypt(JSON.stringify(credentials));
      } catch (encryptError) {
        console.error('Credential encryption error:', encryptError);
        return res.status(500).json({ message: 'Failed to encrypt credentials' });
      }
    }

    const integration = await prisma.integration.create({
      data: {
        name,
        type,
        config,
        credentials: encryptedCredentials,
        isActive
      },
      select: {
        id: true,
        name: true,
        type: true,
        config: true,
        isActive: true,
        lastSync: true,
        createdAt: true,
        updatedAt: true
      }
    });

    // Audit log
    await auditLog('CREATE_INTEGRATION', 'INTEGRATION', integration.id, null, { 
      name, 
      type, 
      isActive 
    }, req.ip, req.get('User-Agent'));

    res.status(201).json(integration);
  } catch (error) {
    console.error('Create integration error:', error);
    res.status(500).json({ message: 'Failed to create integration' });
  }
});

// Update an integration
router.put('/:id', [
  body('name').optional().trim().isLength({ min: 1 }),
  body('type').optional().isIn(['ZAPIER', 'N8N', 'SMS_IT', 'EMAIL_SERVICE', 'CALENDAR', 'PAYMENT_GATEWAY', 'CRM', 'OTHER']),
  body('config').optional().isObject(),
  body('credentials').optional().isObject(),
  body('isActive').optional().isBoolean(),
], async (req, res) => {
  try {
    if (req.user.role !== 'SUPER_ADMIN') {
      return res.status(403).json({ message: 'Only super admins can update integrations' });
    }

    const errors = validationResult(req);
    if (!errors.isEmpty()) {
      return res.status(400).json({ errors: errors.array() });
    }

    const integration = await prisma.integration.findUnique({
      where: { id: req.params.id }
    });

    if (!integration) {
      return res.status(404).json({ message: 'Integration not found' });
    }

    const { name, type, config, credentials, isActive } = req.body;

    // Check if new name conflicts with existing integration
    if (name && name !== integration.name) {
      const existingIntegration = await prisma.integration.findUnique({
        where: { name }
      });

      if (existingIntegration) {
        return res.status(400).json({ message: 'Integration with this name already exists' });
      }
    }

    // Encrypt new credentials if provided
    let encryptedCredentials = integration.credentials;
    if (credentials) {
      try {
        encryptedCredentials = encrypt(JSON.stringify(credentials));
      } catch (encryptError) {
        console.error('Credential encryption error:', encryptError);
        return res.status(500).json({ message: 'Failed to encrypt credentials' });
      }
    }

    const updatedIntegration = await prisma.integration.update({
      where: { id: req.params.id },
      data: {
        ...(name && { name }),
        ...(type && { type }),
        ...(config && { config }),
        ...(credentials && { credentials: encryptedCredentials }),
        ...(isActive !== undefined && { isActive })
      },
      select: {
        id: true,
        name: true,
        type: true,
        config: true,
        isActive: true,
        lastSync: true,
        createdAt: true,
        updatedAt: true
      }
    });

    // Audit log
    await auditLog('UPDATE_INTEGRATION', 'INTEGRATION', integration.id, integration, updatedIntegration, req.ip, req.get('User-Agent'));

    res.json(updatedIntegration);
  } catch (error) {
    console.error('Update integration error:', error);
    res.status(500).json({ message: 'Failed to update integration' });
  }
});

// Delete an integration
router.delete('/:id', async (req, res) => {
  try {
    if (req.user.role !== 'SUPER_ADMIN') {
      return res.status(403).json({ message: 'Only super admins can delete integrations' });
    }

    const integration = await prisma.integration.findUnique({
      where: { id: req.params.id }
    });

    if (!integration) {
      return res.status(404).json({ message: 'Integration not found' });
    }

    await prisma.integration.delete({
      where: { id: req.params.id }
    });

    // Audit log
    await auditLog('DELETE_INTEGRATION', 'INTEGRATION', integration.id, integration, null, req.ip, req.get('User-Agent'));

    res.json({ message: 'Integration deleted successfully' });
  } catch (error) {
    console.error('Delete integration error:', error);
    res.status(500).json({ message: 'Failed to delete integration' });
  }
});

// Test integration connection
router.post('/:id/test', async (req, res) => {
  try {
    if (!['SUPER_ADMIN', 'DENTIST_ADMIN', 'SPECIALIST_ADMIN'].includes(req.user.role)) {
      return res.status(403).json({ message: 'Insufficient permissions to test integration' });
    }

    const integration = await prisma.integration.findUnique({
      where: { id: req.params.id }
    });

    if (!integration) {
      return res.status(404).json({ message: 'Integration not found' });
    }

    if (!integration.isActive) {
      return res.status(400).json({ message: 'Integration is not active' });
    }

    let testResult = { success: false, message: '', data: null };

    try {
      // Decrypt credentials if needed
      let credentials = null;
      if (integration.credentials) {
        credentials = JSON.parse(decrypt(integration.credentials));
      }

      // Mock integration testing based on type
      switch (integration.type) {
        case 'ZAPIER':
          // Mock Zapier webhook test
          testResult = {
            success: true,
            message: 'Zapier webhook connection successful',
            data: { webhook_url: integration.config.webhook_url }
          };
          break;

        case 'N8N':
          // Mock N8N workflow test
          testResult = {
            success: true,
            message: 'N8N workflow connection successful',
            data: { workflow_id: integration.config.workflow_id }
          };
          break;

        case 'SMS_IT':
          // Mock SMS service test
          testResult = {
            success: true,
            message: 'SMS service connection successful',
            data: { provider: 'SMS_IT' }
          };
          break;

        case 'EMAIL_SERVICE':
          // Mock email service test
          testResult = {
            success: true,
            message: 'Email service connection successful',
            data: { smtp_host: integration.config.smtp_host }
          };
          break;

        default:
          testResult = {
            success: true,
            message: 'Generic integration test successful',
            data: { type: integration.type }
          };
      }

      // Update last sync time on successful test
      if (testResult.success) {
        await prisma.integration.update({
          where: { id: req.params.id },
          data: { lastSync: new Date() }
        });
      }

    } catch (testError) {
      testResult = {
        success: false,
        message: `Integration test failed: ${testError.message}`,
        data: null
      };
    }

    // Audit log
    await auditLog('TEST_INTEGRATION', 'INTEGRATION', integration.id, null, testResult, req.ip, req.get('User-Agent'));

    res.json(testResult);
  } catch (error) {
    console.error('Test integration error:', error);
    res.status(500).json({ message: 'Failed to test integration' });
  }
});

// Trigger integration sync
router.post('/:id/sync', async (req, res) => {
  try {
    if (!['SUPER_ADMIN', 'DENTIST_ADMIN', 'SPECIALIST_ADMIN'].includes(req.user.role)) {
      return res.status(403).json({ message: 'Insufficient permissions to sync integration' });
    }

    const integration = await prisma.integration.findUnique({
      where: { id: req.params.id }
    });

    if (!integration) {
      return res.status(404).json({ message: 'Integration not found' });
    }

    if (!integration.isActive) {
      return res.status(400).json({ message: 'Integration is not active' });
    }

    const { data } = req.body;

    let syncResult = { success: false, message: '', syncedData: null };

    try {
      // Mock sync operation based on integration type
      switch (integration.type) {
        case 'ZAPIER':
          // Mock Zapier webhook trigger
          syncResult = {
            success: true,
            message: 'Zapier webhook triggered successfully',
            syncedData: { webhook_triggered: true, data }
          };
          break;

        case 'N8N':
          // Mock N8N workflow execution
          syncResult = {
            success: true,
            message: 'N8N workflow executed successfully',
            syncedData: { workflow_executed: true, data }
          };
          break;

        case 'SMS_IT':
          // Mock SMS sending
          syncResult = {
            success: true,
            message: 'SMS notifications sent successfully',
            syncedData: { messages_sent: 1, data }
          };
          break;

        case 'EMAIL_SERVICE':
          // Mock email sending
          syncResult = {
            success: true,
            message: 'Email notifications sent successfully',
            syncedData: { emails_sent: 1, data }
          };
          break;

        default:
          syncResult = {
            success: true,
            message: 'Generic integration sync completed',
            syncedData: { type: integration.type, data }
          };
      }

      // Update last sync time on successful sync
      if (syncResult.success) {
        await prisma.integration.update({
          where: { id: req.params.id },
          data: { lastSync: new Date() }
        });
      }

    } catch (syncError) {
      syncResult = {
        success: false,
        message: `Integration sync failed: ${syncError.message}`,
        syncedData: null
      };
    }

    // Audit log
    await auditLog('SYNC_INTEGRATION', 'INTEGRATION', integration.id, null, syncResult, req.ip, req.get('User-Agent'));

    res.json(syncResult);
  } catch (error) {
    console.error('Sync integration error:', error);
    res.status(500).json({ message: 'Failed to sync integration' });
  }
});

// Get integration types
router.get('/meta/types', async (req, res) => {
  try {
    const integrationTypes = [
      { value: 'ZAPIER', label: 'Zapier', description: 'Connect to Zapier workflows' },
      { value: 'N8N', label: 'n8n', description: 'Connect to n8n workflows' },
      { value: 'SMS_IT', label: 'SMS Service', description: 'SMS notification service' },
      { value: 'EMAIL_SERVICE', label: 'Email Service', description: 'Email notification service' },
      { value: 'CALENDAR', label: 'Calendar', description: 'Calendar integration' },
      { value: 'PAYMENT_GATEWAY', label: 'Payment Gateway', description: 'Payment processing integration' },
      { value: 'CRM', label: 'CRM System', description: 'Customer relationship management system' },
      { value: 'OTHER', label: 'Other', description: 'Custom integration' }
    ];

    res.json(integrationTypes);
  } catch (error) {
    console.error('Get integration types error:', error);
    res.status(500).json({ message: 'Failed to get integration types' });
  }
});

export default router;