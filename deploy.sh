#!/bin/bash

# Sapyyn Patient Referral System - Deploy Script
# This script handles the complete deployment process

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PYTHON_MIN_VERSION="3.8"
NODE_MIN_VERSION="16"
DEFAULT_PORT="5000"

echo -e "${BLUE}🚀 Sapyyn Patient Referral System - Deployment Script${NC}"
echo -e "${BLUE}====================================================${NC}"

# Function to check version
version_ge() {
    printf '%s\n%s' "$2" "$1" | sort -V -C
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${YELLOW}🔍 Checking prerequisites...${NC}"

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    if version_ge "$PYTHON_VERSION" "$PYTHON_MIN_VERSION"; then
        echo -e "${GREEN}✅ Python $PYTHON_VERSION found${NC}"
    else
        echo -e "${RED}❌ Python $PYTHON_MIN_VERSION or higher required. Found: $PYTHON_VERSION${NC}"
        exit 1
    fi
else
    echo -e "${RED}❌ Python 3 not found. Please install Python $PYTHON_MIN_VERSION or higher${NC}"
    exit 1
fi

# Check pip
if command_exists pip3; then
    echo -e "${GREEN}✅ pip3 found${NC}"
else
    echo -e "${RED}❌ pip3 not found. Please install pip3${NC}"
    exit 1
fi

# Check Node.js
if command_exists node; then
    NODE_VERSION=$(node --version | sed 's/v//')
    if version_ge "$NODE_VERSION" "$NODE_MIN_VERSION"; then
        echo -e "${GREEN}✅ Node.js $NODE_VERSION found${NC}"
    else
        echo -e "${YELLOW}⚠️  Node.js $NODE_MIN_VERSION or higher recommended. Found: $NODE_VERSION${NC}"
        echo -e "${YELLOW}   Frontend build may not work properly${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Node.js not found. Frontend build will be skipped${NC}"
fi

# Check npm
if command_exists npm; then
    echo -e "${GREEN}✅ npm found${NC}"
else
    echo -e "${YELLOW}⚠️  npm not found. Frontend build will be skipped${NC}"
fi

echo ""

# Install Python dependencies
echo -e "${YELLOW}📦 Installing Python dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    echo -e "${GREEN}✅ Python dependencies installed${NC}"
else
    echo -e "${RED}❌ requirements.txt not found${NC}"
    exit 1
fi

echo ""

# Install Node.js dependencies and build frontend (if available)
if command_exists npm && [ -f "package.json" ]; then
    echo -e "${YELLOW}📦 Installing Node.js dependencies...${NC}"
    npm install
    echo -e "${GREEN}✅ Node.js dependencies installed${NC}"
    
    echo -e "${YELLOW}🏗️  Building frontend assets...${NC}"
    npm run build
    echo -e "${GREEN}✅ Frontend assets built${NC}"
else
    echo -e "${YELLOW}⚠️  Skipping frontend build (npm or package.json not available)${NC}"
fi

echo ""

# Setup environment file
echo -e "${YELLOW}⚙️  Setting up environment...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Environment file created from .env.example${NC}"
        echo -e "${YELLOW}⚠️  Please edit .env with your actual configuration values${NC}"
    else
        echo -e "${YELLOW}⚠️  No .env.example found, creating basic .env file${NC}"
        cat > .env << EOF
SECRET_KEY=development-secret-key-change-in-production
FLASK_ENV=development
DATABASE_NAME=sapyyn.db
BASE_URL=http://localhost:${DEFAULT_PORT}
DEBUG=true
EOF
        echo -e "${GREEN}✅ Basic .env file created${NC}"
    fi
else
    echo -e "${GREEN}✅ Environment file already exists${NC}"
fi

echo ""

# Initialize database
echo -e "${YELLOW}🗄️  Initializing database...${NC}"
python3 -c "
try:
    from app import init_db
    init_db()
    print('Database initialized successfully')
except Exception as e:
    print(f'Database initialization error: {e}')
    exit(1)
"
echo -e "${GREEN}✅ Database initialized${NC}"

echo ""

# Check if port is available
echo -e "${YELLOW}🔍 Checking if port ${DEFAULT_PORT} is available...${NC}"
if command_exists lsof; then
    if lsof -Pi :${DEFAULT_PORT} -sTCP:LISTEN -t >/dev/null; then
        echo -e "${YELLOW}⚠️  Port ${DEFAULT_PORT} is already in use${NC}"
        echo -e "${YELLOW}   You may need to stop the existing service or use a different port${NC}"
    else
        echo -e "${GREEN}✅ Port ${DEFAULT_PORT} is available${NC}"
    fi
fi

echo ""

# Display deployment options
echo -e "${BLUE}🎯 Deployment Options:${NC}"
echo -e "${YELLOW}1. Development (Flask dev server):${NC}"
echo -e "   python3 app.py"
echo -e ""
echo -e "${YELLOW}2. Production (Gunicorn):${NC}"
echo -e "   gunicorn app:app -b 0.0.0.0:${DEFAULT_PORT} --workers=4"
echo -e ""
echo -e "${YELLOW}3. Docker:${NC}"
echo -e "   docker-compose up -d"
echo -e ""

# Ask user which deployment method to use
read -p "$(echo -e "${YELLOW}Choose deployment method (1-3) or press Enter for development: ${NC}")" choice

case $choice in
    1|"")
        echo -e "${YELLOW}🚀 Starting development server...${NC}"
        echo -e "${GREEN}✅ Application will be available at: http://localhost:${DEFAULT_PORT}${NC}"
        echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
        echo ""
        python3 app.py
        ;;
    2)
        if command_exists gunicorn; then
            echo -e "${YELLOW}🚀 Starting production server with Gunicorn...${NC}"
            echo -e "${GREEN}✅ Application will be available at: http://localhost:${DEFAULT_PORT}${NC}"
            echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
            echo ""
            gunicorn app:app -b 0.0.0.0:${DEFAULT_PORT} --workers=4
        else
            echo -e "${RED}❌ Gunicorn not found. Installing...${NC}"
            pip3 install gunicorn
            echo -e "${YELLOW}🚀 Starting production server with Gunicorn...${NC}"
            echo -e "${GREEN}✅ Application will be available at: http://localhost:${DEFAULT_PORT}${NC}"
            echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
            echo ""
            gunicorn app:app -b 0.0.0.0:${DEFAULT_PORT} --workers=4
        fi
        ;;
    3)
        if command_exists docker-compose; then
            echo -e "${YELLOW}🚀 Starting Docker containers...${NC}"
            docker-compose up -d
            echo -e "${GREEN}✅ Docker containers started${NC}"
            echo -e "${GREEN}✅ Application should be available at: http://localhost:${DEFAULT_PORT}${NC}"
            echo -e "${YELLOW}Use 'docker-compose logs -f' to view logs${NC}"
            echo -e "${YELLOW}Use 'docker-compose down' to stop containers${NC}"
        else
            echo -e "${RED}❌ Docker Compose not found. Please install Docker and Docker Compose${NC}"
            exit 1
        fi
        ;;
    *)
        echo -e "${RED}❌ Invalid choice. Exiting.${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}🎉 Deployment completed successfully!${NC}"