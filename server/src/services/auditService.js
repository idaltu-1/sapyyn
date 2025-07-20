import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

export const auditLog = async (action, resource, resourceId, oldData, newData, ipAddress, userAgent, userId = null) => {
  try {
    await prisma.auditLog.create({
      data: {
        userId,
        action,
        resource,
        resourceId,
        oldData,
        newData,
        ipAddress,
        userAgent
      }
    });
  } catch (error) {
    console.error('Audit log error:', error);
  }
};