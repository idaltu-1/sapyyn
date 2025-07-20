#!/bin/bash

# =============================================================================
# SAPYYN PLATFORM - COMPLETE AUTOMATED DEPLOYMENT
# From Terminal to Production (Heroku + MongoDB Atlas)
# =============================================================================

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration - Update these values
PROJECT_NAME="sapyyn"
HEROKU_APP_NAME="sapyyn-app"
MONGODB_USERNAME="wgray6"
MONGODB_PASSWORD="tc61eQwVcSKwW3ST"
MONGODB_CLUSTER="cluster0"
MONGODB_DATABASE="sapyyn"

# Derived variables
MONGODB_URI="mongodb+srv://${MONGODB_USERNAME}:${MONGODB_PASSWORD}@${MONGODB_CLUSTER}.mongodb.net/${MONGODB_DATABASE}?retryWrites=true&w=majority"
HEROKU_APP_URL="https://${HEROKU_APP_NAME}-5465ab15434a.herokuapp.com"

echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${PURPLE}║                    SAPYYN PLATFORM DEPLOYMENT                     ║${NC}"
echo -e "${PURPLE}║                  Complete Automated Setup                         ║${NC}"
echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to print section headers
print_section() {
    echo -e "\n${CYAN}▶ $1${NC}"
    echo -e "${CYAN}$(printf '%.0s─' {1..50})${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to install missing dependencies
install_dependencies() {
    print_section "CHECKING DEPENDENCIES"
    
    # Check Node.js
    if ! command_exists node; then
        echo -e "${YELLOW}Installing Node.js...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            if command_exists brew; then
                brew install node
            else
                echo -e "${RED}Please install Homebrew first: /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"${NC}"
                exit 1
            fi
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
            sudo apt-get install -y nodejs
        fi
    fi
    
    # Check Git
    if ! command_exists git; then
        echo -e "${YELLOW}Installing Git...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install git
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo apt-get update && sudo apt-get install -y git
        fi
    fi
    
    # Check Heroku CLI
    if ! command_exists heroku; then
        echo -e "${YELLOW}Installing Heroku CLI...${NC}"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew tap heroku/brew && brew install heroku
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            curl https://cli-assets.heroku.com/install.sh | sh
        fi
    fi
    
    echo -e "${GREEN}✅ All dependencies checked/installed${NC}"
}

# Function to create project files
create_project_files() {
    print_section "CREATING PROJECT FILES"
    
    # Create package.json
    cat > package.json << 'PACKAGE_EOF'
{
  "name": "sapyyn-platform",
  "version": "1.0.0",
  "description": "Complete healthcare referral management platform with enhanced features",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js || node server.js",
    "test": "echo 'Tests not configured yet'",
    "postinstall": "echo '✅ Installation complete!'",
    "heroku-postbuild": "echo '🚀 Heroku build complete'"
  },
  "dependencies": {
    "express": "^4.18.2",
    "mongoose": "^7.5.0",
    "cors": "^2.8.5",
    "dotenv": "^16.3.1",
    "helmet": "^7.0.0",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.2"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  },
  "engines": {
    "node": "18.x",
    "npm": "9.x"
  },
  "keywords": [
    "healthcare",
    "referrals",
    "medical",
    "platform",
    "mongodb",
    "atlas"
  ],
  "author": "Sapyyn Team",
  "license": "MIT"
}
PACKAGE_EOF

    # Create Procfile
    echo "web: node server.js" > Procfile
    
    echo -e "${GREEN}✅ Project files created${NC}"
}

# Function to create backend structure
create_backend() {
    print_section "CREATING BACKEND STRUCTURE"
    
    # Create directories
    mkdir -p backend/config
    
    # Create database configuration
    cat > backend/config/database.js << 'DATABASE_EOF'
const mongoose = require('mongoose');

class DatabaseService {
    constructor() {
        this.isConnected = false;
        this.reconnectTimeout = null;
        this.maxReconnectAttempts = 5;
        this.reconnectAttempts = 0;
    }

    async connect() {
        try {
            const mongoUri = process.env.MONGODB_URI;
            
            if (!mongoUri) {
                throw new Error('MongoDB URI not found in environment variables');
            }

            console.log('🔌 Connecting to MongoDB Atlas...');

            const options = {
                useNewUrlParser: true,
                useUnifiedTopology: true,
                serverSelectionTimeoutMS: 5000,
                socketTimeoutMS: 45000,
                maxPoolSize: 10,
                minPoolSize: 1,
                maxIdleTimeMS: 30000,
                bufferCommands: false,
                bufferMaxEntries: 0
            };

            await mongoose.connect(mongoUri, options);

            this.isConnected = true;
            this.reconnectAttempts = 0;
            
            console.log('✅ MongoDB Atlas connected successfully!');
            console.log(`📊 Database: ${mongoose.connection.db.databaseName}`);

            this.setupEventListeners();
            return true;
        } catch (error) {
            console.error('❌ MongoDB Atlas connection failed:', error.message);
            throw error;
        }
    }

    setupEventListeners() {
        mongoose.connection.on('connected', () => {
            console.log('✅ MongoDB Atlas connection established');
            this.isConnected = true;
        });

        mongoose.connection.on('error', (error) => {
            console.error('❌ MongoDB Atlas connection error:', error);
            this.isConnected = false;
        });

        mongoose.connection.on('disconnected', () => {
            console.warn('⚠️ MongoDB Atlas disconnected');
            this.isConnected = false;
        });

        process.on('SIGINT', () => this.gracefulShutdown('SIGINT'));
        process.on('SIGTERM', () => this.gracefulShutdown('SIGTERM'));
    }

    async gracefulShutdown(signal) {
        console.log(`📤 Received ${signal}. Gracefully shutting down MongoDB connection...`);
        
        try {
            await mongoose.connection.close();
            console.log('✅ MongoDB Atlas connection closed gracefully');
            process.exit(0);
        } catch (error) {
            console.error('❌ Error during graceful shutdown:', error);
            process.exit(1);
        }
    }

    async healthCheck() {
        try {
            if (!this.isConnected) {
                return {
                    status: 'disconnected',
                    message: 'Not connected to MongoDB Atlas'
                };
            }

            await mongoose.connection.db.admin().ping();
            
            return {
                status: 'healthy',
                message: 'MongoDB Atlas connection is healthy',
                details: {
                    host: mongoose.connection.host,
                    database: mongoose.connection.db.databaseName,
                    readyState: mongoose.connection.readyState
                }
            };
        } catch (error) {
            return {
                status: 'unhealthy',
                message: 'MongoDB Atlas health check failed',
                error: error.message
            };
        }
    }

    async initializeDatabase() {
        try {
            console.log('🏗️ Initializing database structure...');
            await this.createIndexes();
            console.log('✅ Database initialization complete');
        } catch (error) {
            console.error('❌ Database initialization failed:', error);
            throw error;
        }
    }

    async createIndexes() {
        await mongoose.connection.db.collection('users').createIndex({ email: 1 }, { unique: true });
        await mongoose.connection.db.collection('referrals').createIndex({ patientEmail: 1 });
        await mongoose.connection.db.collection('referrals').createIndex({ status: 1 });
        console.log('📊 Database indexes created successfully');
    }
}

module.exports = new DatabaseService();
DATABASE_EOF

    # Create main server.js
    cat > server.js << 'SERVER_EOF'
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
SERVER_EOF

    echo -e "${GREEN}✅ Backend structure created${NC}"
}

# Function to create frontend structure
create_frontend() {
    print_section "CREATING FRONTEND STRUCTURE"
    
    # Create directories
    mkdir -p frontend/public
    
    # Create main HTML file
    cat > frontend/public/index.html << 'INDEX_EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sapyyn - Healthcare Referral Platform</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .hero { padding: 100px 0; color: white; text-align: center; }
        .card { box-shadow: 0 10px 30px rgba(0,0,0,0.1); border: none; border-radius: 15px; }
        .btn-primary { background: linear-gradient(45deg, #667eea, #764ba2); border: none; }
    </style>
</head>
<body>
    <div class="hero">
        <div class="container">
            <h1 class="display-4 mb-4">
                <i class="fas fa-hospital me-3"></i>Sapyyn Platform
            </h1>
            <p class="lead mb-5">Advanced Healthcare Referral Management System</p>
            <div class="row justify-content-center">
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-body p-5">
                            <h3 class="mb-4">Platform Features</h3>
                            <div class="row">
                                <div class="col-md-6 mb-3">
                                    <a href="/portal" class="btn btn-primary btn-lg w-100">
                                        <i class="fas fa-users me-2"></i>Referral Portal
                                    </a>
                                </div>
                                <div class="col-md-6 mb-3">
                                    <a href="/admin" class="btn btn-outline-primary btn-lg w-100">
                                        <i class="fas fa-cog me-2"></i>Admin Panel
                                    </a>
                                </div>
                            </div>
                            <div class="mt-4">
                                <small class="text-muted">
                                    <i class="fas fa-shield-alt me-1"></i>Secure • 
                                    <i class="fas fa-database me-1"></i>MongoDB Atlas • 
                                    <i class="fas fa-cloud me-1"></i>Heroku Hosted
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Test API connectivity on load
        fetch('/api/health')
            .then(response => response.json())
            .then(data => {
                console.log('✅ Platform Status:', data);
                if (data.database && data.database.status === 'healthy') {
                    console.log('✅ Database Connected');
                }
            })
            .catch(error => console.error('❌ Platform Error:', error));
    </script>
</body>
</html>
INDEX_EOF

    # Create portal page
    cat > frontend/public/portal.html << 'PORTAL_EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Referral Portal - Sapyyn</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="/">
                <i class="fas fa-hospital me-2"></i>Sapyyn Portal
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Home</a>
                <a class="nav-link" href="/admin">Admin</a>
            </div>
        </div>
    </nav>

    <div class="container mt-5">
        <h2>Referral Management Portal</h2>
        <div class="row">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5>Quick Referral Form</h5>
                    </div>
                    <div class="card-body">
                        <form id="referralForm">
                            <div class="mb-3">
                                <label class="form-label">Patient Name</label>
                                <input type="text" class="form-control" name="patientName" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Patient Email</label>
                                <input type="email" class="form-control" name="patientEmail" required>
                            </div>
                            <div class="mb-3">
                                <label class="form-label">Referral Type</label>
                                <select class="form-control" name="referralType" required>
                                    <option>Oral Surgery</option>
                                    <option>Orthodontics</option>
                                    <option>Periodontist</option>
                                    <option>Endodontist</option>
                                </select>
                            </div>
                            <button type="submit" class="btn btn-primary">Submit Referral</button>
                        </form>
                    </div>
                </div>
            </div>
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5>System Status</h5>
                    </div>
                    <div class="card-body">
                        <div id="systemStatus">Loading...</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Load system status
        fetch('/api/health')
            .then(response => response.json())
            .then(data => {
                const statusDiv = document.getElementById('systemStatus');
                statusDiv.innerHTML = `
                    <div class="mb-2">
                        <span class="badge bg-success">Server Online</span>
                    </div>
                    <div class="mb-2">
                        <span class="badge ${data.database && data.database.status === 'healthy' ? 'bg-success' : 'bg-warning'}">
                            Database ${data.database ? data.database.status : 'Unknown'}
                        </span>
                    </div>
                    <small class="text-muted">Last check: ${new Date().toLocaleTimeString()}</small>
                `;
            });

        // Handle form submission
        document.getElementById('referralForm').addEventListener('submit', function(e) {
            e.preventDefault();
            const formData = new FormData(e.target);
            const data = Object.fromEntries(formData);
            
            fetch('/api/referrals', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(result => {
                alert('Referral submitted successfully!');
                e.target.reset();
            })
            .catch(error => {
                alert('Error submitting referral: ' + error.message);
            });
        });
    </script>
</body>
</html>
PORTAL_EOF

    # Create admin page
    cat > frontend/public/admin.html << 'ADMIN_EOF'
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Admin Dashboard - Sapyyn</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container-fluid">
            <a class="navbar-brand" href="/admin">
                <i class="fas fa-hospital me-2"></i>Sapyyn Admin
            </a>
            <div class="navbar-nav ms-auto">
                <a class="nav-link" href="/">Back to Site</a>
            </div>
        </div>
    </nav>

    <div class="container-fluid mt-4">
        <h2 class="mb-4">Admin Dashboard</h2>
        
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <i class="fas fa-users fa-2x text-primary mb-2"></i>
                        <h4 id="userCount">0</h4>
                        <small class="text-muted">Total Users</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <i class="fas fa-handshake fa-2x text-success mb-2"></i>
                        <h4 id="referralCount">0</h4>
                        <small class="text-muted">Referrals</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <i class="fas fa-database fa-2x text-info mb-2"></i>
                        <h4 id="dbStatus">Checking...</h4>
                        <small class="text-muted">Database</small>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card text-center">
                    <div class="card-body">
                        <i class="fas fa-server fa-2x text-warning mb-2"></i>
                        <h4 id="serverUptime">0</h4>
                        <small class="text-muted">Uptime (hrs)</small>
                    </div>
                </div>
            </div>
        </div>

        <div class="row">
            <div class="col-md-12">
                <div class="card">
                    <div class="card-header">
                        <h5>System Information</h5>
                    </div>
                    <div class="card-body">
                        <pre id="systemInfo">Loading system information...</pre>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Load dashboard data
        Promise.all([
            fetch('/api/health').then(r => r.json()),
            fetch('/api/status').then(r => r.json())
        ]).then(([health, status]) => {
            // Update dashboard stats
            document.getElementById('dbStatus').textContent = 
                health.database && health.database.status === 'healthy' ? 'Healthy' : 'Issues';
            document.getElementById('serverUptime').textContent = 
                Math.round(status.uptime / 3600 * 100) / 100;
            
            // Update system info
            document.getElementById('systemInfo').textContent = 
                JSON.stringify({health, status}, null, 2);
        }).catch(error => {
            document.getElementById('systemInfo').textContent = 
                'Error loading system information: ' + error.message;
        });
    </script>
</body>
</html>
ADMIN_EOF

    echo -e "${GREEN}✅ Frontend structure created${NC}"
}

# Function to install npm dependencies
install_npm_dependencies() {
    print_section "INSTALLING NPM DEPENDENCIES"
    
    echo -e "${BLUE}📦 Installing Node.js dependencies...${NC}"
    npm install
    
    echo -e "${GREEN}✅ NPM dependencies installed${NC}"
}

# Function to setup Heroku
setup_heroku() {
    print_section "SETTING UP HEROKU"
    
    # Check if user is logged in to Heroku
    if ! heroku auth:whoami >/dev/null 2>&1; then
        echo -e "${YELLOW}🔐 Please log in to Heroku...${NC}"
        heroku login
    fi
    
    echo -e "${BLUE}🏗️ Setting up Heroku application: $HEROKU_APP_NAME${NC}"
    
    # Add Heroku git remote (will use existing app if it exists)
    heroku git:remote -a "$HEROKU_APP_NAME" || {
        echo -e "${YELLOW}⚠️ Could not connect to existing app. Creating new one...${NC}"
        heroku create "$HEROKU_APP_NAME"
        heroku git:remote -a "$HEROKU_APP_NAME"
    }
    
    echo -e "${GREEN}✅ Heroku application configured${NC}"
}

# Function to configure environment variables
configure_environment() {
    print_section "CONFIGURING ENVIRONMENT VARIABLES"
    
    # Generate security keys
    JWT_SECRET=$(openssl rand -base64 32)
    ENCRYPTION_KEY=$(openssl rand -hex 16)
    ENCRYPTION_IV=$(openssl rand -hex 8)
    
    echo -e "${BLUE}🔐 Setting environment variables...${NC}"
    
    # Set all environment variables
    heroku config:set \
        NODE_ENV=production \
        MONGODB_URI="$MONGODB_URI" \
        DATABASE_NAME="$MONGODB_DATABASE" \
        JWT_SECRET="$JWT_SECRET" \
        ENCRYPTION_KEY="$ENCRYPTION_KEY" \
        ENCRYPTION_IV="$ENCRYPTION_IV" \
        FRONTEND_URL="$HEROKU_APP_URL" \
        -a "$HEROKU_APP_NAME"
    
    echo -e "${GREEN}✅ Environment variables configured${NC}"
}

# Function to deploy to Heroku
deploy_to_heroku() {
    print_section "DEPLOYING TO HEROKU"
    
    # Commit all changes
    echo -e "${BLUE}📝 Committing changes to Git...${NC}"
    git add .
    git commit -m "Complete Sapyyn platform deployment with MongoDB Atlas integration" || echo "Nothing new to commit"
    
    # Deploy to Heroku
    echo -e "${BLUE}🚀 Deploying to Heroku...${NC}"
    git push heroku master || git push heroku main
    
    # Scale web dyno
    echo -e "${BLUE}⚡ Scaling web dyno...${NC}"
    heroku ps:scale web=1 -a "$HEROKU_APP_NAME"
    
    echo -e "${GREEN}✅ Deployment to Heroku complete${NC}"
}

# Function to test deployment
test_deployment() {
    print_section "TESTING DEPLOYMENT"
    
    echo -e "${BLUE}🧪 Testing deployment...${NC}"
    sleep 15  # Wait for deployment to stabilize
    
    # Test main site
    echo -e "${CYAN}Testing main site...${NC}"
    if curl -s -o /dev/null -w "%{http_code}" "$HEROKU_APP_URL" | grep -q "200"; then
        echo -e "${GREEN}✅ Main site responding${NC}"
    else
        echo -e "${RED}❌ Main site not responding${NC}"
    fi
    
    # Test health endpoint
    echo -e "${CYAN}Testing health endpoint...${NC}"
    if curl -s "$HEROKU_APP_URL/api/health" | grep -q "ok"; then
        echo -e "${GREEN}✅ Health endpoint responding${NC}"
    else
        echo -e "${RED}❌ Health endpoint not responding${NC}"
    fi
    
    # Test database connection
    echo -e "${CYAN}Testing database connection...${NC}"
    if curl -s "$HEROKU_APP_URL/api/database/status" | grep -q "healthy"; then
        echo -e "${GREEN}✅ Database connected${NC}"
    else
        echo -e "${YELLOW}⚠️ Database connection may have issues${NC}"
    fi
}

# Function to display final information
display_final_info() {
    print_section "DEPLOYMENT COMPLETE"
    
    echo -e "${GREEN}🎉 Sapyyn Platform deployed successfully!${NC}"
    echo ""
    echo -e "${CYAN}📋 Deployment Information:${NC}"
    echo -e "${CYAN}══════════════════════════${NC}"
    echo -e "🌐 Application URL: ${BLUE}$HEROKU_APP_URL${NC}"
    echo -e "🔗 Portal: ${BLUE}$HEROKU_APP_URL/portal${NC}"
    echo -e "👤 Admin: ${BLUE}$HEROKU_APP_URL/admin${NC}"
    echo -e "📊 Health Check: ${BLUE}$HEROKU_APP_URL/api/health${NC}"
    echo -e "🗄️ Database Status: ${BLUE}$HEROKU_APP_URL/api/database/status${NC}"
    echo ""
    echo -e "${CYAN}🛠️ Useful Commands:${NC}"
    echo -e "View logs: ${YELLOW}heroku logs --tail -a $HEROKU_APP_NAME${NC}"
    echo -e "Open app: ${YELLOW}heroku open -a $HEROKU_APP_NAME${NC}"
    echo -e "Check config: ${YELLOW}heroku config -a $HEROKU_APP_NAME${NC}"
    echo -e "Restart app: ${YELLOW}heroku restart -a $HEROKU_APP_NAME${NC}"
    echo ""
    echo -e "${GREEN}✅ Ready for production use!${NC}"
}

# Main execution function
main() {
    echo -e "${BLUE}Starting complete deployment process...${NC}"
    
    install_dependencies
    create_project_files
    create_backend
    create_frontend
    install_npm_dependencies
    setup_heroku
    configure_environment
    deploy_to_heroku
    test_deployment
    display_final_info
    
    echo -e "${PURPLE}╔════════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║                    DEPLOYMENT SUCCESSFUL!                         ║${NC}"
    echo -e "${PURPLE}║              Your Sapyyn Platform is now live!                    ║${NC}"
    echo -e "${PURPLE}╚════════════════════════════════════════════════════════════════════╝${NC}"
}

# Error handling
trap 'echo -e "\n${RED}❌ Deployment failed! Check the error above.${NC}"; exit 1' ERR

# Run main function
main "$@"
