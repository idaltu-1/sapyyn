#!/bin/bash

# Sapyyn Platform - Docker Setup Script
# Sets up Docker environment for development and production

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Print header
print_header() {
    clear
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                  Sapyyn Docker Setup                         ║${NC}"
    echo -e "${BLUE}║              Containerized Development Environment           ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Check Docker installation
check_docker() {
    echo -e "${BLUE}🐳 Checking Docker installation...${NC}"
    
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}❌ Docker not found${NC}"
        echo -e "${YELLOW}Please install Docker from: https://docs.docker.com/get-docker/${NC}"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        echo -e "${RED}❌ Docker Compose not found${NC}"
        echo -e "${YELLOW}Please install Docker Compose${NC}"
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        echo -e "${RED}❌ Docker daemon not running${NC}"
        echo -e "${YELLOW}Please start Docker service${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ Docker is installed and running${NC}"
}

# Create Docker configuration files
create_docker_configs() {
    echo -e "${BLUE}📄 Creating Docker configuration files...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Create docker directory
    mkdir -p docker
    
    # Create nginx config
    cat > docker/nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    upstream sapyyn_app {
        server sapyyn-app:3000;
    }

    server {
        listen 80;
        server_name localhost;

        # Security headers
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-XSS-Protection "1; mode=block" always;
        add_header X-Content-Type-Options "nosniff" always;

        # Proxy to Node.js app
        location / {
            proxy_pass http://sapyyn_app;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
        }

        # Health check endpoint
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
EOF

    # Create MongoDB init script
    cat > docker/mongo-init.js << 'EOF'
// MongoDB initialization script for Sapyyn
db = db.getSiblingDB('sapyyn');

// Create collections
db.createCollection('users');
db.createCollection('practices');
db.createCollection('referrals');
db.createCollection('referralcodes');
db.createCollection('rewards');
db.createCollection('lmscourses');
db.createCollection('userprogresses');

// Create indexes for better performance
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "role": 1 });
db.referrals.createIndex({ "referralId": 1 }, { unique: true });
db.referrals.createIndex({ "patientId": 1 });
db.referrals.createIndex({ "referringDentistId": 1 });
db.referralcodes.createIndex({ "code": 1 }, { unique: true });
db.referralcodes.createIndex({ "doctorId": 1 });

print('Database initialized successfully');
EOF

    # Create .dockerignore
    cat > .dockerignore << 'EOF'
node_modules
npm-debug.log
.git
.gitignore
README.md
.env
.nyc_output
coverage
.DS_Store
*.log
logs
.vscode
.idea
EOF

    echo -e "${GREEN}✅ Docker configuration files created${NC}"
}

# Create environment file for Docker
create_docker_env() {
    echo -e "${BLUE}📄 Creating Docker environment file...${NC}"
    
    cd "$PROJECT_ROOT"
    
    if [[ ! -f ".env.docker" ]]; then
        cat > .env.docker << 'EOF'
# Docker Environment Configuration for Sapyyn
NODE_ENV=development
PORT=3000
FRONTEND_URL=http://localhost:3000

# Database (Docker Compose)
MONGODB_URI=mongodb://admin:password@sapyyn-mongo:27017/sapyyn?authSource=admin

# Redis (Docker Compose)
REDIS_URL=redis://sapyyn-redis:6379

# JWT Secret (Change in production!)
JWT_SECRET=your-super-secret-jwt-key-change-this-in-production

# Email Service (Configure as needed)
EMAIL_SERVICE_ENABLED=false
EMAIL_SERVICE=gmail
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-password
EMAIL_FROM=noreply@sapyyn.com

# SMS Service (Configure as needed)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=+1234567890

# Reward Providers (Configure as needed)
TANGO_API_KEY=your-tango-api-key
TREMENDOUS_API_KEY=your-tremendous-api-key

# No-Code Integrations (Configure as needed)
AIRTABLE_BASE_ID=your-airtable-base-id
AIRTABLE_API_KEY=your-airtable-api-key
ZAPIER_WEBHOOK_URL=your-zapier-webhook-url
N8N_WEBHOOK_URL=your-n8n-webhook-url
NOTION_TOKEN=your-notion-token
MAKE_WEBHOOK_URL=your-make-webhook-url
EOF
        echo -e "${GREEN}✅ Created .env.docker file${NC}"
    else
        echo -e "${YELLOW}⚠️  .env.docker already exists${NC}"
    fi
}

# Build Docker images
build_images() {
    echo -e "${BLUE}🔨 Building Docker images...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Build the main application image
    echo -e "${YELLOW}Building Sapyyn application image...${NC}"
    docker build -t sapyyn-platform:latest .
    
    echo -e "${GREEN}✅ Docker images built successfully${NC}"
}

# Start Docker services
start_services() {
    echo -e "${BLUE}🚀 Starting Docker services...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Use docker-compose or docker compose based on what's available
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        COMPOSE_CMD="docker compose"
    fi
    
    # Start services
    $COMPOSE_CMD up -d
    
    echo -e "${GREEN}✅ Docker services started${NC}"
    
    # Wait for services to be ready
    echo -e "${YELLOW}Waiting for services to be ready...${NC}"
    sleep 10
    
    # Check service status
    check_services
}

# Check service status
check_services() {
    echo -e "${BLUE}🔍 Checking service status...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Check if containers are running
    if docker ps | grep -q "sapyyn-app"; then
        echo -e "${GREEN}✅ Sapyyn app is running${NC}"
    else
        echo -e "${RED}❌ Sapyyn app is not running${NC}"
    fi
    
    if docker ps | grep -q "sapyyn-mongo"; then
        echo -e "${GREEN}✅ MongoDB is running${NC}"
    else
        echo -e "${RED}❌ MongoDB is not running${NC}"
    fi
    
    if docker ps | grep -q "sapyyn-redis"; then
        echo -e "${GREEN}✅ Redis is running${NC}"
    else
        echo -e "${RED}❌ Redis is not running${NC}"
    fi
    
    # Test application endpoint
    echo -e "${YELLOW}Testing application endpoint...${NC}"
    sleep 5
    
    if curl -f -s http://localhost:3000/api/health > /dev/null; then
        echo -e "${GREEN}✅ Application is responding${NC}"
    else
        echo -e "${YELLOW}⚠️  Application not responding yet (may still be starting)${NC}"
    fi
}

# Show logs
show_logs() {
    echo -e "${BLUE}📋 Recent application logs:${NC}"
    
    cd "$PROJECT_ROOT"
    
    if command -v docker-compose &> /dev/null; then
        docker-compose logs --tail=20 sapyyn-app
    else
        docker compose logs --tail=20 sapyyn-app
    fi
}

# Print usage instructions
print_instructions() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    Docker Setup Complete                     ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}🎉 Sapyyn platform is running in Docker!${NC}"
    echo ""
    echo -e "${YELLOW}Access points:${NC}"
    echo "- Application: http://localhost:3000"
    echo "- Database: mongodb://admin:password@localhost:27017/sapyyn"
    echo "- Redis: redis://localhost:6379"
    echo ""
    echo -e "${YELLOW}Useful Docker commands:${NC}"
    echo "- View logs: docker-compose logs -f sapyyn-app"
    echo "- Stop services: docker-compose down"
    echo "- Restart services: docker-compose restart"
    echo "- Rebuild: docker-compose up --build"
    echo "- Enter container: docker-compose exec sapyyn-app sh"
    echo ""
    echo -e "${YELLOW}Database access:${NC}"
    echo "- MongoDB shell: docker-compose exec sapyyn-mongo mongosh sapyyn -u admin -p password"
    echo "- Redis CLI: docker-compose exec sapyyn-redis redis-cli"
    echo ""
}

# Main execution
main() {
    print_header
    
    echo -e "${YELLOW}Setting up Docker environment for Sapyyn platform...${NC}"
    echo ""
    
    check_docker
    create_docker_configs
    create_docker_env
    build_images
    start_services
    show_logs
    print_instructions
    
    echo -e "${GREEN}Setup completed successfully!${NC}"
}

# Handle script interruption
trap 'echo -e "${RED}Docker setup interrupted${NC}"; exit 1' INT TERM

# Run main function
main "$@"