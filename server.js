const express = require('express');
const path = require('path');
const cors = require('cors');
const helmet = require('helmet');
require('dotenv').config();

// Import database service
const DatabaseService = require('./backend/config/database.js');

// Create Express app
const app = express();
const PORT = process.env.PORT || 3000;

// Security middleware
app.use(helmet({
    contentSecurityPolicy: false,
    crossOriginEmbedderPolicy: false
}));
app.use(cors());

// Basic middleware
app.use(express.static(path.join(__dirname, 'frontend/public')));
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));

// Health check endpoint with database status
app.get('/api/health', async (req, res) => {
    try {
        const dbHealth = await DatabaseService.healthCheck();
        
        res.json({ 
            status: 'ok', 
            message: 'Sapyyn Platform is running!',
            timestamp: new Date().toISOString(),
            environment: process.env.NODE_ENV || 'development',
            version: '1.0.0',
            database: dbHealth
        });
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: 'Health check failed',
            error: error.message
        });
    }
});

// Database status endpoint
app.get('/api/database/status', async (req, res) => {
    try {
        const dbHealth = await DatabaseService.healthCheck();
        res.json(dbHealth);
    } catch (error) {
        res.status(500).json({
            status: 'error',
            message: 'Database status check failed',
            error: error.message
        });
    }
});

// API routes
app.get('/api/status', (req, res) => {
    res.json({
        server: 'running',
        uptime: process.uptime(),
        memory: process.memoryUsage(),
        pid: process.pid,
        database: DatabaseService.isConnected ? 'connected' : 'disconnected'
    });
});

// Frontend routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'frontend/public/index.html'));
});

app.get('/portal', (req, res) => {
    res.sendFile(path.join(__dirname, 'frontend/public/portal.html'));
});

app.get('/admin', (req, res) => {
    res.sendFile(path.join(__dirname, 'frontend/public/admin.html'));
});

// API endpoints
app.post('/api/referrals', async (req, res) => {
    try {
        res.json({ 
            message: 'Referral received successfully', 
            data: req.body,
            saved: DatabaseService.isConnected 
        });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

// Catch-all for SPA routing
app.get('*', (req, res) => {
    if (req.path.startsWith('/api/')) {
        res.status(404).json({ 
            error: 'API endpoint not found',
            path: req.path
        });
    } else {
        res.sendFile(path.join(__dirname, 'frontend/public/index.html'));
    }
});

// Error handling middleware
app.use((error, req, res, next) => {
    console.error('Server error:', error);
    res.status(500).json({ 
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'production' ? 'Something went wrong' : error.message
    });
});

// Initialize database and start server
async function startServer() {
    try {
        if (process.env.MONGODB_URI) {
            console.log('🔌 Connecting to MongoDB Atlas...');
            await DatabaseService.connect();
            await DatabaseService.initializeDatabase();
        } else {
            console.warn('⚠️ MongoDB URI not found - running without database');
        }

        app.listen(PORT, () => {
            console.log('🏥 Sapyyn Platform Started Successfully!');
            console.log(`🌐 Server running on port: ${PORT}`);
            console.log(`📊 Health check: http://localhost:${PORT}/api/health`);
            console.log('✅ Server ready with MongoDB Atlas integration!');
        });
    } catch (error) {
        console.error('❌ Failed to start server:', error);
        process.exit(1);
    }
}

// Handle uncaught exceptions
process.on('uncaughtException', (error) => {
    console.error('Uncaught Exception:', error);
    process.exit(1);
});

process.on('unhandledRejection', (error) => {
    console.error('Unhandled Rejection:', error);
    process.exit(1);
});

startServer();
module.exports = app;
