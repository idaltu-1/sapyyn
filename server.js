const express = require('express');
const path = require('path');

// Create Express app
const app = express();
const PORT = process.env.PORT || 3000;

// Basic middleware
app.use(express.static(path.join(__dirname, 'frontend/public')));
app.use(express.json());

// Health check endpoint
app.get('/api/health', (req, res) => {
    res.json({ 
        status: 'ok', 
        message: 'Sapyyn Platform is running!',
        timestamp: new Date().toISOString(),
        dependencies: 'loaded'
    });
});

// Basic routes
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'frontend/public/index.html'));
});

app.get('/portal', (req, res) => {
    res.sendFile(path.join(__dirname, 'frontend/public/portal.html'));
});

app.get('/quick-referral', (req, res) => {
    res.sendFile(path.join(__dirname, 'frontend/public/quick-referral-form.html'));
});

// Fallback for SPA routing
app.get('*', (req, res) => {
    if (req.path.startsWith('/api/')) {
        res.status(404).json({ error: 'API endpoint not found' });
    } else {
        res.sendFile(path.join(__dirname, 'frontend/public/index.html'));
    }
});

// Error handling
app.use((error, req, res, next) => {
    console.error('Server error:', error);
    res.status(500).json({ 
        error: 'Internal server error',
        message: process.env.NODE_ENV === 'development' ? error.message : 'Something went wrong'
    });
});

// Start server
app.listen(PORT, () => {
    console.log('🏥 Sapyyn Platform Started Successfully!');
    console.log(`🌐 Server running on: http://localhost:${PORT}`);
    console.log(`📊 Health check: http://localhost:${PORT}/api/health`);
    console.log(`🚪 Portal access: http://localhost:${PORT}/portal`);
    console.log(`⚡ Quick referral: http://localhost:${PORT}/quick-referral`);
    console.log('');
    console.log('✅ Dependencies loaded successfully!');
    console.log('🎉 Ready to handle requests!');
});

module.exports = app;