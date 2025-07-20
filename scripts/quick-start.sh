#!/bin/bash

# Sapyyn Platform - Quick Start Script
# One-command setup for development environment

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
    echo -e "${BLUE}║                    Sapyyn Quick Start                        ║${NC}"
    echo -e "${BLUE}║              One-Command Platform Setup                     ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}Welcome to Sapyyn! This script will set up everything for you.${NC}"
    echo ""
}

# Check prerequisites
check_prerequisites() {
    echo -e "${BLUE}🔍 Checking prerequisites...${NC}"
    
    local needs_install=false
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        echo -e "${YELLOW}⚠️  Node.js not found${NC}"
        needs_install=true
    else
        local node_version=$(node --version | sed 's/v//')
        if ! printf '%s\n%s\n' "16.0.0" "$node_version" | sort -V -C; then
            echo -e "${YELLOW}⚠️  Node.js version too old: $node_version${NC}"
            needs_install=true
        else
            echo -e "${GREEN}✅ Node.js version: $node_version${NC}"
        fi
    fi
    
    # Check npm
    if ! command -v npm &> /dev/null; then
        echo -e "${YELLOW}⚠️  npm not found${NC}"
        needs_install=true
    else
        echo -e "${GREEN}✅ npm version: $(npm --version)${NC}"
    fi
    
    if [[ "$needs_install" == true ]]; then
        echo -e "${YELLOW}Installing prerequisites...${NC}"
        if [[ -x "./scripts/install-prereqs.sh" ]]; then
            ./scripts/install-prereqs.sh
        else
            echo -e "${RED}❌ Prerequisites installer not found${NC}"
            echo -e "${YELLOW}Please install Node.js manually: https://nodejs.org/${NC}"
            exit 1
        fi
    fi
}

# Setup project
setup_project() {
    echo -e "${BLUE}📦 Setting up project...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Create environment file
    if [[ ! -f ".env" ]] && [[ -f ".env.example" ]]; then
        echo -e "${YELLOW}Creating .env file from template...${NC}"
        cp .env.example .env
        echo -e "${GREEN}✅ .env file created${NC}"
    fi
    
    # Install dependencies
    echo -e "${YELLOW}Installing dependencies...${NC}"
    
    # Try multiple installation strategies
    if npm install; then
        echo -e "${GREEN}✅ Dependencies installed successfully${NC}"
    elif npm install --legacy-peer-deps; then
        echo -e "${GREEN}✅ Dependencies installed with legacy peer deps${NC}"
    elif [[ -x "./scripts/fix-dependencies.sh" ]]; then
        echo -e "${YELLOW}Running dependency fix script...${NC}"
        ./scripts/fix-dependencies.sh
    else
        echo -e "${RED}❌ Dependency installation failed${NC}"
        exit 1
    fi
}

# Start the application
start_application() {
    echo -e "${BLUE}🚀 Starting Sapyyn platform...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Start in development mode
    echo -e "${YELLOW}Starting development server...${NC}"
    echo -e "${BLUE}Press Ctrl+C to stop the server${NC}"
    echo ""
    
    npm run dev
}

# Show quick start options
show_options() {
    echo -e "${BLUE}Choose your setup method:${NC}"
    echo ""
    echo "1) Quick Setup (Recommended) - Install and run locally"
    echo "2) Docker Setup - Run in containers"
    echo "3) Troubleshoot - Fix common issues"
    echo "4) Exit"
    echo ""
    read -p "Enter your choice (1-4): " choice
    
    case $choice in
        1)
            echo -e "${GREEN}Starting quick setup...${NC}"
            check_prerequisites
            setup_project
            start_application
            ;;
        2)
            echo -e "${GREEN}Starting Docker setup...${NC}"
            if [[ -x "./scripts/docker-setup.sh" ]]; then
                ./scripts/docker-setup.sh
            else
                echo -e "${RED}❌ Docker setup script not found${NC}"
            fi
            ;;
        3)
            echo -e "${GREEN}Running troubleshooter...${NC}"
            if [[ -x "./scripts/troubleshoot.sh" ]]; then
                ./scripts/troubleshoot.sh
            else
                echo -e "${RED}❌ Troubleshoot script not found${NC}"
            fi
            ;;
        4)
            echo -e "${YELLOW}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please try again.${NC}"
            show_options
            ;;
    esac
}

# Main execution
main() {
    print_header
    show_options
}

# Handle script interruption
trap 'echo -e "${RED}Quick start interrupted${NC}"; exit 1' INT TERM

# Run main function
main "$@"