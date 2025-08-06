# Migration Guide: NoCodeBackend to Supabase

This guide explains how to migrate the Sapyyn Patient Referral System from NoCodeBackend to Supabase.

## Overview

The migration replaces NoCodeBackend (a backend-as-a-service) with Supabase, an open-source Firebase alternative that provides:

- PostgreSQL database with real-time subscriptions
- RESTful API and realtime subscriptions
- File storage with CDN
- Row Level Security (RLS) 
- Built-in authentication (though we continue using Flask sessions)

## Prerequisites

1. Create a [Supabase account](https://supabase.com) and new project
2. Note your project URL and API keys from the Supabase dashboard
3. Install required dependencies: `pip install supabase`

## Step-by-Step Migration

### 1. Supabase Project Setup

1. Create a new project in Supabase dashboard
2. Go to Settings > API to get your project credentials:
   - Project URL: `https://your-project-ref.supabase.co`
   - Anon key: `eyJhbGciOiJIUzI1NiIsI...` (public key)
   - Service role key: `eyJhbGciOiJIUzI1NiIsI...` (secret key)

### 2. Database Schema Setup

1. In your Supabase dashboard, go to SQL Editor
2. Run the SQL script from `supabase_schema.sql` to create the tables:
   - `referrals` table (replaces NoCodeBackend referrals collection)
   - `documents` table (replaces NoCodeBackend uploads collection)

### 3. Storage Setup

1. Go to Storage in your Supabase dashboard
2. Create two buckets:
   - `documents` - for document files
   - `uploads` - for general uploads
3. Configure bucket policies as needed

### 4. Environment Configuration

Update your `.env` file with Supabase credentials:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
SUPABASE_DOCUMENTS_BUCKET=documents
SUPABASE_UPLOADS_BUCKET=uploads
```

### 5. Data Migration (Optional)

If you have existing data in NoCodeBackend, you'll need to:

1. Export data from NoCodeBackend using their API
2. Transform the data to match the PostgreSQL schema
3. Import into Supabase using the API or SQL

Example data transformation script (customize as needed):

```python
import json
from supabase_client import SupabaseClient

# Initialize Supabase client
client = SupabaseClient()

# Load exported NoCodeBackend data
with open('nocodebackend_export.json', 'r') as f:
    old_data = json.load(f)

# Transform and insert referrals
for referral in old_data['referrals']:
    new_referral = {
        'referral_id': referral.get('_id'),
        'user_id': referral.get('user_id'),
        'patient_name': referral.get('patient_name'),
        'referring_doctor': referral.get('referring_doctor'),
        'target_doctor': referral.get('target_doctor'),
        'medical_condition': referral.get('medical_condition'),
        'status': referral.get('status', 'pending'),
        'notes': referral.get('notes'),
        'created_at': referral.get('created_at')
    }
    result = client.create_referral(new_referral)
    print(f"Migrated referral: {result}")
```

## Code Changes Summary

The migration involves replacing several components:

### Files Replaced/Updated:
- `nocodebackend_client.py` → `supabase_client.py`
- `services/nocodebackend_service.py` → `services/supabase_service.py`
- `controllers/nocodebackend_controller.py` → `controllers/supabase_controller.py`
- `routes/nocode_routes.py` → `routes/supabase_routes.py`
- `utils/nocodebackend_utils.py` → `utils/supabase_utils.py`

### Main Application Updates:
- Updated imports in `app.py`
- Updated blueprint registration
- Added Supabase configuration to `.env.example`
- Updated `requirements.txt`

### API Endpoint Changes:
- `/api/nocode/*` → `/api/supabase/*`
- `/api/nocodebackend/*` → `/api/supabase/*`

## Benefits of Migration

1. **Open Source**: Supabase is open-source and can be self-hosted
2. **PostgreSQL**: Full-featured relational database with ACID compliance
3. **Real-time**: Built-in real-time subscriptions for live updates
4. **Performance**: Better query performance and indexing
5. **Security**: Row Level Security (RLS) policies for data protection
6. **Cost**: Transparent pricing with generous free tier
7. **Ecosystem**: Rich ecosystem of tools and integrations

## Testing the Migration

1. Start the Flask application: `python app.py`
2. Test the new endpoints:
   ```bash
   # Health check
   curl http://localhost:5000/api/supabase/health
   
   # Get referrals (requires authentication)
   curl http://localhost:5000/api/supabase/referrals
   
   # Create referral
   curl -X POST http://localhost:5000/api/supabase/referrals \
     -H "Content-Type: application/json" \
     -d '{"patient_name": "Test Patient", "medical_condition": "Test"}'
   ```

## Troubleshooting

### Common Issues:

1. **Import errors**: Make sure all new files are in the correct directories
2. **Database connection**: Verify Supabase URL and keys in `.env`
3. **RLS policies**: Adjust Row Level Security policies if getting permission errors
4. **Storage access**: Check bucket policies and CORS settings

### Debug Steps:

1. Check Supabase logs in dashboard
2. Enable Flask debug mode: `FLASK_ENV=development`
3. Check application logs for detailed error messages

## Rollback Plan

If you need to rollback to NoCodeBackend:

1. Revert the code changes in `app.py`
2. Restore original files from backup
3. Update environment variables back to NoCodeBackend
4. Restart the application

## Performance Considerations

- Use database indexes for frequently queried columns
- Implement pagination for large datasets
- Use Supabase CDN for file delivery
- Consider caching for read-heavy operations

## Security Recommendations

1. Use Row Level Security (RLS) policies
2. Rotate API keys regularly
3. Use service role key only for admin operations
4. Implement proper input validation
5. Use HTTPS in production

## Next Steps

After successful migration:

1. Monitor application performance
2. Set up database backups
3. Configure alerts and monitoring
4. Update documentation
5. Train team on Supabase dashboard
6. Remove NoCodeBackend dependencies

## Support

- Supabase Documentation: https://supabase.com/docs
- Supabase Community: https://github.com/supabase/supabase/discussions
- Flask Documentation: https://flask.palletsprojects.com/