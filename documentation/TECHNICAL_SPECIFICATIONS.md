# Sapyyn.com - Technical Specifications

## API Endpoints Discovered

### Primary API Service
```
Base URL: https://api.sapyyn.com/api/v1
```

### WebSocket Service  
```
Base URL: https://socket.sapyyn.com/api/v1
Notification Socket: https://api.sapyyn.com/api/v1/notification/socket
```

## JavaScript Bundle Analysis

### Main Site (sapyyn.com)
**Core Bundles:**
- `main-app-2abfdeb087631a01.js` - Main application logic
- `app/page-4ec8501b2d876f0e.js` - Homepage component
- `app/layout-59f6ee933d784501.js` - Layout component
- `webpack-e42ad6b6bf80eda0.js` - Webpack runtime
- `polyfills-c67a75d1b6f99dc8.js` - Browser polyfills

**Code Splitting Chunks:**
- 20+ numbered chunks for optimal loading
- Dynamic imports for route-based splitting
- Vendor libraries separated into chunks

### Portal (portal.sapyyn.com)
**Main Bundle:**
- `index-867af749.js` (801KB) - Complete application
- `index-ffb7e56b.css` (261KB) - Styles
- Vite build system (modern bundling)

### Admin (admin.sapyyn.com)
**Main Bundle:**
- `main.1311e9a8.js` (1.7MB) - Complete application
- `main.4605a13b.css` (53KB) - Styles
- Create React App build system

## CSS Architecture

### Main Site Stylesheets
```
/_next/static/css/d3df112486f97f47.css
/_next/static/css/d9f96263af48df27.css  
/_next/static/css/46b29e5e787975f1.css
/_next/static/css/e4f21793dee1be02.css
```

### External CSS Dependencies
```
https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.6.0/slick.min.css
https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.6.0/slick-theme.min.css
https://fonts.googleapis.com/css2?family=Poppins:...
https://fonts.googleapis.com/css?family=Roboto:...
https://unpkg.com/leaflet@1.7.1/dist/leaflet.css
```

## Server Configuration

### HTTP Headers Analysis
```
Server: Apache/2.4.58 (Ubuntu)
X-Powered-By: Next.js
X-NextJS-Cache: HIT
Cache-Control: s-maxage=31536000, stale-while-revalidate
Vary: RSC,Next-Router-State-Tree,Next-Router-Prefetch,Next-Url,Accept-Encoding
```

### Content Types
- Main site: `text/html; charset=utf-8`
- Subdomains: `text/html`
- Static assets: Appropriate MIME types

## DNS Configuration

### A Records
```
sapyyn.com          → 3.12.139.251, 3.18.31.27, 3.134.179.15
portal.sapyyn.com   → 3.134.179.15, 3.18.31.27, 3.12.139.251  
admin.sapyyn.com    → 3.18.31.27, 3.12.139.251, 3.134.179.15
api.sapyyn.com      → [Same IP pool]
socket.sapyyn.com   → [Same IP pool]
```

### AWS Infrastructure
- **Region:** Multiple (us-east-1, us-east-2, us-west-2 based on IPs)
- **Load Balancer:** Application Load Balancer (ALB)
- **Auto Scaling:** Multiple instances across AZs

## Build System Details

### Next.js Configuration
- App Router architecture (not Pages Router)
- Static generation with ISR (Incremental Static Regeneration)
- Code splitting enabled
- Image optimization configured
- Font optimization with Google Fonts

### React Applications
- **Portal:** Modern Vite build with ES modules
- **Admin:** Traditional CRA build with Webpack
- **State Management:** Context API (no Redux detected)
- **Routing:** React Router (client-side)

## Third-Party Services

### Chat Integration
```
Provider: SimpleBase.co
Widget URL: https://chatbox.simplebase.co/projects/65fde462604c7e2eafcc9139/widget.js
Project ID: 65fde462604c7e2eafcc9139
```

### External APIs
- Google Fonts API
- CDNJS for libraries
- GitHub Buttons API
- Leaflet tile servers

## Security Implementation

### Authentication Flow
1. Login forms on portal/admin subdomains
2. Token-based authentication (JWT likely)
3. API calls return 401 when unauthenticated
4. Session management via cookies

### CORS Configuration
- Cross-origin requests enabled
- Proper headers for SPA communication
- API accessible from frontend domains

## Performance Optimizations

### Caching Strategy
- **Static Assets:** Long-term caching (1 year)
- **HTML:** Stale-while-revalidate
- **API:** No-cache for dynamic content
- **CDN:** CloudFront likely in use

### Bundle Optimization
- Code splitting by routes and features
- Tree shaking for unused code
- Minification and compression
- Source maps available for debugging

## Database Architecture (Inferred)

### Likely Structure
- **Users:** Dentists, patients, admins
- **Referrals:** Patient referral records
- **Practices:** Dental practice information
- **Notifications:** Real-time messaging
- **Documents:** Patient document storage

### Technology Stack (Estimated)
- **Database:** PostgreSQL or MySQL on AWS RDS
- **ORM:** Likely Prisma or TypeORM
- **Migrations:** Version-controlled schema changes
- **Backups:** Automated AWS RDS backups

## Deployment Pipeline (Reconstructed)

### Build Process
1. **Source:** Git repository (GitHub likely)
2. **CI/CD:** GitHub Actions or AWS CodePipeline
3. **Build:** 
   - Next.js: `npm run build`
   - Portal: `npm run build` (Vite)
   - Admin: `npm run build` (CRA)
4. **Deploy:** AWS S3 + CloudFront or EC2/ECS

### Environment Variables (Required)
```bash
# API Configuration
API_BASE_URL=https://api.sapyyn.com/api/v1
SOCKET_URL=https://socket.sapyyn.com/api/v1

# Database
DATABASE_URL=postgresql://...

# Authentication
JWT_SECRET=...
SESSION_SECRET=...

# Third-party Services
SIMPLEBASE_PROJECT_ID=65fde462604c7e2eafcc9139

# AWS Configuration
AWS_REGION=us-east-1
AWS_S3_BUCKET=...
AWS_CLOUDFRONT_DISTRIBUTION=...
```

## File Manifest

### Complete Asset Inventory
- **Total Files:** 150+ across all applications
- **Total Size:** ~9MB compressed, ~25MB uncompressed
- **File Types:** HTML, CSS, JS, PNG, JPG, SVG, WOFF2, ICO
- **Source Maps:** Available for debugging

### Critical Files for Redeployment
1. **package.json** files (need to be recreated)
2. **Environment configurations**
3. **Database schema and migrations**
4. **SSL certificates and domain configurations**
5. **AWS infrastructure as code (Terraform/CloudFormation)**

## Monitoring & Analytics

### Current Implementation
- Error boundaries in React applications
- Console logging for debugging
- Performance monitoring via browser APIs

### Recommended Additions
- AWS CloudWatch integration
- Application performance monitoring (APM)
- User analytics and conversion tracking
- Error tracking service (Sentry)
- Uptime monitoring

This technical specification provides the foundation for recreating your Sapyyn deployment infrastructure.

