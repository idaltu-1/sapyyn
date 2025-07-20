# Sapyyn Referral Rewards System Documentation

## Overview

The Sapyyn Referral Rewards System is a comprehensive, HIPAA and Stark Law compliant solution for incentivizing and tracking patient referrals in healthcare environments. This system provides all the essential functionality of a professional referral factory platform while maintaining strict compliance with healthcare regulations.

## Key Features

### 🏆 Core Functionality
- **Customizable Reward Programs**: Create and manage multiple reward programs with flexible configurations
- **Tiered Reward Structure**: Support for multiple reward tiers with progressive benefits
- **Flexible Trigger Logic**: Configurable triggers based on various referral actions and outcomes
- **Automated Reward Processing**: Automatic point allocation and tier advancement
- **Comprehensive Dashboard**: Real-time analytics and reward status tracking
- **Gamification Elements**: Achievements, leaderboards, and progress tracking

### 🛡️ Compliance & Security
- **HIPAA Compliance**: Full protection of patient health information (PHI)
- **Stark Law Compliance**: Anti-kickback provision adherence
- **Comprehensive Audit Trail**: All actions logged with immutable records
- **Privacy Protection**: Anonymized leaderboards and secure data handling
- **Legal Framework**: Customizable legal terms and compliance documentation

### 🎯 User Experience
- **Role-Based Access**: Different interfaces for patients, doctors, and administrators
- **Intuitive Navigation**: Easy-to-use interface for all user types
- **Mobile Responsive**: Full functionality on all device types
- **Real-Time Notifications**: Instant updates on reward status and achievements
- **Progress Tracking**: Visual progress indicators and achievement unlocks

### 🔗 Integration Capabilities
- **CRM/EMR Ready**: Database structure designed for external system integration
- **API Endpoints**: RESTful APIs for system integration
- **Flexible Data Export**: Compliance reporting and data analysis capabilities
- **Webhook Support**: Real-time event notifications for external systems

## System Architecture

### Database Schema

The rewards system uses a comprehensive database schema with the following key tables:

#### Core Tables
- `reward_programs`: Master reward program configurations
- `reward_tiers`: Tiered reward structure definitions
- `reward_triggers`: Automated trigger logic and conditions
- `user_rewards`: Individual reward transactions and status
- `achievements`: Gamification achievements and progress
- `user_achievements`: User achievement tracking

#### Compliance Tables
- `compliance_audit_trail`: Immutable audit log for all system actions
- `reward_notifications`: User notification history

### Security Architecture

1. **Data Encryption**: All sensitive data encrypted at rest and in transit
2. **Access Control**: Role-based permissions with granular access rights
3. **Audit Logging**: Comprehensive logging of all system interactions
4. **Privacy Protection**: HIPAA-compliant data handling and anonymization
5. **Secure Sessions**: Protected user sessions with timeout handling

## User Roles & Permissions

### Patient Users
- View personal reward status and history
- Access achievement progress and leaderboard ranking
- Receive notifications about earned rewards
- Create and track referrals

### Doctor Users
- All patient user capabilities
- Access to advanced analytics and reporting
- Create and manage reward programs (if authorized)
- View anonymized performance metrics

### Administrator Users
- Full system access and configuration
- Reward program creation and management
- Compliance audit trail access
- User management and role assignment
- System analytics and reporting

## Reward Program Configuration

### Program Types
1. **Referral Rewards**: Points awarded for completed referrals
2. **Loyalty Programs**: Long-term engagement incentives
3. **Achievement Based**: Milestone and goal-based rewards
4. **Quality Metrics**: Performance-based reward allocation

### Tier Structure
- **Bronze**: Entry-level recognition (1+ referrals)
- **Silver**: Consistent performance (5+ referrals)
- **Gold**: High-quality performance (15+ referrals)
- **Platinum**: Excellence tier (30+ referrals)

### Trigger Types
- **Referral Completion**: Automatic rewards on referral completion
- **Quality Metrics**: Rewards based on outcome quality
- **Time-Based**: Speed and efficiency incentives
- **Milestone**: Achievement-based triggers

## Compliance Framework

### HIPAA Compliance
- **Privacy Rule**: All PHI protected and access controlled
- **Security Rule**: Technical, administrative, and physical safeguards
- **Breach Notification**: Automated breach detection and reporting
- **Business Associate**: Compliance for third-party integrations

### Stark Law Compliance
- **Fair Market Value**: All rewards based on legitimate value exchange
- **No Volume Incentives**: Rewards based on quality, not quantity
- **Documentation**: Comprehensive legal documentation and review
- **Audit Trail**: Complete record of all reward decisions and approvals

### Legal Framework
- Customizable terms and conditions
- Regulatory compliance documentation
- Legal review integration points
- Audit-ready compliance reporting

## Installation & Setup

### Prerequisites
- Python 3.8+
- SQLite 3.x
- Flask 3.1.1+
- Modern web browser

### Installation Steps
1. **Clone Repository**
   ```bash
   git clone https://github.com/idaltu-1/sapyyn.git
   cd sapyyn
   ```

2. **Create Virtual Environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Database**
   ```bash
   python3 app.py  # This creates the database schema
   ```

5. **Create Demo Users**
   ```bash
   python3 create_demo_users.py
   ```

6. **Initialize Rewards System**
   ```bash
   python3 init_rewards_sample_data.py
   ```

7. **Launch Application**
   ```bash
   python3 app.py
   ```

8. **Access System**
   - Open browser to `http://localhost:5001`
   - Login with demo credentials (see README.md)

## API Documentation

### Rewards Endpoints

#### Get User Rewards
```http
GET /api/rewards/user/{user_id}
```
Returns user's reward history and current point balance.

#### Trigger Reward Check
```http
POST /api/rewards/trigger-check
Content-Type: application/json

{
  "referral_id": 123,
  "user_id": 456
}
```

#### Mark Notifications Read
```http
POST /api/rewards/notifications/mark-read
```

### Admin Endpoints

#### Create Reward Program
```http
POST /rewards/admin/program/new
```

#### Add Reward Tier
```http
POST /rewards/admin/program/{program_id}/tier/new
```

## Configuration Options

### Environment Variables
- `SAPYYN_SECRET_KEY`: Application secret key
- `SAPYYN_DB_PATH`: Database file path
- `SAPYYN_DEBUG`: Debug mode toggle
- `SAPYYN_MAX_UPLOAD_SIZE`: Maximum file upload size

### Program Settings
- Point values per reward tier
- Trigger conditions and thresholds
- Notification preferences
- Compliance review requirements

## Maintenance & Monitoring

### Regular Tasks
1. **Database Backup**: Regular automated backups
2. **Audit Review**: Monthly compliance audit reviews
3. **Performance Monitoring**: System performance metrics
4. **Security Updates**: Regular security patch application

### Monitoring Metrics
- User engagement and participation rates
- Reward distribution and fairness metrics
- System performance and response times
- Compliance audit trail completeness

## Troubleshooting

### Common Issues

#### Database Connection Errors
```bash
# Check database file permissions
ls -la sapyyn.db

# Reinitialize database if corrupted
rm sapyyn.db
python3 app.py
python3 init_rewards_sample_data.py
```

#### Permission Errors
```bash
# Check user roles in database
sqlite3 sapyyn.db "SELECT username, role FROM users;"
```

#### Template Rendering Issues
```bash
# Check template file existence
ls -la templates/rewards/
```

### Performance Optimization
- Database indexing for large datasets
- Caching for frequently accessed data
- Image optimization for faster loading
- CDN integration for static assets

## Best Practices

### Security
1. Regular security audits and penetration testing
2. Keep all dependencies updated
3. Use HTTPS in production environments
4. Implement proper backup and disaster recovery

### Compliance
1. Regular legal review of program terms
2. Document all program changes and approvals
3. Maintain comprehensive audit trails
4. Train users on compliance requirements

### User Experience
1. Regular user feedback collection
2. Performance monitoring and optimization
3. Mobile-first design principles
4. Accessibility compliance (WCAG 2.1)

## Support & Maintenance

### Support Channels
- GitHub Issues: Technical bug reports
- Documentation: Comprehensive user guides
- API Reference: Developer integration guides

### Maintenance Schedule
- **Daily**: Automated backups and health checks
- **Weekly**: Performance metrics review
- **Monthly**: Security updates and compliance review
- **Quarterly**: Feature updates and system optimization

## Future Enhancements

### Planned Features
1. **Advanced Analytics**: Machine learning insights
2. **Mobile App**: Native mobile applications
3. **Integration Hub**: Pre-built CRM/EMR connectors
4. **Advanced Gamification**: Social features and competitions
5. **Multi-tenant Support**: Organization-level isolation

### Roadmap
- Q1 2025: Advanced reporting and analytics
- Q2 2025: Mobile application release
- Q3 2025: Enterprise integration features
- Q4 2025: AI-powered insights and recommendations

---

For technical support or questions, please refer to the GitHub repository or contact the development team.
