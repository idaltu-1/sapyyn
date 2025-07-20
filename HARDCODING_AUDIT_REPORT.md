# Hardcoding Audit Report - Sapyyn Platform

## 🚨 **Critical Hardcoded Values Found**

### **1. Security-Critical Hardcoding**

#### **app.py - Secret Keys & Credentials**
```python
# CRITICAL: Hardcoded secret key
app.secret_key = 'sapyyn-patient-referral-system-2025'

# CRITICAL: Hardcoded admin credentials
password_hash = generate_password_hash('P@$sW0rD54321$')
'wgray@stloralsurgery.com'

# CRITICAL: Hardcoded demo passwords
'password': 'password123'  # Used in multiple demo users

# CRITICAL: Hardcoded temporary passwords
password_hash = generate_password_hash('temp123')
password = email.split('@')[0] + '123!'
```

#### **Stripe Configuration**
```python
# Partially hardcoded - should have better defaults
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_...')
STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY', 'pk_test_...')
```

### **2. Database & Infrastructure Hardcoding**

#### **Database Configuration**
```python
# Hardcoded database name
conn = sqlite3.connect('sapyyn.db')

# Hardcoded file upload limits
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB
```

#### **URL & Port Configuration**
```python
# referral_management.py
base_url = os.environ.get('BASE_URL', 'http://localhost:5000')

# config/security.py
RATELIMIT_STORAGE_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
```

### **3. Test Data Hardcoding**

#### **Demo User Credentials**
```python
# create_demo_users.py & app.py
demo_users = [
    {'username': 'dentist1', 'email': 'dentist@sapyyn.com', 'password': 'password123'},
    {'username': 'specialist1', 'email': 'specialist@sapyyn.com', 'password': 'password123'},
    {'username': 'patient1', 'email': 'patient@sapyyn.com', 'password': 'password123'},
    {'username': 'admin1', 'email': 'admin@sapyyn.com', 'password': 'password123'}
]
```

#### **Test Configuration**
```python
# Multiple test files
self.login('user1', 'password123')
os.environ['NOCODEBACKEND_SECRET_KEY'] = 'testkey'
```

### **4. Business Logic Hardcoding**

#### **Provider Code Generation**
```python
# Hardcoded character set and length
chars = '23456789ABCDEFGHJKMNPQRSTUVWXYZ'
code = ''.join(random.choice(chars) for _ in range(6))  # Hardcoded 6 chars
```

#### **Subscription Plans**
```python
# Hardcoded plan details in database initialization
('Basic', 'free', 0.00, 0.00, 'Up to 5 referrals/month...', 5, 1, 1, 'email'),
('Professional', 'practice', 49.99, 499.99, '...', -1, 3, 10, 'priority'),
```

## 🔧 **Recommended Fixes**

### **Priority 1: Security Critical**

1. **Move secret key to environment variable**
2. **Remove hardcoded admin credentials**
3. **Implement secure password generation**
4. **Use environment-based configuration**

### **Priority 2: Configuration Management**

1. **Create centralized configuration system**
2. **Move database settings to config**
3. **Externalize business rules**
4. **Implement feature flags**

### **Priority 3: Test Data Management**

1. **Separate test fixtures**
2. **Use configuration-based test data**
3. **Implement test data factories**

## 📋 **Implementation Plan**

### **Phase 1: Security Hardening**
- [ ] Create `.env.example` template
- [ ] Move all secrets to environment variables
- [ ] Implement secure configuration loading
- [ ] Remove hardcoded credentials

### **Phase 2: Configuration Centralization**
- [ ] Create `config/` directory structure
- [ ] Implement environment-specific configs
- [ ] Move business rules to configuration
- [ ] Add configuration validation

### **Phase 3: Test Data Management**
- [ ] Create test fixtures directory
- [ ] Implement test data factories
- [ ] Separate test and production data
- [ ] Add test environment isolation

## 🎯 **Security Impact**

### **High Risk Issues**
- Hardcoded secret keys in source code
- Admin credentials in repository
- Predictable demo passwords
- No environment separation

### **Medium Risk Issues**
- Hardcoded business rules
- Fixed infrastructure settings
- Test data in production code

### **Recommendations**
1. **Immediate**: Remove all hardcoded secrets
2. **Short-term**: Implement configuration management
3. **Long-term**: Add configuration validation and monitoring
