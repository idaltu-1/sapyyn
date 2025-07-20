import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import { createServer } from 'http';
import { Server } from 'socket.io';
import dotenv from 'dotenv';

// Import routes
import authRoutes from './routes/auth.js';
import userRoutes from './routes/users.js';
import referralRoutes from './routes/referrals.js';
import documentRoutes from './routes/documents.js';
import practiceRoutes from './routes/practices.js';
import rewardRoutes from './routes/rewards.js';
import integrationRoutes from './routes/integrations.js';
import adminRoutes from './routes/admin.js';

// Import middleware
import { authenticateToken } from './middleware/auth.js';
import { errorHandler } from './middleware/errorHandler.js';
import { setupSocketIO } from './services/socketService.js';

// Load environment variables
dotenv.config();

const app = express();
const server = createServer(app);
const io = new Server(server, {
  cors: {
    origin: [
      process.env.MAIN_WEBSITE_URL || 'http://localhost:3000',
      process.env.PORTAL_URL || 'http://localhost:3001',
      process.env.ADMIN_URL || 'http://localhost:3002'
    ],
    credentials: true
  }
});

const PORT = process.env.PORT || 5000;

// Rate limiting
const limiter = rateLimit({
  windowMs: parseInt(process.env.RATE_LIMIT_WINDOW_MS) || 15 * 60 * 1000, // 15 minutes
  max: parseInt(process.env.RATE_LIMIT_MAX_REQUESTS) || 100, // limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});

// Middleware
app.use(helmet());
app.use(compression());
app.use(morgan('combined'));
app.use(limiter);
app.use(cors({
  origin: [
    process.env.MAIN_WEBSITE_URL || 'http://localhost:3000',
    process.env.PORTAL_URL || 'http://localhost:3001',
    process.env.ADMIN_URL || 'http://localhost:3002'
  ],
  credentials: true
}));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Setup Socket.IO
setupSocketIO(io);

// Health check
app.get('/health', (req, res) => {
  res.json({ 
    status: 'OK', 
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// API Routes
app.use('/api/auth', authRoutes);
app.use('/api/users', authenticateToken, userRoutes);
app.use('/api/referrals', authenticateToken, referralRoutes);
app.use('/api/documents', authenticateToken, documentRoutes);
app.use('/api/practices', authenticateToken, practiceRoutes);
app.use('/api/rewards', authenticateToken, rewardRoutes);
app.use('/api/integrations', authenticateToken, integrationRoutes);
app.use('/api/admin', authenticateToken, adminRoutes);

// Serve uploaded files
app.use('/uploads', express.static('uploads'));

// Error handling middleware
app.use(errorHandler);

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ message: 'API endpoint not found' });
});

// Start server
server.listen(PORT, () => {
  console.log(`🚀 Sapyyn server running on port ${PORT}`);
  console.log(`📱 Main Website: ${process.env.MAIN_WEBSITE_URL || 'http://localhost:3000'}`);
  console.log(`🏥 Portal: ${process.env.PORTAL_URL || 'http://localhost:3001'}`);
  console.log(`⚙️ Admin: ${process.env.ADMIN_URL || 'http://localhost:3002'}`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM signal received: closing HTTP server');
  server.close(() => {
    console.log('HTTP server closed');
    process.exit(0);
  });
});

export default app;