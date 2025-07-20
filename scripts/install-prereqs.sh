#!/bin/bash

# Sapyyn Platform - Prerequisites Installation Script
# Installs Node.js, npm, and other required tools

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
NODE_VERSION="18.17.1"  # LTS version
MIN_NODE_VERSION="16.0.0"

# Detect OS
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [[ -f /etc/debian_version ]]; then
            OS="debian"
        elif [[ -f /etc/redhat-release ]]; then
            OS="redhat"
        else
            OS="linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        OS="windows"
    else
        OS="unknown"
    fi
}

# Print header
print_header() {
    clear
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║              Sapyyn Prerequisites Installer                  ║${NC}"
    echo -e "${BLUE}║          Installing Node.js, npm, and dependencies          ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${YELLOW}Detected OS: $OS${NC}"
    echo ""
}

# Check if running as root (for Linux package managers)
check_root() {
    if [[ $EUID -eq 0 ]] && [[ "$OS" != "windows" ]]; then
        echo -e "${RED}Warning: Running as root. This may cause permission issues.${NC}"
        echo -e "${YELLOW}Consider running as a regular user.${NC}"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

# Install Node.js and npm
install_nodejs() {
    echo -e "${BLUE}📦 Installing Node.js and npm...${NC}"
    
    case $OS in
        "debian")
            install_nodejs_debian
            ;;
        "redhat")
            install_nodejs_redhat
            ;;
        "macos")
            install_nodejs_macos
            ;;
        "windows")
            install_nodejs_windows
            ;;
        *)
            install_nodejs_generic
            ;;
    esac
}

# Install Node.js on Debian/Ubuntu
install_nodejs_debian() {
    echo "Installing Node.js on Debian/Ubuntu..."
    
    # Update package list
    sudo apt-get update
    
    # Install curl if not present
    sudo apt-get install -y curl
    
    # Add NodeSource repository
    curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
    
    # Install Node.js
    sudo apt-get install -y nodejs
    
    # Install build essentials for native modules
    sudo apt-get install -y build-essential
    
    echo -e "${GREEN}✅ Node.js installed via apt${NC}"
}

# Install Node.js on RedHat/CentOS/Fedora
install_nodejs_redhat() {
    echo "Installing Node.js on RedHat/CentOS/Fedora..."
    
    # Install curl if not present
    if command -v dnf &> /dev/null; then
        sudo dnf install -y curl
        # Add NodeSource repository
        curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
        # Install Node.js
        sudo dnf install -y nodejs npm
        # Install development tools
        sudo dnf groupinstall -y "Development Tools"
    else
        sudo yum install -y curl
        # Add NodeSource repository
        curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
        # Install Node.js
        sudo yum install -y nodejs npm
        # Install development tools
        sudo yum groupinstall -y "Development Tools"
    fi
    
    echo -e "${GREEN}✅ Node.js installed via package manager${NC}"
}

# Install Node.js on macOS
install_nodejs_macos() {
    echo "Installing Node.js on macOS..."
    
    # Check if Homebrew is installed
    if command -v brew &> /dev/null; then
        echo "Using Homebrew to install Node.js..."
        brew install node
        echo -e "${GREEN}✅ Node.js installed via Homebrew${NC}"
    else
        echo "Homebrew not found. Installing using NVM..."
        install_nodejs_nvm
    fi
}

# Install Node.js on Windows (via chocolatey or manual)
install_nodejs_windows() {
    echo "Installing Node.js on Windows..."
    
    if command -v choco &> /dev/null; then
        echo "Using Chocolatey to install Node.js..."
        choco install nodejs -y
        echo -e "${GREEN}✅ Node.js installed via Chocolatey${NC}"
    else
        echo -e "${YELLOW}Please install Node.js manually from: https://nodejs.org/${NC}"
        echo -e "${YELLOW}Or install Chocolatey first: https://chocolatey.org/install${NC}"
        exit 1
    fi
}

# Generic installation using NVM
install_nodejs_generic() {
    echo "Using NVM for Node.js installation..."
    install_nodejs_nvm
}

# Install Node.js using NVM (Node Version Manager)
install_nodejs_nvm() {
    echo "Installing Node.js using NVM..."
    
    # Install NVM
    curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
    
    # Source NVM
    export NVM_DIR="$HOME/.nvm"
    [ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"
    [ -s "$NVM_DIR/bash_completion" ] && \. "$NVM_DIR/bash_completion"
    
    # Install Node.js
    nvm install $NODE_VERSION
    nvm use $NODE_VERSION
    nvm alias default $NODE_VERSION
    
    echo -e "${GREEN}✅ Node.js installed via NVM${NC}"
}

# Verify Node.js installation
verify_nodejs() {
    echo -e "${BLUE}🔍 Verifying Node.js installation...${NC}"
    
    # Check Node.js
    if command -v node &> /dev/null; then
        local node_version=$(node --version | sed 's/v//')
        echo -e "${GREEN}✅ Node.js version: $node_version${NC}"
        
        # Check if version meets requirements
        if ! printf '%s\n%s\n' "$MIN_NODE_VERSION" "$node_version" | sort -V -C; then
            echo -e "${RED}❌ Node.js version too old. Minimum required: $MIN_NODE_VERSION${NC}"
            return 1
        fi
    else
        echo -e "${RED}❌ Node.js not found${NC}"
        return 1
    fi
    
    # Check npm
    if command -v npm &> /dev/null; then
        local npm_version=$(npm --version)
        echo -e "${GREEN}✅ npm version: $npm_version${NC}"
    else
        echo -e "${RED}❌ npm not found${NC}"
        return 1
    fi
}

# Install additional development tools
install_dev_tools() {
    echo -e "${BLUE}🛠️  Installing additional development tools...${NC}"
    
    # Install global npm packages
    npm install -g nodemon@latest
    npm install -g pm2@latest
    
    case $OS in
        "debian")
            sudo apt-get install -y git python3 python3-pip
            ;;
        "redhat")
            if command -v dnf &> /dev/null; then
                sudo dnf install -y git python3 python3-pip
            else
                sudo yum install -y git python3 python3-pip
            fi
            ;;
        "macos")
            if command -v brew &> /dev/null; then
                brew install git python3
            fi
            ;;
        "windows")
            if command -v choco &> /dev/null; then
                choco install git python3 -y
            fi
            ;;
    esac
    
    echo -e "${GREEN}✅ Development tools installed${NC}"
}

# Set up npm configuration
setup_npm_config() {
    echo -e "${BLUE}⚙️  Configuring npm...${NC}"
    
    # Set npm configuration for better performance and reliability
    npm config set timeout 120000
    npm config set fetch-retries 5
    npm config set fetch-retry-mintimeout 20000
    npm config set fetch-retry-maxtimeout 120000
    npm config set registry https://registry.npmjs.org/
    npm config set audit-level moderate
    npm config set fund false
    
    echo -e "${GREEN}✅ npm configured${NC}"
}

# Install Docker (optional)
install_docker() {
    echo -e "${BLUE}🐳 Installing Docker (optional)...${NC}"
    
    read -p "Install Docker? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        return 0
    fi
    
    case $OS in
        "debian")
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
            ;;
        "redhat")
            curl -fsSL https://get.docker.com -o get-docker.sh
            sudo sh get-docker.sh
            sudo usermod -aG docker $USER
            rm get-docker.sh
            ;;
        "macos")
            echo "Please install Docker Desktop from: https://docs.docker.com/desktop/install/mac-install/"
            ;;
        "windows")
            echo "Please install Docker Desktop from: https://docs.docker.com/desktop/install/windows-install/"
            ;;
    esac
    
    echo -e "${GREEN}✅ Docker installation initiated${NC}"
}

# Create environment file template
create_env_template() {
    echo -e "${BLUE}📄 Creating environment file template...${NC}"
    
    local env_file="../.env"
    
    if [[ ! -f "$env_file" ]] && [[ -f "../.env.example" ]]; then
        cp "../.env.example" "$env_file"
        echo -e "${GREEN}✅ .env file created from template${NC}"
        echo -e "${YELLOW}Please edit .env file with your configuration${NC}"
    else
        echo -e "${YELLOW}⚠️  .env file already exists or .env.example not found${NC}"
    fi
}

# Final setup instructions
print_final_instructions() {
    echo ""
    echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║                    Installation Complete                     ║${NC}"
    echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${GREEN}🎉 Prerequisites installed successfully!${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Restart your terminal or run: source ~/.bashrc"
    echo "2. Navigate to the project directory"
    echo "3. Run: npm install"
    echo "4. Configure your .env file"
    echo "5. Run: npm run dev"
    echo ""
    echo -e "${BLUE}Useful commands:${NC}"
    echo "- Check Node.js version: node --version"
    echo "- Check npm version: npm --version"
    echo "- Install dependencies: npm install"
    echo "- Start development server: npm run dev"
    echo "- Run dependency fix script: ./scripts/fix-dependencies.sh"
    echo ""
}

# Main execution
main() {
    detect_os
    print_header
    check_root
    
    # Check if Node.js is already installed and meets requirements
    if command -v node &> /dev/null; then
        local current_version=$(node --version | sed 's/v//')
        if printf '%s\n%s\n' "$MIN_NODE_VERSION" "$current_version" | sort -V -C; then
            echo -e "${GREEN}✅ Node.js $current_version already installed and meets requirements${NC}"
            verify_nodejs
            setup_npm_config
            create_env_template
            print_final_instructions
            return 0
        else
            echo -e "${YELLOW}⚠️  Node.js $current_version is too old, upgrading...${NC}"
        fi
    fi
    
    install_nodejs
    verify_nodejs
    install_dev_tools
    setup_npm_config
    install_docker
    create_env_template
    print_final_instructions
}

# Handle script interruption
trap 'echo -e "${RED}Installation interrupted${NC}"; exit 1' INT TERM

# Run main function
main "$@"