# Sapyyn - Patient Referral System

A comprehensive web-based patient referral management system built with Flask, featuring secure document handling, QR code generation, and HIPAA-compliant data management.

**Copyright © 2025 Sapyyn. All rights reserved.**

## 🚀 Features

### Core Functionality
- **User Authentication & Authorization** - Secure login system with role-based access (Doctor, Patient, Admin)
- **Patient Referral Management** - Create, track, and manage patient referrals with unique IDs
- **Document Management** - Upload and organize medical documents by category
- **QR Code Generation** - Automatic QR code creation for easy referral tracking
- **Dashboard Analytics** - Real-time statistics and referral status tracking
- **Responsive Design** - Mobile-friendly interface using Bootstrap 5

### 🏆 Referral Rewards System
- **Comprehensive Reward Programs** - Customizable reward programs with tiered structures
- **HIPAA & Stark Law Compliant** - Full regulatory compliance for healthcare environments
- **Gamification Features** - Achievements, leaderboards, and progress tracking
- **Automated Reward Processing** - Intelligent trigger system for reward allocation
- **Compliance Audit Trail** - Complete logging for regulatory requirements
- **Flexible Fulfillment Options** - Manual, automatic, and external system integration
- **Advanced Analytics** - Performance metrics and reward program insights
- **Role-Based Administration** - Granular control for program management

### Document Categories Supported
- Medical Reports
- Insurance Documents
- Experience Documents
- Qualification Documents
- Supporting Documents
- Profile Pictures
- Testimonial Images
- Broadcast Files
- General Uploads

### Security & Compliance
- HIPAA-compliant data handling
- Encrypted file storage
- Secure user sessions
- Access control and audit trails
- Input validation and sanitization

## 🛠️ Technology Stack

- **Backend**: Python Flask 3.1.1
- **Database**: SQLite (with SQLAlchemy ORM)
- **Frontend**: HTML5, CSS3, JavaScript (ES6+)
- **UI Framework**: Bootstrap 5.1.3 with Bootstrap Icons
- **File Handling**: Werkzeug for secure uploads
- **QR Codes**: qrcode library with Pillow
- **Security**: Werkzeug password hashing

## 📦 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Node.js 16 or higher (for frontend build)
- npm package manager

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/idaltu-1/sapyyn.git
   cd sapyyn
   ```

2. **Quick Build (Recommended)**
   ```bash
   chmod +x build.sh
   ./build.sh
   ```

3. **Manual Installation**
   ```bash
   # Install Python dependencies
   pip install -r requirements.txt
   
   # Install Node.js dependencies and build frontend assets
   npm install
   npm run build
   ```

4. **Initialize the database and demo users**
   ```bash
   python3 create_demo_users.py
   ```

5. **Initialize the rewards system**
   ```bash
   python3 init_rewards_sample_data.py
   ```

6. **Run the application**
   ```bash
   python3 app.py
   ```

6. **Access the application**
   - Open your browser and navigate to `http://localhost:5001`
   - Use demo credentials or register a new account

## 👥 Demo Accounts

For testing purposes, the following demo accounts are available:

| Role | Username | Password | Description |
|------|----------|----------|-------------|
| Doctor | `doctor1` | `password123` | Healthcare provider account |
| Patient | `patient1` | `password123` | Patient account |
| Admin | `admin1` | `password123` | Administrator account |

## 🎯 Usage Guide

### Creating a New Referral

1. **Login** with your credentials
2. **Navigate** to the dashboard
3. **Click** "New Referral" button
4. **Fill in** patient information:
   - Patient full name
   - Medical condition
   - Referring doctor
   - Target specialist
   - Urgency level
   - Clinical notes
5. **Submit** the form to generate a unique referral ID and QR code

### Uploading Documents

1. **Go to** "Upload Documents" page
2. **Select** document type from dropdown
3. **Choose** file (PDF, DOC, images, etc.)
4. **Upload** the document with automatic categorization

### Managing Referrals

- **View** all referrals on the dashboard
- **Track** referral status (Pending, Approved, Completed, Rejected)
- **Generate** QR codes for easy sharing
- **Monitor** progress through the referral lifecycle

## 🏗️ Project Structure

```
sapyyn/
├── app.py                      # Main Flask application
├── requirements.txt            # Python dependencies
├── create_demo_users.py       # Demo user setup script
├── sapyyn.db                  # SQLite database (auto-generated)
├── templates/                 # HTML templates
│   ├── base.html             # Base template with navigation
│   ├── index.html            # Homepage
│   ├── login.html            # Login page
│   ├── register.html         # Registration page
│   ├── dashboard.html        # User dashboard
│   ├── new_referral.html     # Create referral form
│   ├── upload.html           # File upload page
│   └── documents.html        # Document management
├── static/                   # Static assets
│   ├── css/
│   │   └── style.css        # Custom styles
│   └── js/
│       └── main.js          # Client-side JavaScript
├── patient-referral/        # Document storage directory
└── README.md               # This file
```

## 🔧 Configuration

### Environment Variables

The application can be configured using the following variables:

- `FLASK_ENV`: Set to `development` for debug mode
- `SECRET_KEY`: Application secret key (auto-generated)
- `UPLOAD_FOLDER`: Directory for file uploads (default: `patient-referral/`)
- `MAX_CONTENT_LENGTH`: Maximum file upload size (default: 16MB)

### Database Configuration

The application uses SQLite by default. The database schema includes:

- **Users** table for authentication
- **Referrals** table for patient referrals
- **Documents** table for file management

## 🚀 Deployment

### Production Deployment

For production deployment, consider:

1. **Use a production WSGI server** (e.g., Gunicorn, uWSGI)
2. **Configure a reverse proxy** (e.g., Nginx, Apache)
3. **Use a production database** (e.g., PostgreSQL, MySQL)
4. **Set up SSL/TLS encryption**
5. **Configure environment variables**
6. **Set up backup and monitoring**

### Docker Deployment

A Dockerfile can be created for containerized deployment:

```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "app.py"]
```

## 🧪 Testing

### Manual Testing

1. **User Registration & Login**
   - Test account creation with different roles
   - Verify password validation and security

2. **Referral Management**
   - Create referrals with various urgency levels
   - Test QR code generation and display

3. **File Upload**
   - Upload different file types and sizes
   - Test document categorization

4. **Dashboard Functionality**
   - Verify statistics accuracy
   - Test responsive design on mobile devices

### Automated Testing

Future enhancements could include:
- Unit tests with pytest
- Integration tests for API endpoints
- Frontend tests with Selenium
- Performance testing with locust

## 🔐 Security Considerations

### Implemented Security Measures

- **Password Hashing**: Using Werkzeug's secure password hashing
- **File Upload Validation**: Restricted file types and size limits
- **SQL Injection Prevention**: Using parameterized queries
- **XSS Prevention**: Template escaping and input sanitization
- **Session Management**: Secure session handling with Flask

### Additional Security Recommendations

- Implement rate limiting for login attempts
- Add two-factor authentication (2FA)
- Set up comprehensive logging and monitoring
- Regular security audits and penetration testing
- HTTPS enforcement in production

## 🎨 Customization

### Themes and Styling

The application uses a modular CSS approach:

- **Custom CSS**: Located in `static/css/style.css`
- **Bootstrap Variables**: Can be customized for branding
- **Responsive Design**: Mobile-first approach with breakpoints

### Feature Extensions

The system is designed for extensibility:

- **API Endpoints**: RESTful API for mobile app integration
- **Notification System**: Email and SMS notifications
- **Reporting**: Advanced analytics and reporting features
- **Integration**: Connect with EMR/EHR systems
- **Multi-language**: Internationalization support

## 📊 Analytics and Reporting

### Dashboard Metrics

- Total referrals count
- Referrals by status (Pending, Approved, etc.)
- Document upload statistics
- User activity metrics

### Export Capabilities

- PDF reports generation
- CSV data export
- QR code downloads
- Document archiving

## 🤝 Contributing

Contributions are welcome! Please follow these guidelines:

1. **Fork** the repository
2. **Create** a feature branch
3. **Make** your changes with tests
4. **Submit** a pull request with detailed description

### Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install pytest flask-testing

# Run tests
pytest

# Start development server
python app.py
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For support and questions:

- **Issues**: Create an issue on GitHub
- **Documentation**: Check the project wiki
- **Security**: Report security issues privately

## 🗺️ Roadmap

### Version 2.0 Planning

- [ ] RESTful API development
- [ ] Mobile application (React Native/Flutter)
- [ ] Advanced analytics dashboard
- [ ] Integration with popular EMR systems
- [ ] Multi-tenant architecture
- [ ] Advanced user roles and permissions
- [ ] Automated referral routing
- [ ] Telemedicine integration

### Version 1.1 Enhancements

- [ ] Email notifications
- [ ] PDF report generation
- [ ] Advanced search and filtering
- [ ] Bulk operations
- [ ] Data export functionality
- [ ] Performance optimizations

---

## 📸 Screenshots

### Homepage
![Homepage](https://github.com/user-attachments/assets/349d1fc8-fed1-4394-9ca5-eb65c9249d48)

### Dashboard
![Dashboard](https://github.com/user-attachments/assets/5e3b1404-520e-4d01-b9ae-dc45eb169d0a)

### Dashboard with Referral
![Dashboard with Referral](https://github.com/user-attachments/assets/1b8af067-3064-4ab8-9677-7132ea828ab2)

---

*Built with ❤️ for healthcare professionals to streamline patient referral management.*

## 🏆 Rewards System

The Sapyyn platform includes a comprehensive referral rewards system designed to incentivize quality patient referrals while maintaining strict compliance with healthcare regulations.

### Key Features

- **HIPAA & Stark Law Compliant**: Full regulatory compliance for healthcare environments
- **Customizable Programs**: Create and manage multiple reward programs with flexible configurations
- **Tiered Rewards**: Progressive reward structure (Bronze, Silver, Gold, Platinum)
- **Gamification**: Achievements, leaderboards, and progress tracking
- **Automated Processing**: Intelligent trigger system for reward allocation
- **Audit Trail**: Complete logging for compliance and regulatory requirements
- **Role-Based Access**: Different interfaces for patients, doctors, and administrators

### Using the Rewards System

#### For Healthcare Professionals
1. **Access Rewards Dashboard**: Navigate to "Rewards" in the main menu
2. **View Progress**: Track your points, tier status, and achievements
3. **Check Leaderboard**: See your ranking among peers (anonymized for privacy)
4. **Earn Rewards**: Complete quality referrals to earn points and advance tiers

#### For Administrators
1. **Manage Programs**: Create and configure reward programs
2. **Set Tiers**: Define reward tiers and requirements
3. **Monitor Compliance**: Access audit trails and compliance reports
4. **Configure Triggers**: Set up automated reward conditions

### Compliance Features

- **Privacy Protection**: All leaderboards anonymized to protect user privacy
- **Audit Logging**: Comprehensive logging of all system actions
- **Legal Framework**: Customizable terms and conditions
- **Regulatory Adherence**: Built-in HIPAA and Stark Law compliance

For detailed information, see [REWARDS_SYSTEM_DOCUMENTATION.md](REWARDS_SYSTEM_DOCUMENTATION.md).
