# NoCodeBackend Database Integration

This document describes the integration with nocodebackend.com databases for the Sapyyn patient referral system.

## Overview

The integration connects to two NoCodeBackend databases:
1. **referralomsdb** - Referral and Order Management System data
2. **website_uploads** - File upload records and metadata

## Configuration

### Environment Variables

Add the following environment variables to your `.env` file:

```bash
# NoCodeBackend API Integration
NOCODEBACKEND_API_KEY=your_secret_api_key_here
NOCODEBACKEND_BASE_URL=https://api.nocodebackend.com
REFERRALOMSDB_INSTANCE=35557_referralomsdb
WEBSITE_UPLOADS_INSTANCE=35557_website_uploads
```

### GitHub Secrets (Production)

For production deployment, set the `NOCODEBACKEND_API_KEY` as a GitHub secret and expose it as an environment variable in your deployment configuration.

## API Endpoints

The integration provides the following REST API endpoints:

### Status Endpoint
```
GET /api/nocodebackend/status
```
Returns the configuration status and health of the NoCodeBackend integration.

**Response:**
```json
{
  "success": true,
  "status": {
    "configured": true,
    "referral_client": true,
    "uploads_client": true,
    "config": {
      "base_url": "https://api.nocodebackend.com",
      "referral_instance": "35557_referralomsdb",
      "uploads_instance": "35557_website_uploads",
      "api_key_set": true
    }
  }
}
```

### Referral Database Endpoints

#### Get All Referrals
```
GET /api/nocodebackend/referrals?limit=50&offset=0
```

#### Get Specific Referral
```
GET /api/nocodebackend/referrals/{referral_id}
```

#### Sync Local Referral to NoCodeBackend
```
POST /api/nocodebackend/sync-referral
Content-Type: application/json

{
  "referral_id": "local_referral_id_or_numeric_id"
}
```

### Upload Database Endpoints

#### Get All Uploads
```
GET /api/nocodebackend/uploads?limit=50&offset=0
```

#### Get Uploads by Referral
```
GET /api/nocodebackend/uploads?referral_id={referral_id}
```

#### Get Specific Upload
```
GET /api/nocodebackend/uploads/{upload_id}
```

## Client Library Usage

You can also use the NoCodeBackend client library directly in your Python code:

```python
from nocodebackend_client import create_nocodebackend_clients

# Configuration
config = {
    'API_KEY': 'your_api_key',
    'BASE_URL': 'https://api.nocodebackend.com',
    'REFERRALOMSDB_INSTANCE': '35557_referralomsdb',
    'WEBSITE_UPLOADS_INSTANCE': '35557_website_uploads'
}

# Create clients
referral_client, uploads_client = create_nocodebackend_clients(config)

# Use referral client
referrals = referral_client.get_referrals(limit=10)
specific_referral = referral_client.get_referral_by_id('ref_123')

# Use uploads client
uploads = uploads_client.get_uploads(limit=10)
referral_uploads = uploads_client.get_uploads_by_referral('ref_123')
```

## Error Handling

All endpoints include comprehensive error handling:
- **500** - Server errors (API unreachable, authentication failed, etc.)
- **404** - Resource not found
- **400** - Bad request (missing parameters)

Errors are logged and return JSON responses with error details:

```json
{
  "error": "Description of the error"
}
```

## Testing

Use the provided test script to verify the integration:

```bash
python3 test_nocodebackend_integration.py
```

This will test:
- Client configuration
- Database connectivity
- API endpoint functionality

## Security Notes

- **Never hardcode the API key** in source code
- Use environment variables or GitHub secrets for the API key
- The API key is transmitted over HTTPS to nocodebackend.com
- All API calls include proper authentication headers
- Error messages do not expose sensitive information

## Troubleshooting

### Common Issues

1. **"NoCodeBackend client not configured"**
   - Ensure `NOCODEBACKEND_API_KEY` environment variable is set
   - Check that the API key is valid

2. **"API request failed"**
   - Verify internet connectivity
   - Check that the nocodebackend.com API is accessible
   - Validate the API key and instance names

3. **"Failed to fetch [data]"**
   - Check API rate limits
   - Verify the instance names are correct
   - Ensure the databases contain data

### Debug Mode

Enable debug logging to see detailed API request/response information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Integration Architecture

```
Sapyyn App (Flask)
       ↓
nocodebackend_client.py
       ↓
requests (HTTPS)
       ↓
api.nocodebackend.com
       ↓
[referralomsdb] [website_uploads]
```

The integration uses a modular approach with separate client classes for each database, making it easy to extend or modify individual components.