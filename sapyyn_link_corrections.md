# Sapyyn Repository Link Corrections

## Current Issues and Recommended Fixes

### 1. **Asset Links (All Files)**
**Current:** 
- `/logo.svg`
- `/favicon.ico` 
- `/hero-dashboard.png`

**Should be:**
- `./assets/logo.svg` or `./images/logo.svg`
- `./assets/favicon.ico`
- `./assets/hero-dashboard.png` or `./images/hero-dashboard.png`

### 2. **Portal Navigation (sapyyn-portal.html)**
**Current:**
```html
<a href="/portal" class="portal-logo">
<a href="/portal/dashboard" class="active">Dashboard</a>
<a href="/portal/referrals">My Referrals</a>
<a href="/portal/appointments">Appointments</a>
<a href="/portal/documents">Documents</a>
<a href="/portal/messages">Messages</a>
```

**Should be:**
```html
<a href="./sapyyn-portal.html" class="portal-logo">
<a href="./sapyyn-portal.html" class="active">Dashboard</a>
<a href="./portal-referrals.html">My Referrals</a>
<a href="./portal-appointments.html">Appointments</a>
<a href="./portal-documents.html">Documents</a>
<a href="./portal-messages.html">Messages</a>
```

### 3. **Quick Action Links (sapyyn-portal.html)**
**Current:**
```html
<a href="/portal/new-referral" class="action-card">
<a href="/portal/find-provider" class="action-card">
<a href="/portal/upload-document" class="action-card">
<a href="/portal/schedule" class="action-card">
```

**Should be:**
```html
<a href="./portal-new-referral.html" class="action-card">
<a href="./portal-find-provider.html" class="action-card">
<a href="./portal-upload-document.html" class="action-card">
<a href="./portal-schedule.html" class="action-card">
```

### 4. **Main Site Navigation (sapyyn-main-site.html)**
**Current:**
```html
<a href="/portal" class="btn btn-secondary">Sign In</a>
<a href="/portal/signup" class="btn btn-primary">Get Started</a>
<a href="/portal/signup" class="btn btn-primary">
```

**Should be:**
```html
<a href="./sapyyn-portal.html" class="btn btn-secondary">Sign In</a>
<a href="./portal-signup.html" class="btn btn-primary">Get Started</a>
<a href="./portal-signup.html" class="btn btn-primary">
```

### 5. **Legal and Info Pages (sapyyn-main-site.html)**
**Current:**
```html
<a href="/privacy">Privacy Policy</a>
<a href="/terms">Terms of Service</a>
<a href="/hipaa">HIPAA Compliance</a>
<a href="/security">Security</a>
<a href="/contact">Contact</a>
```

**Should be:**
```html
<a href="./privacy.html">Privacy Policy</a>
<a href="./terms.html">Terms of Service</a>
<a href="./hipaa.html">HIPAA Compliance</a>
<a href="./security.html">Security</a>
<a href="./contact.html">Contact</a>
```

## Recommended Repository Structure

```
sapyyn/
├── index.html (rename sapyyn-main-site.html)
├── sapyyn-portal.html
├── sapyyn-admin-panel.html
├── portal-referrals.html (new)
├── portal-appointments.html (new)
├── portal-documents.html (new)
├── portal-messages.html (new)
├── portal-new-referral.html (new)
├── portal-find-provider.html (new)
├── portal-upload-document.html (new)
├── portal-schedule.html (new)
├── portal-signup.html (new)
├── privacy.html (new)
├── terms.html (new)
├── hipaa.html (new)
├── security.html (new)
├── contact.html (new)
├── assets/
│   ├── logo.svg
│   ├── favicon.ico
│   └── hero-dashboard.png
├── css/
│   └── styles.css (optional - extract common styles)
├── js/
│   └── scripts.js (optional - extract common scripts)
└── README.md
```

## GitHub Pages Configuration

If hosting on GitHub Pages, ensure:

1. **Main site** should be named `index.html`
2. **Base URL** in repository settings points to your GitHub Pages URL
3. **Relative paths** work correctly with the repository structure

## Additional Recommendations

### For GitHub Repository:
1. **Create missing pages** referenced in the navigation
2. **Add proper meta tags** for GitHub Pages SEO
3. **Include README.md** with setup instructions
4. **Add LICENSE file** if open source
5. **Create .gitignore** for any build files

### For Production Deployment:
1. **Use environment variables** for base URLs
2. **Implement proper routing** if using a single-page application framework
3. **Add SSL certificates** for security
4. **Set up domain redirects** if using custom domain

## Files That Need Updates

1. **sapyyn-portal.html** - Update all internal navigation links
2. **sapyyn-main-site.html** - Update portal links and legal page links  
3. **sapyyn-admin-panel.html** - Update asset paths
4. **Create missing pages** - All the referenced but non-existent pages
5. **Add assets folder** - Move logo, favicon, and images to proper directory