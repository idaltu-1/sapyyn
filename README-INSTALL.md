# 🚨 Dependency Installation Fix Guide

If you're experiencing dependency installation failures, this guide provides multiple solutions.

## 🚀 Quick Solutions (Try These First)

### 1. Quick Fix Script (Recommended)
```bash
chmod +x scripts/*.sh
./scripts/quick-fix.sh
```

### 2. Manual Quick Fix
```bash
# Clear everything and retry
rm -rf node_modules package-lock.json
npm cache clean --force
npm install --legacy-peer-deps
```

### 3. Use Yarn Instead
```bash
npm install -g yarn
yarn install
```

## 🆘 Emergency Solutions

### 1. Emergency Installer (Nuclear Option)
```bash
./scripts/emergency-install.sh
```
This script tries 12 different installation methods until one works.

### 2. Docker Solution (Isolation)
```bash
./scripts/docker-setup.sh
```
Runs everything in containers to avoid local dependency issues.

### 3. Diagnose Issues First
```bash
./scripts/diagnose.sh
```
Identifies what's causing the installation to fail.

## 🔧 Manual Troubleshooting

### Check Node.js Version
```bash
node --version  # Should be 14.0.0 or higher
npm --version   # Should be 6.0.0 or higher
```

### Clear All Caches
```bash
npm cache clean --force
rm -rf ~/.npm
rm -rf node_modules
rm -f package-lock.json
```

### Try Different Methods
```bash
# Method 1: Legacy peer deps
npm install --legacy-peer-deps

# Method 2: Force install
npm install --force

# Method 3: No audit/fund
npm install --no-audit --no-fund

# Method 4: Production only
npm install --only=production
```

## 🐳 Docker Alternative

If all else fails, use Docker:
```bash
# Quick Docker setup
docker run -it -v "$(pwd)":/app -w /app node:18 npm install
```

## 📋 Common Issues & Solutions

### Permission Errors
```bash
sudo chown -R $(whoami) ~/.npm
sudo chown -R $(whoami) /usr/local/lib/node_modules
```

### Network/Proxy Issues
```bash
npm config set registry https://registry.npmjs.org/
npm config delete proxy
npm config delete https-proxy
```

### Disk Space Issues
```bash
df -h  # Check available space
npm cache clean --force  # Free up cache space
```

## ✅ Verify Installation

After any fix, verify it worked:
```bash
npm run dev
# Should start server on http://localhost:3000
```

## 🆘 Still Having Issues?

1. **Run the diagnostic**: `./scripts/diagnose.sh`
2. **Check the logs**: Look at error messages carefully
3. **Try different network**: Switch WiFi/use mobile hotspot
4. **Update Node.js**: Install latest LTS from nodejs.org
5. **Use Docker**: Completely isolate the environment

## 📞 Emergency Contacts

If nothing works:
1. Create a GitHub issue with full error log
2. Include output from `./scripts/diagnose.sh`
3. Mention your OS and Node.js version

---

**🎯 Success Indicator**: You should see "✅ Dependencies installation successful!" when it works.