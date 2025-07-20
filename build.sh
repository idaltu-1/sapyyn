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

# Check if Python dependencies are installed
echo "🐍 Checking Python dependencies..."
if ! python -c "import flask" &> /dev/null; then
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
fi

echo "✅ Build completed successfully!"
echo ""
echo "🚀 To start the application:"
echo "   python app.py"
echo ""
echo "🌐 The application will be available at:"
echo "   http://localhost:5001"
