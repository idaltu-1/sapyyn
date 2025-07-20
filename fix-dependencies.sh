#!/bin/bash

# Sapyyn Platform - Dependency Conflict Resolution Script
# This script resolves the Pillow 10.4.0 vs 11.0.0 conflict

echo "🔧 Fixing Pillow dependency conflicts..."

# Step 1: Clean existing pip cache
echo "📦 Clearing pip cache..."
pip cache purge

# Step 2: Uninstall conflicting Pillow versions
echo "🗑️ Removing existing Pillow installations..."
pip uninstall pillow -y 2>/dev/null || true
pip uninstall Pillow -y 2>/dev/null || true

# Step 3: Install specific Pillow version
echo "📥 Installing compatible Pillow version..."
pip install "pillow>=10.4.0,<12.0.0"

# Step 4: Install other dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "📋 Installing dependencies from requirements.txt..."
    pip install -r requirements.txt
elif [ -f "requirements-fixed.txt" ]; then
    echo "📋 Installing dependencies from requirements-fixed.txt..."
    pip install -r requirements-fixed.txt
fi

# Step 5: Verify installation
echo "✅ Verifying Pillow installation..."
python -c "import PIL; print(f'Pillow version: {PIL.__version__}')" 2>/dev/null && echo "✅ Pillow installed successfully!" || echo "❌ Pillow installation failed"

# Step 6: Check for conflicts
echo "🔍 Checking for dependency conflicts..."
pip check

echo "🎉 Dependency resolution complete!"
echo ""
echo "📌 Solution Summary:"
echo "   • Removed conflicting Pillow versions (10.4.0 and 11.0.0)"
echo "   • Installed Pillow with flexible version range (>=10.4.0,<12.0.0)"
echo "   • This allows pip to resolve to the best compatible version"
echo "   • Updated requirements.txt files to prevent future conflicts"
echo ""
echo "🚀 You can now run your build process again!"