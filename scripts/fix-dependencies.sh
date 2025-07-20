#!/bin/bash

# Sapyyn Platform - Dependency Installation Fix Script
# This script diagnoses and fixes common dependency installation issues

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="$PROJECT_ROOT/dependency-fix.log"
BACKUP_DIR="$PROJECT_ROOT/backups/$(date +%Y%m%d_%H%M%S)"

# Requirements
MIN_NODE_VERSION="16.0.0"
MIN_NPM_VERSION="8.0.0"
REQUIRED_SPACE_KB=1048576  # 1GB in KB

# Error tracking
ERROR_COUNT=0
ERROR_DETAILS=()

# Logging function
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Print header
print_header() {
    clear
    log "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    log "${BLUE}║                  Sapyyn Dependency Fix Tool                  ║${NC}"
    log "${BLUE}║              Diagnose & Fix Installation Issues              ║${NC}"
    log "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    log ""
    log "${YELLOW}Starting dependency fix process...${NC}"
    log "Log file: $LOG_FILE"
    log ""
}

# Check system requirements
check_system_requirements() {
    log "${BLUE}🔍 Checking system requirements...${NC}"
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        log "${RED}❌ Node.js not found${NC}"
        ((ERROR_COUNT++))
        ERROR_DETAILS+=("Node.js is not installed")
        return 1
    fi
    
    local node_version=$(node --version | sed 's/v//')
    if ! version_check "$node_version" "$MIN_NODE_VERSION"; then
        log "${RED}❌ Node.js version $node_version < $MIN_NODE_VERSION${NC}"
        ((ERROR_COUNT++))
        ERROR_DETAILS+=("Node.js version too old: $node_version")
    else
        log "${GREEN}✅ Node.js version: $node_version${NC}"
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        log "${RED}❌ npm not found${NC}"
        ((ERROR_COUNT++))
        ERROR_DETAILS+=("npm is not installed")
        return 1
    fi
    
    local npm_version=$(npm --version)
    if ! version_check "$npm_version" "$MIN_NPM_VERSION"; then
        log "${YELLOW}⚠️  npm version $npm_version < $MIN_NPM_VERSION (will update)${NC}"
    else
        log "${GREEN}✅ npm version: $npm_version${NC}"
    fi
    
    # Check disk space
    check_disk_space
    
    # Check network connectivity
    check_network_connectivity
    
    # Check permissions
    check_permissions
}

# Version comparison function
version_check() {
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

# Check available disk space
check_disk_space() {
    local available
    available=$(df --output=avail "$PROJECT_ROOT" 2>/dev/null | tail -1)
    if [[ -z "$available" || "$available" -lt "$REQUIRED_SPACE_KB" ]]; then
        log "${RED}❌ Insufficient disk space in $PROJECT_ROOT${NC}"
        ((ERROR_COUNT++))
        ERROR_DETAILS+=("Need at least 1GB free space")
        return 1
    else
        local space_gb=$((available / 1024 / 1024))
        log "${GREEN}✅ Available disk space: ${space_gb}GB${NC}"
    fi
}

# Check network connectivity
check_network_connectivity() {
    log "${BLUE}🌐 Checking network connectivity...${NC}"
    
    # Test npm registry
    if ! curl -s --max-time 10 https://registry.npmjs.org/ > /dev/null; then
        log "${RED}❌ Cannot reach npm registry${NC}"
        ((ERROR_COUNT++))
        ERROR_DETAILS+=("Network connectivity issue to npm registry")
    else
        log "${GREEN}✅ npm registry accessible${NC}"
    fi
    
    # Test GitHub (for some dependencies)
    if ! curl -s --max-time 10 https://github.com > /dev/null; then
        log "${YELLOW}⚠️  GitHub not accessible (some dependencies may fail)${NC}"
    else
        log "${GREEN}✅ GitHub accessible${NC}"
    fi
}

# Check file permissions
check_permissions() {
    log "${BLUE}🔐 Checking permissions...${NC}"
    
    if [[ ! -w "$PROJECT_ROOT" ]]; then
        log "${RED}❌ No write permission to project directory${NC}"
        ((ERROR_COUNT++))
        ERROR_DETAILS+=("No write permission to $PROJECT_ROOT")
        return 1
    fi
    
    # Check npm cache permissions
    local npm_cache=$(npm config get cache)
    if [[ ! -w "$npm_cache" ]]; then
        log "${YELLOW}⚠️  npm cache directory not writable: $npm_cache${NC}"
    else
        log "${GREEN}✅ npm cache writable${NC}"
    fi
    
    log "${GREEN}✅ Project directory writable${NC}"
}

# Create backup of existing files
create_backup() {
    log "${BLUE}💾 Creating backup...${NC}"
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup package files
    if [[ -f "$PROJECT_ROOT/package.json" ]]; then
        cp "$PROJECT_ROOT/package.json" "$BACKUP_DIR/"
        log "${GREEN}✅ Backed up package.json${NC}"
    fi
    
    if [[ -f "$PROJECT_ROOT/package-lock.json" ]]; then
        cp "$PROJECT_ROOT/package-lock.json" "$BACKUP_DIR/"
        log "${GREEN}✅ Backed up package-lock.json${NC}"
    fi
    
    if [[ -d "$PROJECT_ROOT/node_modules" ]]; then
        log "${YELLOW}⚠️  Large node_modules directory exists (not backing up)${NC}"
    fi
}

# Clean npm cache and temporary files
clean_npm_cache() {
    log "${BLUE}🧹 Cleaning npm cache and temporary files...${NC}"
    
    # Clear npm cache
    npm cache clean --force 2>/dev/null || log "${YELLOW}⚠️  Could not clean npm cache${NC}"
    
    # Remove node_modules
    if [[ -d "$PROJECT_ROOT/node_modules" ]]; then
        log "${YELLOW}Removing existing node_modules...${NC}"
        rm -rf "$PROJECT_ROOT/node_modules"
        log "${GREEN}✅ Removed node_modules${NC}"
    fi
    
    # Remove package-lock.json
    if [[ -f "$PROJECT_ROOT/package-lock.json" ]]; then
        log "${YELLOW}Removing package-lock.json...${NC}"
        rm -f "$PROJECT_ROOT/package-lock.json"
        log "${GREEN}✅ Removed package-lock.json${NC}"
    fi
    
    # Clear npm temporary files
    local npm_tmp=$(npm config get tmp)
    if [[ -d "$npm_tmp" ]]; then
        find "$npm_tmp" -name "npm-*" -type d -exec rm -rf {} + 2>/dev/null || true
    fi
    
    log "${GREEN}✅ Cleanup completed${NC}"
}

# Update npm to latest version
update_npm() {
    log "${BLUE}📦 Updating npm to latest version...${NC}"
    
    local current_npm=$(npm --version)
    
    # Update npm globally
    if npm install -g npm@latest; then
        local new_npm=$(npm --version)
        log "${GREEN}✅ npm updated from $current_npm to $new_npm${NC}"
    else
        log "${YELLOW}⚠️  Could not update npm globally, continuing with current version${NC}"
    fi
}

# Configure npm for better reliability
configure_npm() {
    log "${BLUE}⚙️  Configuring npm for better reliability...${NC}"
    
    # Set longer timeout
    npm config set timeout 120000
    
    # Set retries
    npm config set fetch-retries 5
    npm config set fetch-retry-mintimeout 20000
    npm config set fetch-retry-maxtimeout 120000
    
    # Use specific registry
    npm config set registry https://registry.npmjs.org/
    
    # Set audit level to avoid blocking on vulnerabilities
    npm config set audit-level moderate
    
    # Enable fund messages
    npm config set fund false
    
    log "${GREEN}✅ npm configured for better reliability${NC}"
}

# Install dependencies with multiple strategies
install_dependencies() {
    log "${BLUE}📦 Installing dependencies...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Strategy 1: Standard npm install
    log "${YELLOW}Strategy 1: Standard npm install${NC}"
    if npm install; then
        log "${GREEN}✅ Standard npm install successful${NC}"
        return 0
    else
        log "${RED}❌ Standard npm install failed${NC}"
    fi
    
    # Strategy 2: Install with --force
    log "${YELLOW}Strategy 2: npm install with --force${NC}"
    if npm install --force; then
        log "${GREEN}✅ npm install --force successful${NC}"
        return 0
    else
        log "${RED}❌ npm install --force failed${NC}"
    fi
    
    # Strategy 3: Install with --legacy-peer-deps
    log "${YELLOW}Strategy 3: npm install with --legacy-peer-deps${NC}"
    if npm install --legacy-peer-deps; then
        log "${GREEN}✅ npm install --legacy-peer-deps successful${NC}"
        return 0
    else
        log "${RED}❌ npm install --legacy-peer-deps failed${NC}"
    fi
    
    # Strategy 4: Install critical dependencies individually
    log "${YELLOW}Strategy 4: Installing critical dependencies individually${NC}"
    install_critical_dependencies
    
    # Strategy 5: Use yarn as fallback
    if command -v yarn &> /dev/null; then
        log "${YELLOW}Strategy 5: Trying with yarn${NC}"
        if yarn install; then
            log "${GREEN}✅ yarn install successful${NC}"
            return 0
        else
            log "${RED}❌ yarn install failed${NC}"
        fi
    fi
    
    log "${RED}❌ All installation strategies failed${NC}"
    return 1
}

# Install critical dependencies one by one
install_critical_dependencies() {
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
    )
    
    local critical_dev_deps=(
        "nodemon@^3.0.1"
    )
    
    log "${BLUE}Installing critical production dependencies...${NC}"
    for dep in "${critical_deps[@]}"; do
        log "Installing $dep..."
        if npm install "$dep" --save; then
            log "${GREEN}✅ $dep installed${NC}"
        else
            log "${RED}❌ Failed to install $dep${NC}"
            ((ERROR_COUNT++))
        fi
    done
    
    log "${BLUE}Installing critical development dependencies...${NC}"
    for dep in "${critical_dev_deps[@]}"; do
        log "Installing $dep..."
        if npm install "$dep" --save-dev; then
            log "${GREEN}✅ $dep installed${NC}"
        else
            log "${RED}❌ Failed to install $dep${NC}"
        fi
    done
}

# Fix common dependency issues
fix_common_issues() {
    log "${BLUE}🔧 Fixing common dependency issues...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Fix peer dependency issues
    if [[ -f "package.json" ]]; then
        log "Checking for peer dependency issues..."
        npm ls --depth=0 2>&1 | grep -E "(UNMET|missing)" && {
            log "${YELLOW}Found peer dependency issues, attempting to fix...${NC}"
            npm install --legacy-peer-deps
        } || log "${GREEN}No peer dependency issues found${NC}"
    fi
    
    # Fix node-gyp issues (common on Windows and some Linux systems)
    if npm ls node-gyp 2>/dev/null | grep -q "node-gyp"; then
        log "Rebuilding native dependencies..."
        npm rebuild 2>/dev/null || log "${YELLOW}Could not rebuild native dependencies${NC}"
    fi
    
    # Fix permission issues in node_modules
    if [[ -d "node_modules" ]]; then
        log "Fixing permissions in node_modules..."
        find node_modules -type d -exec chmod 755 {} + 2>/dev/null || true
        find node_modules -type f -exec chmod 644 {} + 2>/dev/null || true
    fi
}

# Verify installation
verify_installation() {
    log "${BLUE}✅ Verifying installation...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Check if package.json exists
    if [[ ! -f "package.json" ]]; then
        log "${RED}❌ package.json not found${NC}"
        return 1
    fi
    
    # Check if node_modules exists
    if [[ ! -d "node_modules" ]]; then
        log "${RED}❌ node_modules directory not found${NC}"
        return 1
    fi
    
    # Check critical dependencies
    local critical_modules=("express" "mongoose" "cors" "bcryptjs" "jsonwebtoken")
    for module in "${critical_modules[@]}"; do
        if [[ -d "node_modules/$module" ]]; then
            log "${GREEN}✅ $module installed${NC}"
        else
            log "${RED}❌ $module missing${NC}"
            ((ERROR_COUNT++))
        fi
    done
    
    # Try to run npm audit fix
    log "${BLUE}Running security audit...${NC}"
    npm audit fix --audit-level moderate 2>/dev/null || log "${YELLOW}Could not run audit fix${NC}"
    
    # Test if the application can start
    log "${BLUE}Testing application startup...${NC}"
    timeout 10s npm run dev 2>/dev/null && {
        log "${GREEN}✅ Application starts successfully${NC}"
    } || {
        log "${YELLOW}⚠️  Could not test application startup (this may be normal)${NC}"
    }
}

# Install alternative package managers
install_alternative_managers() {
    log "${BLUE}📦 Installing alternative package managers...${NC}"
    
    # Install yarn if not present
    if ! command -v yarn &> /dev/null; then
        log "Installing yarn..."
        if npm install -g yarn; then
            log "${GREEN}✅ yarn installed${NC}"
        else
            log "${YELLOW}⚠️  Could not install yarn${NC}"
        fi
    else
        log "${GREEN}✅ yarn already installed${NC}"
    fi
    
    # Install pnpm if not present
    if ! command -v pnpm &> /dev/null; then
        log "Installing pnpm..."
        if npm install -g pnpm; then
            log "${GREEN}✅ pnpm installed${NC}"
        else
            log "${YELLOW}⚠️  Could not install pnpm${NC}"
        fi
    else
        log "${GREEN}✅ pnpm already installed${NC}"
    fi
}

# Generate detailed report
generate_report() {
    local report_file="$PROJECT_ROOT/dependency-fix-report.txt"
    
    log "${BLUE}📊 Generating detailed report...${NC}"
    
    {
        echo "Sapyyn Dependency Fix Report"
        echo "Generated: $(date)"
        echo "==============================="
        echo ""
        
        echo "System Information:"
        echo "- OS: $(uname -s)"
        echo "- Node.js: $(node --version 2>/dev/null || echo 'Not installed')"
        echo "- npm: $(npm --version 2>/dev/null || echo 'Not installed')"
        echo "- yarn: $(yarn --version 2>/dev/null || echo 'Not installed')"
        echo "- pnpm: $(pnpm --version 2>/dev/null || echo 'Not installed')"
        echo ""
        
        echo "Project Information:"
        echo "- Project Root: $PROJECT_ROOT"
        echo "- Package.json: $(test -f "$PROJECT_ROOT/package.json" && echo "Found" || echo "Missing")"
        echo "- Node Modules: $(test -d "$PROJECT_ROOT/node_modules" && echo "Found" || echo "Missing")"
        echo ""
        
        echo "Errors Encountered: $ERROR_COUNT"
        if [[ ${#ERROR_DETAILS[@]} -gt 0 ]]; then
            echo "Error Details:"
            for error in "${ERROR_DETAILS[@]}"; do
                echo "- $error"
            done
        fi
        echo ""
        
        echo "Installed Dependencies:"
        if [[ -f "$PROJECT_ROOT/package.json" ]]; then
            cd "$PROJECT_ROOT"
            npm ls --depth=0 2>/dev/null || echo "Could not list dependencies"
        fi
        
    } > "$report_file"
    
    log "${GREEN}✅ Report generated: $report_file${NC}"
}

# Main execution
main() {
    print_header
    
    # Create log file
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "Dependency fix started at $(date)" > "$LOG_FILE"
    
    # Run diagnostic and fix steps
    check_system_requirements
    
    if [[ $ERROR_COUNT -gt 0 ]]; then
        log "${RED}❌ System requirements check failed with $ERROR_COUNT errors${NC}"
        log "${YELLOW}Attempting to fix issues...${NC}"
    fi
    
    create_backup
    clean_npm_cache
    update_npm
    configure_npm
    install_alternative_managers
    
    if install_dependencies; then
        log "${GREEN}✅ Dependencies installed successfully${NC}"
    else
        log "${RED}❌ Dependency installation failed${NC}"
        ((ERROR_COUNT++))
    fi
    
    fix_common_issues
    verify_installation
    generate_report
    
    # Final summary
    log ""
    log "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    log "${BLUE}║                        Summary                               ║${NC}"
    log "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    
    if [[ $ERROR_COUNT -eq 0 ]]; then
        log "${GREEN}🎉 All dependency issues have been resolved!${NC}"
        log "${GREEN}You can now run: npm run dev${NC}"
    else
        log "${RED}⚠️  $ERROR_COUNT issues remain. Check the report for details.${NC}"
        log "${YELLOW}Try running the script again or install dependencies manually.${NC}"
    fi
    
    log ""
    log "Log file: $LOG_FILE"
    log "Report: $PROJECT_ROOT/dependency-fix-report.txt"
    log "Backup: $BACKUP_DIR"
}

# Handle script interruption
trap 'log "${RED}Script interrupted${NC}"; exit 1' INT TERM

# Run main function
main "$@"