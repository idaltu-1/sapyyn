#!/bin/bash

# Quick Fix Script - Fast dependency resolution
# Tries the most common solutions first

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo -e "${BLUE}🚀 Sapyyn Quick Dependency Fix${NC}"
echo -e "${YELLOW}Trying fast solutions first...${NC}"
echo ""

cd "$PROJECT_ROOT"

# Quick Fix 1: Clear cache and reinstall
echo -e "${CYAN}Quick Fix 1: Clear cache and reinstall${NC}"
rm -rf node_modules package-lock.json
npm cache clean --force
if npm install --legacy-peer-deps; then
    echo -e "${GREEN}✅ SUCCESS! Dependencies installed.${NC}"
    echo -e "${GREEN}🎉 Run: npm run dev${NC}"
    exit 0
fi

# Quick Fix 2: Use yarn
echo -e "${CYAN}Quick Fix 2: Try with yarn${NC}"
if ! command -v yarn &> /dev/null; then
    npm install -g yarn
fi
if yarn install; then
    echo -e "${GREEN}✅ SUCCESS! Dependencies installed with yarn.${NC}"
    echo -e "${GREEN}🎉 Run: npm run dev${NC}"
    exit 0
fi

# Quick Fix 3: Install core dependencies only
echo -e "${CYAN}Quick Fix 3: Install core dependencies${NC}"
rm -rf node_modules package-lock.json

npm init -y
npm install express@^4.18.2 mongoose@^7.5.0 cors@^2.8.5 bcryptjs@^2.4.3 jsonwebtoken@^9.0.2 dotenv@^16.3.1 nodemon@^3.0.1 --legacy-peer-deps

if [[ -d "node_modules/express" ]]; then
    echo -e "${GREEN}✅ SUCCESS! Core dependencies installed.${NC}"
    
    # Create basic package.json scripts
    cat > package.json << 'EOF'
{
  "name": "sapyyn-platform",
  "version": "1.0.0",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js || node server.js"
  },
  "dependencies": {
    "express": "^4.18.2",
    "mongoose": "^7.5.0",
    "cors": "^2.8.5",
    "bcryptjs": "^2.4.3",
    "jsonwebtoken": "^9.0.2",
    "dotenv": "^16.3.1",
    "nodemon": "^3.0.1"
  }
}
EOF
    
    echo -e "${GREEN}🎉 Core setup complete! Run: npm run dev${NC}"
    exit 0
fi

# If all quick fixes fail, run emergency installer
echo -e "${RED}❌ Quick fixes failed. Running emergency installer...${NC}"
echo ""
exec "$SCRIPT_DIR/emergency-install.sh"