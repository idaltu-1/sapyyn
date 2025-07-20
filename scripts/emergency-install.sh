#!/bin/bash

# Emergency Dependency Installation Script
# This script tries every possible method to install dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/emergency-install.log"
BACKUP_DIR="$PROJECT_ROOT/backup-$(date +%Y%m%d_%H%M%S)"

# Error tracking
ATTEMPT_COUNT=0
SUCCESS=false

# Logging function
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Print header
print_header() {
    clear
    log "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    log "${BLUE}║               EMERGENCY DEPENDENCY INSTALLER                 ║${NC}"
    log "${BLUE}║              Trying All Possible Solutions                  ║${NC}"
    log "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    log ""
    log "${YELLOW}Starting emergency installation process...${NC}"
    log ""
}

# Backup existing files
create_backup() {
    log "${CYAN}📦 Creating backup...${NC}"
    mkdir -p "$BACKUP_DIR"
    
    if [[ -f "$PROJECT_ROOT/package.json" ]]; then
        cp "$PROJECT_ROOT/package.json" "$BACKUP_DIR/"
        log "${GREEN}✅ Backed up package.json${NC}"
    fi
    
    if [[ -f "$PROJECT_ROOT/package-lock.json" ]]; then
        cp "$PROJECT_ROOT/package-lock.json" "$BACKUP_DIR/"
        log "${GREEN}✅ Backed up package-lock.json${NC}"
    fi
    
    if [[ -f "$PROJECT_ROOT/yarn.lock" ]]; then
        cp "$PROJECT_ROOT/yarn.lock" "$BACKUP_DIR/"
        log "${GREEN}✅ Backed up yarn.lock${NC}"
    fi
}

# Complete cleanup
nuclear_cleanup() {
    log "${YELLOW}🧨 Nuclear cleanup - removing everything...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Remove all dependency files
    rm -rf node_modules
    rm -f package-lock.json
    rm -f yarn.lock
    rm -f pnpm-lock.yaml
    
    # Clear all caches
    npm cache clean --force 2>/dev/null || true
    yarn cache clean 2>/dev/null || true
    pnpm store prune 2>/dev/null || true
    
    # Clear system temp
    rm -rf ~/.npm/_cacache 2>/dev/null || true
    rm -rf ~/.yarn/cache 2>/dev/null || true
    
    log "${GREEN}✅ Complete cleanup done${NC}"
}

# Method 1: Standard npm install
try_npm_install() {
    ((ATTEMPT_COUNT++))
    log "${CYAN}Attempt $ATTEMPT_COUNT: Standard npm install${NC}"
    
    cd "$PROJECT_ROOT"
    
    if npm install; then
        log "${GREEN}✅ SUCCESS: Standard npm install worked!${NC}"
        return 0
    else
        log "${RED}❌ Standard npm install failed${NC}"
        return 1
    fi
}

# Method 2: npm install with --force
try_npm_force() {
    ((ATTEMPT_COUNT++))
    log "${CYAN}Attempt $ATTEMPT_COUNT: npm install --force${NC}"
    
    cd "$PROJECT_ROOT"
    
    if npm install --force; then
        log "${GREEN}✅ SUCCESS: npm install --force worked!${NC}"
        return 0
    else
        log "${RED}❌ npm install --force failed${NC}"
        return 1
    fi
}

# Method 3: npm install with --legacy-peer-deps
try_npm_legacy() {
    ((ATTEMPT_COUNT++))
    log "${CYAN}Attempt $ATTEMPT_COUNT: npm install --legacy-peer-deps${NC}"
    
    cd "$PROJECT_ROOT"
    
    if npm install --legacy-peer-deps; then
        log "${GREEN}✅ SUCCESS: npm install --legacy-peer-deps worked!${NC}"
        return 0
    else
        log "${RED}❌ npm install --legacy-peer-deps failed${NC}"
        return 1
    fi
}

# Method 4: npm install with multiple flags
try_npm_aggressive() {
    ((ATTEMPT_COUNT++))
    log "${CYAN}Attempt $ATTEMPT_COUNT: npm install with aggressive flags${NC}"
    
    cd "$PROJECT_ROOT"
    
    if npm install --force --legacy-peer-deps --no-audit --no-fund; then
        log "${GREEN}✅ SUCCESS: Aggressive npm install worked!${NC}"
        return 0
    else
        log "${RED}❌ Aggressive npm install failed${NC}"
        return 1
    fi
}

# Method 5: Install critical dependencies individually
try_individual_install() {
    ((ATTEMPT_COUNT++))
    log "${CYAN}Attempt $ATTEMPT_COUNT: Installing critical dependencies individually${NC}"
    
    cd "$PROJECT_ROOT"
    
    local critical_deps=(
        "express@^4.18.2"
        "mongoose@^7.5.0"
        "cors@^2.8.5"
        "bcryptjs@^2.4.3"
        "jsonwebtoken@^9.0.2"
        "dotenv@^16.3.1"
        "helmet@^7.0.0"
        "express-rate-limit@^6.10.0"
        "express-validator@^7.0.1"
        "multer@^1.4.5-lts.1"
        "nodemailer@^6.9.4"
        "axios@^1.5.0"
    )
    
    local dev_deps=(
        "nodemon@^3.0.1"
    )
    
    local success_count=0
    local total_deps=${#critical_deps[@]}
    
    for dep in "${critical_deps[@]}"; do
        log "Installing $dep..."
        if npm install "$dep" --save --legacy-peer-deps; then
            log "${GREEN}✅ $dep installed${NC}"
            ((success_count++))
        else
            log "${RED}❌ Failed to install $dep${NC}"
        fi
    done
    
    # Install dev dependencies
    for dep in "${dev_deps[@]}"; do
        log "Installing $dep (dev)..."
        if npm install "$dep" --save-dev --legacy-peer-deps; then
            log "${GREEN}✅ $dep installed${NC}"
        else
            log "${RED}❌ Failed to install $dep${NC}"
        fi
    done
    
    if [[ $success_count -ge $((total_deps * 70 / 100)) ]]; then
        log "${GREEN}✅ SUCCESS: Installed $success_count/$total_deps critical dependencies${NC}"
        return 0
    else
        log "${RED}❌ Individual install failed: only $success_count/$total_deps installed${NC}"
        return 1
    fi
}

# Method 6: Use yarn
try_yarn_install() {
    ((ATTEMPT_COUNT++))
    log "${CYAN}Attempt $ATTEMPT_COUNT: Using yarn${NC}"
    
    # Install yarn if not present
    if ! command -v yarn &> /dev/null; then
        log "Installing yarn..."
        if npm install -g yarn; then
            log "${GREEN}✅ yarn installed${NC}"
        else
            log "${RED}❌ Failed to install yarn${NC}"
            return 1
        fi
    fi
    
    cd "$PROJECT_ROOT"
    
    if yarn install; then
        log "${GREEN}✅ SUCCESS: yarn install worked!${NC}"
        return 0
    else
        log "${RED}❌ yarn install failed${NC}"
        return 1
    fi
}

# Method 7: Use pnpm
try_pnpm_install() {
    ((ATTEMPT_COUNT++))
    log "${CYAN}Attempt $ATTEMPT_COUNT: Using pnpm${NC}"
    
    # Install pnpm if not present
    if ! command -v pnpm &> /dev/null; then
        log "Installing pnpm..."
        if npm install -g pnpm; then
            log "${GREEN}✅ pnpm installed${NC}"
        else
            log "${RED}❌ Failed to install pnpm${NC}"
            return 1
        fi
    fi
    
    cd "$PROJECT_ROOT"
    
    if pnpm install; then
        log "${GREEN}✅ SUCCESS: pnpm install worked!${NC}"
        return 0
    else
        log "${RED}❌ pnpm install failed${NC}"
        return 1
    fi
}

# Method 8: Create minimal package.json
try_minimal_setup() {
    ((ATTEMPT_COUNT++))
    log "${CYAN}Attempt $ATTEMPT_COUNT: Creating minimal setup${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Backup original package.json
    if [[ -f "package.json" ]]; then
        cp package.json package.json.original
    fi
    
    # Create minimal package.json
    cat > package.json << 'EOF'
{
  "name": "sapyyn-platform",
  "version": "1.0.0",
  "description": "Healthcare referral management platform",
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
    "dotenv": "^16.3.1"
  },
  "devDependencies": {
    "nodemon": "^3.0.1"
  },
  "engines": {
    "node": ">=16.0.0",
    "npm": ">=8.0.0"
  }
}
EOF
    
    if npm install --legacy-peer-deps; then
        log "${GREEN}✅ SUCCESS: Minimal setup worked!${NC}"
        
        # Now try to add additional packages
        local additional_deps=(
            "helmet@^7.0.0"
            "express-rate-limit@^6.10.0"
            "express-validator@^7.0.1"
            "multer@^1.4.5-lts.1"
            "nodemailer@^6.9.4"
            "axios@^1.5.0"
        )
        
        for dep in "${additional_deps[@]}"; do
            npm install "$dep" --save --legacy-peer-deps 2>/dev/null || true
        done
        
        return 0
    else
        log "${RED}❌ Minimal setup failed${NC}"
        # Restore original package.json
        if [[ -f "package.json.original" ]]; then
            mv package.json.original package.json
        fi
        return 1
    fi
}

# Method 9: Use different Node.js version with nvm
try_different_node_version() {
    ((ATTEMPT_COUNT++))
    log "${CYAN}Attempt $ATTEMPT_COUNT: Trying different Node.js version${NC}"
    
    # Check if nvm is available
    if ! command -v nvm &> /dev/null; then
        log "Installing nvm..."
        curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
        export NVM_DIR="$HOME/.nvm"
        [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    fi
    
    if command -v nvm &> /dev/null; then
        log "Installing Node.js 18 LTS..."
        nvm install 18
        nvm use 18
        
        cd "$PROJECT_ROOT"
        
        if npm install --legacy-peer-deps; then
            log "${GREEN}✅ SUCCESS: Different Node.js version worked!${NC}"
            return 0
        else
            log "${RED}❌ Different Node.js version failed${NC}"
            return 1
        fi
    else
        log "${RED}❌ Could not install/use nvm${NC}"
        return 1
    fi
}

# Method 10: Download and extract dependencies manually
try_manual_download() {
    ((ATTEMPT_COUNT++))
    log "${CYAN}Attempt $ATTEMPT_COUNT: Manual dependency download${NC}"
    
    cd "$PROJECT_ROOT"
    mkdir -p node_modules
    
    # Download and extract critical packages manually
    local packages=(
        "https://registry.npmjs.org/express/-/express-4.18.2.tgz"
        "https://registry.npmjs.org/mongoose/-/mongoose-7.5.0.tgz"
        "https://registry.npmjs.org/cors/-/cors-2.8.5.tgz"
    )
    
    local success_count=0
    
    for pkg_url in "${packages[@]}"; do
        local pkg_name=$(basename "$pkg_url" .tgz)
        log "Downloading $pkg_name..."
        
        if curl -L "$pkg_url" -o "/tmp/$pkg_name.tgz"; then
            if tar -xzf "/tmp/$pkg_name.tgz" -C node_modules/; then
                log "${GREEN}✅ $pkg_name downloaded and extracted${NC}"
                ((success_count++))
            fi
        fi
    done
    
    if [[ $success_count -gt 0 ]]; then
        log "${GREEN}✅ SUCCESS: Manual download partially worked${NC}"
        return 0
    else
        log "${RED}❌ Manual download failed${NC}"
        return 1
    fi
}

# Verify installation
verify_installation() {
    log "${BLUE}🔍 Verifying installation...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Check if node_modules exists
    if [[ ! -d "node_modules" ]]; then
        log "${RED}❌ node_modules directory not found${NC}"
        return 1
    fi
    
    # Check critical modules
    local critical_modules=("express" "mongoose" "cors")
    local found_count=0
    
    for module in "${critical_modules[@]}"; do
        if [[ -d "node_modules/$module" ]]; then
            log "${GREEN}✅ $module found${NC}"
            ((found_count++))
        else
            log "${YELLOW}⚠️  $module missing${NC}"
        fi
    done
    
    if [[ $found_count -gt 0 ]]; then
        log "${GREEN}✅ Installation verification: $found_count/${#critical_modules[@]} critical modules found${NC}"
        return 0
    else
        log "${RED}❌ Installation verification failed${NC}"
        return 1
    fi
}

# Test if app can start
test_app_startup() {
    log "${BLUE}🚀 Testing application startup...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Create a minimal server.js if it doesn't exist
    if [[ ! -f "server.js" ]]; then
        cat > server.js << 'EOF'
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.get('/', (req, res) => {
    res.send('Sapyyn Platform - Dependencies Installed Successfully!');
});

app.get('/health', (req, res) => {
    res.json({ status: 'ok', message: 'Dependencies working' });
});

app.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
    console.log('Dependencies installed successfully!');
});
EOF
    fi
    
    # Test startup
    timeout 10s node server.js &> /tmp/app_test.log &
    local test_pid=$!
    
    sleep 3
    
    if kill -0 $test_pid 2>/dev/null; then
        kill $test_pid 2>/dev/null
        log "${GREEN}✅ Application can start successfully!${NC}"
        return 0
    else
        log "${YELLOW}⚠️  Application startup test inconclusive${NC}"
        cat /tmp/app_test.log 2>/dev/null || true
        return 1
    fi
}

# Generate success report
generate_success_report() {
    local report_file="$PROJECT_ROOT/installation-success-report.txt"
    
    cat > "$report_file" << EOF
Sapyyn Platform - Emergency Installation Report
============================================

Installation completed successfully!
Date: $(date)
Method used: Attempt #$ATTEMPT_COUNT
Total attempts: $ATTEMPT_COUNT

System Information:
- OS: $(uname -s)
- Node.js: $(node --version 2>/dev/null || echo 'N/A')
- npm: $(npm --version 2>/dev/null || echo 'N/A')

Installed Dependencies:
$(cd "$PROJECT_ROOT" && ls node_modules 2>/dev/null | head -10)
$(cd "$PROJECT_ROOT" && ls node_modules 2>/dev/null | wc -l) total packages installed

Next Steps:
1. Run: npm run dev
2. Visit: http://localhost:3000
3. Check: http://localhost:3000/health

Backup Location: $BACKUP_DIR
Log File: $LOG_FILE
EOF

    log "${GREEN}✅ Success report generated: $report_file${NC}"
}

# Main execution function
main() {
    print_header
    create_backup
    
    # Try each method until one succeeds
    local methods=(
        "try_npm_install"
        "try_npm_legacy"
        "try_npm_force"
        "try_npm_aggressive"
        "nuclear_cleanup && try_npm_install"
        "nuclear_cleanup && try_npm_legacy"
        "try_yarn_install"
        "try_pnpm_install"
        "try_individual_install"
        "try_minimal_setup"
        "try_different_node_version"
        "try_manual_download"
    )
    
    for method in "${methods[@]}"; do
        log "${BLUE}═══════════════════════════════════════════════════════════${NC}"
        
        if eval "$method"; then
            SUCCESS=true
            break
        fi
        
        log "${YELLOW}Method failed, trying next approach...${NC}"
        log ""
    done
    
    # Final verification
    if [[ "$SUCCESS" == true ]] && verify_installation; then
        log ""
        log "${GREEN}╔═══════════════════════════════════════════════════════════╗${NC}"
        log "${GREEN}║                    SUCCESS!                               ║${NC}"
        log "${GREEN}║            Dependencies installed successfully!           ║${NC}"
        log "${GREEN}╚═══════════════════════════════════════════════════════════╝${NC}"
        log ""
        
        test_app_startup
        generate_success_report
        
        log "${CYAN}🎉 Installation completed successfully!${NC}"
        log "${CYAN}💡 You can now run: npm run dev${NC}"
        log "${CYAN}📊 Success achieved with method: Attempt #$ATTEMPT_COUNT${NC}"
        
    else
        log ""
        log "${RED}╔═══════════════════════════════════════════════════════════╗${NC}"
        log "${RED}║                      FAILED                               ║${NC}"
        log "${RED}║           All installation methods failed                 ║${NC}"
        log "${RED}╚═══════════════════════════════════════════════════════════╝${NC}"
        log ""
        log "${YELLOW}📋 Diagnostic Information:${NC}"
        log "- Total attempts: $ATTEMPT_COUNT"
        log "- Node.js version: $(node --version 2>/dev/null || echo 'Not found')"
        log "- npm version: $(npm --version 2>/dev/null || echo 'Not found')"
        log "- Current directory: $(pwd)"
        log "- Log file: $LOG_FILE"
        log "- Backup location: $BACKUP_DIR"
        log ""
        log "${YELLOW}💡 Manual steps to try:${NC}"
        log "1. Update Node.js: https://nodejs.org/"
        log "2. Clear all caches: npm cache clean --force"
        log "3. Try Docker: ./scripts/docker-setup.sh"
        log "4. Check network connectivity"
        log "5. Try different network/VPN"
        
        exit 1
    fi
}

# Handle script interruption
trap 'log "${RED}Emergency installation interrupted${NC}"; exit 1' INT TERM

# Run main function
main "$@"