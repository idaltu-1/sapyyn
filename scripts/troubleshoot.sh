#!/bin/bash

# Sapyyn Platform - Troubleshooting Script
# Diagnoses and provides solutions for common issues

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
LOG_FILE="$PROJECT_ROOT/troubleshoot.log"

# Issue tracking
ISSUES_FOUND=0
FIXES_APPLIED=0

# Logging function
log() {
    echo -e "$1" | tee -a "$LOG_FILE"
}

# Print header
print_header() {
    clear
    log "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    log "${BLUE}║                  Sapyyn Troubleshooting Tool                 ║${NC}"
    log "${BLUE}║              Diagnose and Fix Common Issues                  ║${NC}"
    log "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    log ""
    log "${YELLOW}Analyzing system and project...${NC}"
    log ""
}

# Check if Node.js and npm are working
check_nodejs_npm() {
    log "${BLUE}🔍 Checking Node.js and npm...${NC}"
    
    if ! command -v node &> /dev/null; then
        log "${RED}❌ Node.js not found${NC}"
        log "${YELLOW}💡 Solution: Run ./scripts/install-prereqs.sh${NC}"
        ((ISSUES_FOUND++))
        return 1
    fi
    
    if ! command -v npm &> /dev/null; then
        log "${RED}❌ npm not found${NC}"
        log "${YELLOW}💡 Solution: Reinstall Node.js which includes npm${NC}"
        ((ISSUES_FOUND++))
        return 1
    fi
    
    # Test npm
    if ! npm --version &> /dev/null; then
        log "${RED}❌ npm not working properly${NC}"
        log "${YELLOW}💡 Solution: Try 'npm cache clean --force' or reinstall npm${NC}"
        ((ISSUES_FOUND++))
        return 1
    fi
    
    log "${GREEN}✅ Node.js and npm are working${NC}"
    return 0
}

# Check project structure
check_project_structure() {
    log "${BLUE}🔍 Checking project structure...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Check package.json
    if [[ ! -f "package.json" ]]; then
        log "${RED}❌ package.json not found${NC}"
        log "${YELLOW}💡 Solution: Ensure you're in the correct project directory${NC}"
        ((ISSUES_FOUND++))
        return 1
    fi
    
    # Check server.js
    if [[ ! -f "server.js" ]]; then
        log "${RED}❌ server.js not found${NC}"
        log "${YELLOW}💡 Solution: Ensure all project files are present${NC}"
        ((ISSUES_FOUND++))
    fi
    
    # Check frontend directory
    if [[ ! -d "frontend" ]]; then
        log "${YELLOW}⚠️  frontend directory not found${NC}"
        log "${YELLOW}💡 Note: This might be expected if using a different structure${NC}"
    fi
    
    log "${GREEN}✅ Project structure looks good${NC}"
    return 0
}

# Check dependencies
check_dependencies() {
    log "${BLUE}🔍 Checking dependencies...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Check node_modules
    if [[ ! -d "node_modules" ]]; then
        log "${RED}❌ node_modules directory not found${NC}"
        log "${YELLOW}💡 Solution: Run 'npm install' to install dependencies${NC}"
        ((ISSUES_FOUND++))
        return 1
    fi
    
    # Check critical dependencies
    local critical_deps=("express" "mongoose" "cors" "bcryptjs" "jsonwebtoken")
    for dep in "${critical_deps[@]}"; do
        if [[ ! -d "node_modules/$dep" ]]; then
            log "${RED}❌ Critical dependency missing: $dep${NC}"
            log "${YELLOW}💡 Solution: Run 'npm install $dep' or './scripts/fix-dependencies.sh'${NC}"
            ((ISSUES_FOUND++))
        fi
    done
    
    # Check for dependency conflicts
    if npm ls --depth=0 2>&1 | grep -q "UNMET DEPENDENCY\|missing"; then
        log "${YELLOW}⚠️  Dependency conflicts detected${NC}"
        log "${YELLOW}💡 Solution: Run 'npm install --legacy-peer-deps' or fix manually${NC}"
        ((ISSUES_FOUND++))
    fi
    
    log "${GREEN}✅ Dependencies check completed${NC}"
    return 0
}

# Check environment configuration
check_environment() {
    log "${BLUE}🔍 Checking environment configuration...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Check .env file
    if [[ ! -f ".env" ]]; then
        if [[ -f ".env.example" ]]; then
            log "${YELLOW}⚠️  .env file not found, but .env.example exists${NC}"
            log "${YELLOW}💡 Solution: Copy .env.example to .env and configure${NC}"
            
            read -p "Create .env from .env.example now? (y/N): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                cp .env.example .env
                log "${GREEN}✅ Created .env from template${NC}"
                ((FIXES_APPLIED++))
            fi
        else
            log "${RED}❌ No .env or .env.example file found${NC}"
            log "${YELLOW}💡 Solution: Create .env file with required environment variables${NC}"
        fi
        ((ISSUES_FOUND++))
    else
        log "${GREEN}✅ .env file found${NC}"
    fi
    
    return 0
}

# Check port availability
check_port_availability() {
    log "${BLUE}🔍 Checking port availability...${NC}"
    
    local port=3000
    
    # Check if port is in use
    if command -v lsof &> /dev/null; then
        if lsof -i :$port &> /dev/null; then
            log "${YELLOW}⚠️  Port $port is already in use${NC}"
            log "${YELLOW}💡 Solution: Stop the process using port $port or use a different port${NC}"
            
            # Show what's using the port
            local process_info=$(lsof -i :$port | tail -n +2)
            log "${BLUE}Process using port $port:${NC}"
            log "$process_info"
            
            ((ISSUES_FOUND++))
        else
            log "${GREEN}✅ Port $port is available${NC}"
        fi
    elif command -v netstat &> /dev/null; then
        if netstat -tuln | grep ":$port " &> /dev/null; then
            log "${YELLOW}⚠️  Port $port might be in use${NC}"
            log "${YELLOW}💡 Solution: Check for processes using port $port${NC}"
            ((ISSUES_FOUND++))
        else
            log "${GREEN}✅ Port $port appears available${NC}"
        fi
    else
        log "${YELLOW}⚠️  Cannot check port availability (lsof/netstat not found)${NC}"
    fi
    
    return 0
}

# Check database connectivity (if MongoDB is configured)
check_database() {
    log "${BLUE}🔍 Checking database connectivity...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Check if MongoDB URI is configured
    if [[ -f ".env" ]]; then
        local mongodb_uri=$(grep "MONGODB_URI" .env | cut -d'=' -f2)
        if [[ -n "$mongodb_uri" ]]; then
            log "${GREEN}✅ MongoDB URI configured${NC}"
            
            # Try to connect (basic check)
            if command -v mongosh &> /dev/null; then
                if mongosh "$mongodb_uri" --eval "db.runCommand('ping')" &> /dev/null; then
                    log "${GREEN}✅ MongoDB connection successful${NC}"
                else
                    log "${RED}❌ Cannot connect to MongoDB${NC}"
                    log "${YELLOW}💡 Solution: Check MongoDB server status and URI${NC}"
                    ((ISSUES_FOUND++))
                fi
            elif command -v mongo &> /dev/null; then
                if mongo "$mongodb_uri" --eval "db.runCommand('ping')" &> /dev/null; then
                    log "${GREEN}✅ MongoDB connection successful${NC}"
                else
                    log "${RED}❌ Cannot connect to MongoDB${NC}"
                    log "${YELLOW}💡 Solution: Check MongoDB server status and URI${NC}"
                    ((ISSUES_FOUND++))
                fi
            else
                log "${YELLOW}⚠️  MongoDB client not found, cannot test connection${NC}"
                log "${YELLOW}💡 Note: Install mongodb-tools to test connectivity${NC}"
            fi
        else
            log "${YELLOW}⚠️  MongoDB URI not configured in .env${NC}"
            log "${YELLOW}💡 Solution: Add MONGODB_URI to your .env file${NC}"
        fi
    fi
    
    return 0
}

# Check file permissions
check_permissions() {
    log "${BLUE}🔍 Checking file permissions...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Check if project directory is writable
    if [[ ! -w "." ]]; then
        log "${RED}❌ Project directory is not writable${NC}"
        log "${YELLOW}💡 Solution: Fix directory permissions or run as appropriate user${NC}"
        ((ISSUES_FOUND++))
        return 1
    fi
    
    # Check npm cache permissions
    local npm_cache=$(npm config get cache 2>/dev/null || echo "$HOME/.npm")
    if [[ ! -w "$npm_cache" ]]; then
        log "${YELLOW}⚠️  npm cache directory not writable: $npm_cache${NC}"
        log "${YELLOW}💡 Solution: Fix npm cache permissions or clear cache${NC}"
        ((ISSUES_FOUND++))
    fi
    
    log "${GREEN}✅ File permissions look good${NC}"
    return 0
}

# Test application startup
test_application_startup() {
    log "${BLUE}🔍 Testing application startup...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Check if we can start the application
    log "${YELLOW}Attempting to start application (10 second timeout)...${NC}"
    
    # Start the application in background with timeout
    timeout 10s npm start &> /tmp/sapyyn_startup_test.log &
    local start_pid=$!
    
    sleep 5
    
    # Check if process is still running
    if kill -0 $start_pid 2>/dev/null; then
        log "${GREEN}✅ Application starts successfully${NC}"
        kill $start_pid 2>/dev/null || true
        return 0
    else
        log "${RED}❌ Application failed to start${NC}"
        log "${YELLOW}💡 Check startup logs:${NC}"
        cat /tmp/sapyyn_startup_test.log | head -20
        log "${YELLOW}💡 Solution: Check error messages above and fix configuration${NC}"
        ((ISSUES_FOUND++))
        return 1
    fi
}

# Suggest fixes for common issues
suggest_fixes() {
    log "${BLUE}💡 Automated fix suggestions:${NC}"
    
    if [[ $ISSUES_FOUND -gt 0 ]]; then
        log "${YELLOW}The following commands might help resolve issues:${NC}"
        log ""
        log "${BLUE}1. Fix dependencies:${NC}"
        log "   ./scripts/fix-dependencies.sh"
        log ""
        log "${BLUE}2. Clean install:${NC}"
        log "   rm -rf node_modules package-lock.json && npm install"
        log ""
        log "${BLUE}3. Install with legacy peer deps:${NC}"
        log "   npm install --legacy-peer-deps"
        log ""
        log "${BLUE}4. Update npm:${NC}"
        log "   npm install -g npm@latest"
        log ""
        log "${BLUE}5. Clear npm cache:${NC}"
        log "   npm cache clean --force"
        log ""
        
        read -p "Would you like to run the dependency fix script now? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log "${YELLOW}Running dependency fix script...${NC}"
            if [[ -x "./scripts/fix-dependencies.sh" ]]; then
                ./scripts/fix-dependencies.sh
                ((FIXES_APPLIED++))
            else
                log "${RED}❌ fix-dependencies.sh not found or not executable${NC}"
            fi
        fi
    fi
}

# Generate troubleshooting report
generate_report() {
    local report_file="$PROJECT_ROOT/troubleshoot-report.txt"
    
    log "${BLUE}📊 Generating troubleshooting report...${NC}"
    
    {
        echo "Sapyyn Troubleshooting Report"
        echo "Generated: $(date)"
        echo "=============================="
        echo ""
        
        echo "System Information:"
        echo "- OS: $(uname -s) $(uname -r)"
        echo "- Node.js: $(node --version 2>/dev/null || echo 'Not installed')"
        echo "- npm: $(npm --version 2>/dev/null || echo 'Not installed')"
        echo "- Git: $(git --version 2>/dev/null || echo 'Not installed')"
        echo ""
        
        echo "Project Information:"
        echo "- Project Root: $PROJECT_ROOT"
        echo "- Package.json: $(test -f "$PROJECT_ROOT/package.json" && echo "Found" || echo "Missing")"
        echo "- Node Modules: $(test -d "$PROJECT_ROOT/node_modules" && echo "Found" || echo "Missing")"
        echo "- Environment File: $(test -f "$PROJECT_ROOT/.env" && echo "Found" || echo "Missing")"
        echo ""
        
        echo "Issues Summary:"
        echo "- Issues Found: $ISSUES_FOUND"
        echo "- Fixes Applied: $FIXES_APPLIED"
        echo ""
        
        if [[ -f "$PROJECT_ROOT/package.json" ]]; then
            echo "Dependencies Status:"
            cd "$PROJECT_ROOT"
            npm ls --depth=0 2>&1 | head -20
            echo ""
        fi
        
        echo "Recent Logs:"
        tail -50 "$LOG_FILE" 2>/dev/null || echo "No log entries"
        
    } > "$report_file"
    
    log "${GREEN}✅ Report generated: $report_file${NC}"
}

# Main execution
main() {
    print_header
    
    # Create log file
    mkdir -p "$(dirname "$LOG_FILE")"
    echo "Troubleshooting started at $(date)" > "$LOG_FILE"
    
    # Run all checks
    check_nodejs_npm
    check_project_structure
    check_dependencies
    check_environment
    check_port_availability
    check_database
    check_permissions
    test_application_startup
    
    # Provide solutions
    suggest_fixes
    generate_report
    
    # Final summary
    log ""
    log "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    log "${BLUE}║                     Troubleshooting Summary                  ║${NC}"
    log "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    
    if [[ $ISSUES_FOUND -eq 0 ]]; then
        log "${GREEN}🎉 No issues found! Your Sapyyn platform should work correctly.${NC}"
        log "${GREEN}Try running: npm run dev${NC}"
    else
        log "${YELLOW}⚠️  Found $ISSUES_FOUND potential issues.${NC}"
        log "${GREEN}Applied $FIXES_APPLIED automatic fixes.${NC}"
        log "${BLUE}Check the report for detailed information: troubleshoot-report.txt${NC}"
    fi
    
    log ""
    log "Log file: $LOG_FILE"
    log "Report: $PROJECT_ROOT/troubleshoot-report.txt"
}

# Handle script interruption
trap 'log "${RED}Troubleshooting interrupted${NC}"; exit 1' INT TERM

# Run main function
main "$@"