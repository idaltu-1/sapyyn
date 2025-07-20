const express = require('express');
const cors = require('cors');
const path = require('path');
const DatabaseService = require('./backend/config/database');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors({
    origin: [
        'http://localhost:3000',
        'http://localhost:3001', 
        'https://www.sapyyn.io',
        'https://sapyyn.io',
        'https://sapyyn-app-5465ab15434a.herokuapp.com'
    ],
    credentials: true
}));

app.use(express.json({ limit: '50mb' }));
app.use(express.urlencoded({ extended: true, limit: '50mb' }));

// Serve static files from frontend build
app.use(express.static(path.join(__dirname, 'frontend/build')));

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({
        status: 'OK',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        environment: process.env.NODE_ENV || 'development'
    });
});

// Database status endpoint
app.get('/api/database/status', (req, res) => {
    const status = DatabaseService.getStatus();
    res.json({
        database: status,
        timestamp: new Date().toISOString()
    });
});

// Demo API endpoints (working without database)
app.get('/api/demo', (req, res) => {
    res.json({
        message: 'Sapyyn Platform Demo API',
        status: 'operational',
        features: [
            'User Authentication',
            'Content Management', 
            'Analytics Dashboard',
            'Real-time Updates'
        ]
    });
});

// Catch-all handler: send back frontend's index.html file
app.get('*', (req, res) => {
    res.sendFile(path.join(__dirname, 'frontend/build', 'index.html'));
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error('❌ Server Error:', err.stack);
    res.status(500).json({
        error: 'Internal Server Error',
        message: process.env.NODE_ENV === 'development' ? err.message : 'Something went wrong!'
    });
});

// Start server function
async function startServer() {
    try {
        // Try to connect to database (won't fail if it doesn't work)
        await DatabaseService.connect();
        
        app.listen(PORT, () => {
            console.log(`🚀 Server started on port ${PORT}`);
            console.log(`🌐 Environment: ${process.env.NODE_ENV || 'development'}`);
            console.log(`📱 Frontend URL: ${process.env.FRONTEND_URL || 'http://localhost:3000'}`);
        });
        
    } catch (error) {
        console.error('❌ Failed to start server:', error.message);
        process.exit(1);
    }
}

// Handle process termination
process.on('SIGTERM', async () => {
    console.log('📴 SIGTERM received, shutting down gracefully...');
    await DatabaseService.disconnect();
    process.exit(0);
});

process.on('SIGINT', async () => {
    console.log('📴 SIGINT received, shutting down gracefully...');
    await DatabaseService.disconnect();
    process.exit(0);
});

// Start the server
startServer();
