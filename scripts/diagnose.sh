#!/bin/bash

# Diagnostic Script - Identify installation issues

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${BLUE}🔍 Sapyyn Dependency Diagnostic Tool${NC}"
echo "=================================================="
echo ""

# Check Node.js
echo -e "${CYAN}Node.js Status:${NC}"
if command -v node &> /dev/null; then
    echo -e "${GREEN}✅ Node.js found: $(node --version)${NC}"
    
    # Check if version is compatible
    node_version=$(node --version | sed 's/v//')
    if [[ $(echo "$node_version 14.0.0" | tr " " "\n" | sort -V | head -n1) == "14.0.0" ]]; then
        echo -e "${GREEN}✅ Node.js version is compatible${NC}"
    else
        echo -e "${RED}❌ Node.js version too old (need 14.0.0+)${NC}"
    fi
else
    echo -e "${RED}❌ Node.js not found${NC}"
fi

# Check npm
echo -e "${CYAN}npm Status:${NC}"
if command -v npm &> /dev/null; then
    echo -e "${GREEN}✅ npm found: $(npm --version)${NC}"
    
    # Check npm config
    echo "Registry: $(npm config get registry)"
    echo "Cache: $(npm config get cache)"
else
    echo -e "${RED}❌ npm not found${NC}"
fi

# Check system resources
echo -e "${CYAN}System Resources:${NC}"
echo "Available disk space: $(df -h . | awk 'NR==2{print $4}')"
echo "Memory usage: $(free -h 2>/dev/null | awk 'NR==2{print $3"/"$2}' || echo 'N/A')"

# Check network connectivity
echo -e "${CYAN}Network Connectivity:${NC}"
if curl -s --max-time 5 https://registry.npmjs.org/ > /dev/null; then
    echo -e "${GREEN}✅ npm registry accessible${NC}"
else
    echo -e "${RED}❌ Cannot reach npm registry${NC}"
fi

# Check project directory
echo -e "${CYAN}Project Status:${NC}"
if [[ -f "package.json" ]]; then
    echo -e "${GREEN}✅ package.json found${NC}"
else
    echo -e "${RED}❌ package.json not found${NC}"
fi

if [[ -d "node_modules" ]]; then
    echo -e "${YELLOW}⚠️  node_modules exists ($(ls node_modules | wc -l) packages)${NC}"
else
    echo -e "${YELLOW}⚠️  node_modules not found${NC}"
fi

if [[ -f "package-lock.json" ]]; then
    echo -e "${YELLOW}⚠️  package-lock.json exists${NC}"
else
    echo -e "${YELLOW}⚠️  package-lock.json not found${NC}"
fi

# Check permissions
echo -e "${CYAN}Permissions:${NC}"
if [[ -w "." ]]; then
    echo -e "${GREEN}✅ Current directory is writable${NC}"
else
    echo -e "${RED}❌ Current directory is not writable${NC}"
fi

# Check for common issues
echo -e "${CYAN}Common Issues Check:${NC}"

# Check for EACCES errors
if npm config get prefix | grep -q "/usr/local"; then
    echo -e "${YELLOW}⚠️  npm prefix set to /usr/local (may cause permission issues)${NC}"
fi

# Check for proxy issues
if [[ -n "$(npm config get proxy)" ]] || [[ -n "$(npm config get https-proxy)" ]]; then
    echo -e "${YELLOW}⚠️  Proxy settings detected${NC}"
fi

echo ""
echo -e "${BLUE}Recommendations:${NC}"
echo "1. Run: chmod +x scripts/*.sh"
echo "2. Run: ./scripts/quick-fix.sh"
echo "3. If that fails: ./scripts/emergency-install.sh"
echo "4. Alternative: ./scripts/docker-setup.sh"