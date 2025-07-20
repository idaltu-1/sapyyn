# Sapyyn Patient Referral System - Deployment Guide

## Overview
This guide provides step-by-step instructions for deploying the Sapyyn Patient Referral System in various environments.

## Prerequisites

### System Requirements
- Python 3.8 or higher
- SQLite 3.0 or higher
- Redis (for rate limiting)
- Git

### Environment Setup
1. **Clone the repository:**
   ```bash
   git clone https://github.com/idaltu-1/sapyyn.git
   cd sapyyn
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### 1. Environment Variables
Copy the example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your actual values:
```bash
# Required - Change these values
SECRET_KEY=your-very-secure-secret-key-here
STRIPE_SECRET_KEY=sk_live_your_stripe_secret_key
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable_key
NOCODEBACKEND_SECRET_KEY=your_nocodebackend_secret_key

# Optional - Update as needed
DATABASE_NAME=sapyyn.db
BASE_URL=https://yourdomain.com
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_email_password
```

### 2. Database Initialization
```bash
python -c "from app import init_db; init_db()"
```

### 3. Create Admin User
The system automatically creates an initial admin user on first run. Check the logs for the generated password.

## Deployment Options

### Option 1: Local Development
```bash
python app.py
```
Access at: http://localhost:5000

### Option 2: Docker Deployment

#### Using Docker Compose
```bash
docker-compose up -d
```

#### Manual Docker Build
```bash
docker build -t sapyyn:latest .
docker run -d -p 5000:5000 --env-file .env sapyyn:latest
```

### Option 3: Production Deployment

#### Using Gunicorn
```bash
gunicorn app:app -w 4 -b 0.0.0.0:5000 --timeout 120
```

#### Using systemd (Linux)
Create `/etc/systemd/system/sapyyn.service`:
```ini
[Unit]
Description=Sapyyn Patient Referral System
After=network.target

[Service]
Type=exec
User=sapyyn
WorkingDirectory=/opt/sapyyn
Environment="PATH=/opt/sapyyn/venv/bin"
ExecStart=/opt/sapyyn/venv/bin/gunicorn app:app -w 4 -b 0.0.0.0:5000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable sapyyn
sudo systemctl start sapyyn
```

### Option 4: Cloud Deployment

#### Heroku
1. Create `Procfile`:
   ```
   web: gunicorn app:app
   ```

2. Deploy:
   ```bash
   heroku create your-app-name
   git push heroku main
   heroku config:set SECRET_KEY=your-secret-key
   ```

#### AWS EC2
1. Launch EC2 instance (Ubuntu 20.04+)
2. Install dependencies:
   ```bash
   sudo apt update && sudo apt install python3-pip python3-venv nginx redis-server
   ```
3. Follow production deployment steps above
4. Configure Nginx reverse proxy

#### DigitalOcean App Platform
1. Create `.do/app.yaml`:
   ```yaml
   name: sapyyn
   services:
   - name: web
     source_dir: /
     environment_slug: python
     run_command: gunicorn app:app
     envs:
     - key: SECRET_KEY
       scope: RUN_AND_BUILD_TIME
       value: ${SECRET_KEY}
   ```

## Security Configuration

### 1. SSL/TLS Setup
- Use Let's Encrypt for free SSL certificates
- Configure automatic renewal

### 2. Firewall Configuration
```bash
# UFW (Ubuntu)
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Rate Limiting
Configure Redis for rate limiting:
```bash
sudo systemctl start redis
sudo systemctl enable redis
```

## Monitoring & Logging

### 1. Application Monitoring
- Set up Sentry for error tracking
- Configure log rotation

### 2. Health Checks
Add health check endpoint:
```bash
curl https://yourdomain.com/health
```

### 3. Backup Strategy
```bash
# Database backup
sqlite3 sapyyn.db .dump > backup_$(date +%Y%m%d_%H%M%S).sql

# Automated backup script
0 2 * * * /opt/sapyyn/backup.sh
```

## Environment-Specific Configurations

### Development
```bash
FLASK_ENV=development
DEBUG=true
```

### Staging
```bash
FLASK_ENV=production
DEBUG=false
```

### Production
```bash
FLASK_ENV=production
DEBUG=false
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
```

## Database Migration

### Adding New Tables
1. Update `init_db()` function in app.py
2. Run migration:
   ```bash
   python -c "from app import init_db; init_db()"
   ```

### Backup Before Migration
```bash
cp sapyyn.db sapyyn.db.backup
```

## Troubleshooting

### Common Issues

1. **Port already in use:**
   ```bash
   lsof -i :5000
   kill -9 <PID>
   ```

2. **Permission denied:**
   ```bash
   chmod +x app.py
   ```

3. **Database locked:**
   ```bash
   fuser sapyyn.db
   ```

4. **Redis connection failed:**
   ```bash
   sudo systemctl restart redis
   ```

### Log Locations
- Application logs: `/var/log/sapyyn/`
- Nginx logs: `/var/log/nginx/`
- System logs: `/var/log/syslog`

## Performance Optimization

### 1. Database Optimization
```sql
-- Create indexes
CREATE INDEX idx_referrals_user_id ON referrals(user_id);
CREATE INDEX idx_referrals_status ON referrals(status);
CREATE INDEX idx_users_email ON users(email);
```

### 2. Caching
- Implement Redis caching for frequently accessed data
- Use CDN for static assets

### 3. Connection Pooling
- Configure database connection pooling
- Set appropriate pool sizes

## Security Checklist

- [ ] Change default admin credentials
- [ ] Enable HTTPS
- [ ] Configure firewall
- [ ] Set up monitoring
- [ ] Regular security updates
- [ ] Backup strategy
- [ ] Rate limiting
- [ ] Input validation
- [ ] SQL injection prevention
- [ ] XSS protection

## Support

For deployment issues:
1. Check application logs
2. Verify environment variables
3. Test database connectivity
4. Check firewall settings
5. Review configuration files

## Quick Start Commands

```bash
# 1. Setup
git clone https://github.com/idaltu-1/sapyyn.git
cd sapyyn
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
cp .env.example .env
# Edit .env with your values

# 3. Initialize
python -c "from app import init_db; init_db()"

# 4. Run
python app.py
```

## Next Steps

1. Set up monitoring (Sentry, New Relic)
2. Configure CI/CD pipeline
3. Set up automated backups
4. Implement A/B testing
5. Add performance monitoring
6. Set up SSL certificate renewal
7. Configure log aggregation
8. Set up alerting
