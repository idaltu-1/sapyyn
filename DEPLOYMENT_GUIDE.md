# 🚀 Sapyyn Healthcare Portal - Deployment Guide

## ✅ Successfully Deployed Updates

### 🎯 **Latest Changes (July 2025)**
- **6-Digit Provider Codes**: Enhanced from 4-digit to 6-digit for better security
- **Updated Pricing**: Starter $49.99, Professional $99.99, Enterprise $499/month
- **Stripe Integration**: Full payment processing with 14-day free trials
- **Multi-Portal System**: Separate interfaces for Dentists, Specialists, Patients, Admins

---

## 📋 **Production Deployment Steps**

### 1. **Environment Setup**
```bash
# Clone the repository
git clone https://github.com/idaltu-1/sapyyn.git
cd sapyyn

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. **Database Initialization**
```bash
# Run the Flask app once to create database
python app.py
# Stop with Ctrl+C after database is created

# Create demo users (optional)
python create_demo_users.py
```

### 3. **Stripe Configuration**
Set these environment variables for production:
```bash
export STRIPE_SECRET_KEY="sk_live_your_secret_key"
export STRIPE_PUBLISHABLE_KEY="pk_live_your_publishable_key" 
export STRIPE_WEBHOOK_SECRET="whsec_your_webhook_secret"
```

### 4. **Production Server**
```bash
# Install production server
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

---

## 🔧 **Configuration Checklist**

### ✅ **Pre-Production Setup**
- [ ] Set Stripe API keys (live keys for production)
- [ ] Configure webhook endpoint: `https://yourdomain.com/stripe-webhook`
- [ ] Set up SSL certificate for HTTPS
- [ ] Configure domain name and DNS
- [ ] Set up database backups
- [ ] Configure email service for notifications

### ✅ **Security Settings**
- [ ] Change Flask secret key in production
- [ ] Enable HTTPS only
- [ ] Set up proper firewall rules
- [ ] Configure rate limiting
- [ ] Enable logging and monitoring

---

## 🌐 **Hosting Options**

### **Option 1: Railway/Render (Recommended)**
1. Connect GitHub repository
2. Set environment variables in dashboard
3. Deploy automatically on push

### **Option 2: DigitalOcean/AWS**
1. Create droplet/EC2 instance
2. Set up nginx reverse proxy
3. Configure SSL with Let's Encrypt
4. Set up systemd service

### **Option 3: Heroku**
1. Create Heroku app
2. Set config vars for Stripe keys
3. Deploy with git push

---

## 📱 **Current Features**

### **Multi-Role Portal System**
- **Dentist Portal**: Practice management, provider codes, referrals
- **Specialist Portal**: Receive referrals, manage appointments
- **Patient Portal**: Find providers, submit referrals
- **Admin Portal**: System management, analytics

### **Payment System**
- **14-Day Free Trial**: Auto-renews to Professional plan
- **Stripe Integration**: Secure payment processing
- **Subscription Management**: Upgrade/downgrade anytime
- **Webhook Support**: Real-time payment status updates

### **Provider Code System**
- **6-Digit Codes**: Range 100000-999999 for enhanced security
- **Instant Referrals**: Patients use codes for direct connection
- **QR Code Support**: Generate QR codes for easy sharing
- **HIPAA Compliant**: Secure, encrypted communications

---

## 🔗 **Important URLs**

- **GitHub Repository**: https://github.com/idaltu-1/sapyyn
- **Demo Login**: doctor1/patient1/admin1 (password: password123)
- **Local Development**: [http://localhost:5001](http://localhost:5001) *(Requires the application to be running locally)*

---

## 📞 **Support & Maintenance**

### **Regular Tasks**
- Monitor Stripe dashboard for payments
- Check application logs for errors
- Backup database regularly
- Update dependencies monthly
- Review user feedback

### **Troubleshooting**
- Check Flask logs for application errors
- Verify Stripe webhook delivery
- Monitor database performance
- Check SSL certificate expiry

---

## 🎉 **Ready for Production!**

The Sapyyn Healthcare Portal is now fully deployed with:
- ✅ 6-digit provider codes
- ✅ Updated pricing structure  
- ✅ Stripe payment integration
- ✅ Multi-role portal system
- ✅ HIPAA-compliant workflow

**Next Step**: Configure your Stripe account and deploy to your production server!
