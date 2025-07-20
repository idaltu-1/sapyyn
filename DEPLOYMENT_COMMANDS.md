# Sapyyn Deployment Commands & Guide

## 🚀 Quick Deployment Options

### Option 1: Netlify (Recommended for Frontend)
```bash
# 1. Install Netlify CLI
npm install -g netlify-cli

# 2. Login to Netlify
netlify login

# 3. Deploy to Netlify
netlify deploy --prod --dir=.

# Or use the build script
npm run build && netlify deploy --prod --dir=dist
```

### Option 2: Docker (Full Stack)
```bash
# 1. Build Docker image
docker build -t sapyyn-app .

# 2. Run with Docker Compose
docker-compose up -d

# 3. Access application
# Frontend: http://localhost:3000
# Backend: http://localhost:5000
```

### Option 3: Local Development
```bash
# 1. Install Python dependencies
pip3 install -r requirements.txt

# 2. Install Node dependencies (if using frontend build)
npm install

# 3. Initialize database
python3 -c "import app; app.init_db()"

# 4. Start Flask application
python3 app.py
# Access: http://localhost:5000
```

### Option 4: Production Server
```bash
# 1. Install dependencies
pip3 install -r requirements.txt

# 2. Set environment variables
cp .env.example .env
# Edit .env with production values

# 3. Initialize database
python3 -c "import app; app.init_db()"

# 4. Run with Gunicorn
gunicorn app:app -b 0.0.0.0:5000 --workers=4
```

## 📋 Pre-Deployment Checklist

### ✅ Environment Setup
- [x] Python 3.8+ installed
- [x] Node.js 16+ installed (for frontend)
- [x] All dependencies installed

### ✅ Configuration
- [x] `.env` file configured
- [x] Database initialized
- [x] Security settings configured
- [x] SSL certificates ready (for production)

### ✅ Files Ready
- [x] `requirements.txt` - Python dependencies
- [x] `package.json` - Node dependencies
- [x] `Dockerfile` - Container configuration
- [x] `docker-compose.yml` - Multi-service setup
- [x] `netlify.toml` - Netlify configuration
- [x] `_redirects` - URL routing rules

## 🌐 Deployment URLs

### Netlify Deployment
- **Production**: https://sapyyn.netlify.app
- **Deploy Preview**: https://deploy-preview-[PR#]--sapyyn.netlify.app

### Docker Deployment
- **Local**: http://localhost:5000
- **Production**: https://your-domain.com

### Local Development
- **Frontend**: http://localhost:3000
- **Backend**: http://localhost:5000

## 🔧 Environment Variables

### Required (.env file)
```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
DATABASE_URL=sqlite:///sapyyn.db

# Stripe Configuration
STRIPE_SECRET_KEY=sk_live_your_stripe_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_key

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-email-password

# Analytics
GA4_MEASUREMENT_ID=G-XXXXXXXXXX
ENABLE_ANALYTICS=true
```

## 🚀 One-Command Deployment

### Deploy to Netlify
```bash
# Single command deployment
npm run deploy:netlify
```

### Deploy with Docker
```bash
# Single command deployment
docker-compose up -d
```

### Deploy Locally
```bash
# Single command deployment
npm run dev
```

## 📊 Monitoring & Health Checks

### Health Check Endpoints
- `/health` - Application health
- `/api/health` - API health
- `/metrics` - Performance metrics

### Monitoring Commands
```bash
# Check if app is running
curl http://localhost:5000/health

# Check database connection
python3 -c "import app; print('Database OK')"

# Check logs
docker logs sapyyn-app
```

## 🔄 Continuous Deployment

### GitHub Actions (Auto-deploy)
```bash
# Push to main branch triggers deployment
git add .
git commit -m "Deploy to production"
git push origin main
```

### Manual Deployment
```bash
# Deploy specific branch
git push origin feature-branch:main
```

## 🎯 Quick Start Commands

### 1. Netlify (Fastest)
```bash
npm install -g netlify-cli
netlify deploy --prod --dir=.
```

### 2. Docker (Full Stack)
```bash
docker-compose up -d
```

### 3. Local (Development)
```bash
pip3 install -r requirements.txt
python3 -c "import app; app.init_db()"
python3 app.py
```

## 📞 Support Commands

### Debug Issues
```bash
# Check logs
docker-compose logs

# Check database
sqlite3 sapyyn.db ".tables"

# Check routes
python3 -c "import app; [print(r.rule) for r in app.app.url_map.iter_rules()]"
```

## ✅ Ready to Deploy

Choose your deployment method:

1. **Netlify**: `netlify deploy --prod --dir=.`
2. **Docker**: `docker-compose up -d`
3. **Local**: `python3 app.py`

All configurations are ready for immediate deployment!
