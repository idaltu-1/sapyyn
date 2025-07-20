#!/bin/bash

# Sapyyn Platform - Netlify Build Script
# Resolves dependency conflicts and ensures successful builds

set -e  # Exit on any error

echo "🚀 Starting Sapyyn build process..."

# Clean environment
echo "🧹 Cleaning environment..."
rm -rf .netlify
rm -rf __pycache__
rm -rf *.pyc

# Update pip to latest version
echo "📦 Updating pip..."
python3 -m pip install --upgrade pip

# Install build dependencies with compatible versions
echo "📋 Installing compatible dependencies..."
python3 -m pip install -r requirements-build.txt

# Verify installations
echo "✅ Verifying installations..."
python3 -c "import flask; print(f'Flask: {flask.__version__}')"
python3 -c "import gevent; print(f'Gevent: {gevent.__version__}')"
python3 -c "import PIL; print(f'Pillow: {PIL.__version__}')"

# Build static files if needed
echo "🏗️ Building static assets..."
if [ -d "static" ]; then
    echo "📁 Syncing static files..."
    rsync -av static/ . --exclude node_modules --exclude .git --exclude venv --exclude .venv
fi

echo "🎉 Build completed successfully!"
echo "📊 Build summary:"
echo "   • Python: $(python --version)"
echo "   • Pip: $(pip --version)"
echo "   • All dependencies installed successfully"
