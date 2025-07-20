#!/bin/bash

# Sapyyn Build Script
# This script installs dependencies and builds the frontend assets

echo "🔧 Building Sapyyn Patient Referral System..."

# Check if Node.js is installed
if ! command -v npm &> /dev/null; then
    echo "❌ Node.js and npm are required but not installed."
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
npm install

# Run the build process
echo "🏗️ Building frontend assets..."
npm run build

# Check if Python is available for Flask app (optional)
echo "🐍 Checking Python availability..."
if command -v python3 &> /dev/null; then
    echo "✅ Python3 is available"
    # Try to install Python dependencies, but don't fail if it doesn't work
    if [ -f requirements.txt ]; then
        echo "📦 Attempting to install Python dependencies..."
        python3 -m pip install -r requirements.txt --user --timeout 30 2>/dev/null || echo "⚠️  Python dependencies installation failed or timed out (this is optional)"
    fi
else
    echo "⚠️  Python3 not available (this is optional for Node.js mode)"
fi

echo "✅ Build completed successfully!"
echo ""
echo "🚀 To start the Node.js application:"
echo "   npm start"
echo ""
echo "🌐 The application will be available at:"
echo "   http://localhost:3000"
echo ""
echo "📁 Static files are served from the public/ directory"
