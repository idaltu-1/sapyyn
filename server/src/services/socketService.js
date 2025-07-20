import jwt from 'jsonwebtoken';
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
let io;

export const setupSocketIO = (socketIO) => {
  io = socketIO;

  io.use(async (socket, next) => {
    try {
      const token = socket.handshake.auth.token;
      if (!token) {
        return next(new Error('Authentication error'));
      }

      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      const user = await prisma.user.findUnique({
        where: { id: decoded.userId }
      });

      if (!user) {
        return next(new Error('User not found'));
      }

      socket.userId = user.id;
      socket.userRole = user.role;
      next();
    } catch (error) {
      next(new Error('Authentication error'));
    }
  });

  io.on('connection', (socket) => {
    console.log(`User ${socket.userId} connected`);

    // Join user to their own room
    socket.join(`user_${socket.userId}`);

    // Handle referral updates
    socket.on('join_referral', (referralId) => {
      socket.join(`referral_${referralId}`);
    });

    socket.on('leave_referral', (referralId) => {
      socket.leave(`referral_${referralId}`);
    });

    socket.on('disconnect', () => {
      console.log(`User ${socket.userId} disconnected`);
    });
  });
};

export const sendNotification = (userId, notification) => {
  if (io) {
    io.to(`user_${userId}`).emit('notification', notification);
  }
};

export const sendReferralUpdate = (referralId, update) => {
  if (io) {
    io.to(`referral_${referralId}`).emit('referral_update', update);
  }
};

export const sendMessage = (referralId, message) => {
  if (io) {
    io.to(`referral_${referralId}`).emit('new_message', message);
  }
};