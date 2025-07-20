# Sapyyn Patient Referral System

A comprehensive patient referral management system designed to streamline healthcare provider connections and patient document management.

## Overview

Sapyyn is a patient referral platform that facilitates secure document sharing and communication between healthcare providers, patients, and insurance companies.

## Features

- **Document Management**: Secure upload and organization of medical documents, insurance files, and supporting documentation
- **Multi-Portal Access**: Separate portals for administrators, healthcare providers, and patients
- **QR Code Integration**: Quick access to patient information via QR codes
- **File Type Support**: Handles PDFs, images (JPEG, PNG, WebP), and various document formats
- **Secure Storage**: HIPAA-compliant document storage and transmission

## Project Structure

```
sapyyn/patient-referral/
├── documents/              # Organized patient documents
│   ├── medical/           # Medical reports and records
│   ├── insurance/         # Insurance documentation
│   ├── qualification/     # Provider qualification documents
│   ├── experience/        # Experience certificates
│   ├── supporting/        # Additional supporting documents
│   ├── profile_pictures/  # User profile images
│   ├── qr_codes/         # Generated QR codes
│   ├── message_attachments/ # Communication attachments
│   ├── testimonials/     # Patient testimonials
│   ├── broadcast/        # Broadcast communications
│   └── uploaded/         # General uploads
├── websites/              # Web applications
│   ├── main/             # Main Sapyyn website
│   ├── admin/            # Admin portal (admin.sapyyn.com)
│   └── portal/           # Patient/Provider portal (portal.sapyyn.com)
├── assets/               # Static assets
│   ├── images/           # Website images
│   └── icons/            # Application icons
├── backend/              # Backend services
├── frontend/             # Frontend source code
├── src/                  # Application source code
├── config/               # Configuration files
└── infrastructure/       # Infrastructure as code

```

## Technology Stack

- **Frontend**: React.js with Vite
- **Backend**: Node.js (planned)
- **Storage**: AWS S3
- **Deployment**: AWS Amplify, Elastic Beanstalk
- **Build Tools**: Vite, PostCSS

## AWS Infrastructure

- **S3 Buckets**:
  - `amplify-prism-dev-ab793-deployment` - Amplify deployment
  - `elasticbeanstalk-us-east-2-533267173236` - Elastic Beanstalk
  - `sapyyn` - Main application storage

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- Python 3.8+ (for backend services)
- AWS CLI (for deployment)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/idaltu-1/sapyyn-website.git
cd sapyyn/patient-referral
```

2. Install dependencies:
```bash
npm install
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start development server:
```bash
npm run dev
```

## Security Considerations

- All patient data must be handled in compliance with HIPAA regulations
- Implement proper authentication and authorization
- Use SSL/TLS for all data transmission
- Regular security audits recommended

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is proprietary software. All rights reserved.

## Contact

For questions or support, please contact the Sapyyn development team.