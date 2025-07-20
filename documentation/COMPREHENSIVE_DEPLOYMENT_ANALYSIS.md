# Sapyyn.com - Comprehensive Deployment Analysis

**Analysis Date:** July 12, 2025  
**Analyst:** Manus AI  
**Purpose:** Complete infrastructure analysis and deployment documentation

## Executive Summary

Your Sapyyn dental referral platform consists of a multi-tier architecture deployed on AWS infrastructure with the following key components:

- **Main Website:** Next.js application (sapyyn.com)
- **User Portal:** React/Vite application (portal.sapyyn.com)  
- **Admin Panel:** React application (admin.sapyyn.com)
- **Backend API:** RESTful API service (api.sapyyn.com)
- **Real-time Services:** WebSocket service (socket.sapyyn.com)

## Infrastructure Overview

### Hosting Platform
- **Provider:** Amazon Web Services (AWS)
- **Load Balancer:** Multiple IP addresses suggesting AWS Application Load Balancer
- **IP Addresses:** 
  - 3.12.139.251
  - 3.18.31.27  
  - 3.134.179.15
- **Web Server:** Apache/2.4.58 (Ubuntu)

### Domain Architecture
```
sapyyn.com (Main Website)
├── portal.sapyyn.com (User Portal)
├── admin.sapyyn.com (Admin Panel)
├── api.sapyyn.com (Backend API)
└── socket.sapyyn.com (WebSocket Service)
```

## Frontend Applications

### 1. Main Website (sapyyn.com)
**Technology Stack:**
- Framework: Next.js (React-based)
- Build System: Webpack with code splitting
- Caching: Next.js cache with HIT status
- External Services: Chatbox widget (simplebase.co)

**Key Features:**
- Server-side rendering (SSR)
- Static generation with caching
- Responsive design (desktop + mobile)
- 20+ JavaScript chunks for optimal loading
- Slick carousel integration

**Assets:**
- 135+ files including dependencies
- Custom CSS with 4 generated stylesheets
- Multiple image formats and fonts
- Progressive web app capabilities

### 2. User Portal (portal.sapyyn.com)
**Technology Stack:**
- Framework: React (likely Vite build system)
- Build Date: December 9, 2024
- Font: Poppins from Google Fonts

**Key Features:**
- Single-page application (SPA)
- Authentication-protected dashboard
- Real-time notifications via WebSocket
- Cookie consent management

**Assets:**
- Main bundle: index-867af749.js (801KB)
- Stylesheet: index-ffb7e56b.css (261KB)
- Shared chatbox integration

### 3. Admin Panel (admin.sapyyn.com)
**Technology Stack:**
- Framework: React (Create React App)
- Build System: Webpack
- Last Modified: June 12, 2025

**Key Features:**
- Progressive Web App (PWA) with manifest
- Material Design components
- Leaflet maps integration
- GitHub buttons integration

**Assets:**
- Main bundle: main.1311e9a8.js (1.7MB)
- Stylesheet: main.4605a13b.css (53KB)
- Service Worker support
- App icons and manifest

## Backend Services

### API Architecture
**Primary API:** https://api.sapyyn.com/api/v1
- RESTful API design
- Version 1 endpoint structure
- Authentication required (401 responses observed)

**WebSocket Service:** https://socket.sapyyn.com/api/v1
- Real-time communication
- Event-driven notifications
- Used by portal application

### Authentication System
- Token-based authentication
- Session management
- Role-based access control (dentist, patient, admin)

## Third-Party Integrations

### Chat System
- **Provider:** SimpleBase.co
- **Project ID:** 65fde462604c7e2eafcc9139
- **Integration:** JavaScript widget across all applications

### External Libraries
- **Fonts:** Google Fonts (Poppins, Roboto, Material Icons)
- **Maps:** Leaflet.js for location services
- **UI Components:** Material-UI/MUI
- **Carousel:** Slick Carousel from CDNJS

## Security & SSL

### SSL Certificates
- All domains secured with HTTPS
- Certificate management likely via AWS Certificate Manager
- Proper SSL/TLS configuration across all subdomains

### Security Headers
- Vary headers for caching optimization
- ETag implementation for cache validation
- Content-Type security headers

## Deployment Architecture

### Build Process
1. **Main Site:** Next.js build with static generation
2. **Portal:** Vite build system with modern bundling
3. **Admin:** Create React App with Webpack optimization
4. **API:** Separate backend service deployment

### Caching Strategy
- Next.js cache: `s-maxage=31536000, stale-while-revalidate`
- Static asset caching via Apache
- CDN integration for external resources

### Load Balancing
- Multiple IP addresses indicate load balancer setup
- Geographic distribution across AWS regions
- High availability configuration

## Development Stack Recommendations

Based on your current setup and dental practice preferences, consider:

### Database Layer
- **Current:** Unknown (likely PostgreSQL or MySQL on AWS RDS)
- **Recommended:** Airtable integration for easier management
- **Format:** Excel workbooks for data exports

### Automation
- **Integration:** n8n workflow automation
- **Features:** ReferralHero/Referral Factory capabilities
- **HIPAA:** Compliant communication workflows

### Communication
- **Current:** SimpleBase chat widget
- **Recommended:** SuiteDash/Flowlu for client communications
- **Video:** doxy.me or GHL for secure consultations

## File Structure Analysis

### Downloaded Assets
```
sapyyn_websites_rip/
├── sapyyn_com/sapyyn.com/          # 135+ files, 7.1MB
├── portal_sapyyn_com/              # 5 files, 1.1MB  
├── admin_sapyyn_com/               # 7 files, 1.7MB
└── documentation/                  # Analysis files
```

### Key Files Identified
- **Next.js Config:** Embedded in build
- **React Manifests:** PWA configurations
- **API Endpoints:** Hardcoded in bundles
- **Asset Maps:** Source mapping available

## Recommendations for Redeployment

### 1. Infrastructure Setup
- Use AWS Elastic Beanstalk or ECS for container deployment
- Implement AWS CloudFront CDN
- Set up AWS RDS for database layer
- Configure AWS Route 53 for DNS management

### 2. CI/CD Pipeline
- GitHub Actions or AWS CodePipeline
- Automated testing and deployment
- Environment-specific configurations
- Database migration scripts

### 3. Monitoring & Analytics
- AWS CloudWatch for infrastructure monitoring
- Application performance monitoring
- Error tracking and logging
- User analytics integration

### 4. Security Enhancements
- AWS WAF for web application firewall
- Regular security audits
- HIPAA compliance validation
- Data encryption at rest and in transit

## Next Steps

1. **Source Code Recovery:** Locate original repositories
2. **Database Backup:** Export current database structure
3. **Environment Variables:** Document API keys and configurations
4. **Deployment Scripts:** Recreate build and deployment processes
5. **Testing:** Validate all functionality in new environment

## Contact Information

For questions about this analysis or deployment assistance:
- **Original Site:** https://sapyyn.com
- **Contact:** contact@sapyyn.com
- **Analysis Date:** July 12, 2025

