# MongoDB Migration Documentation

## Overview
This document outlines the migration from NoCodeBackend to MongoDB for the Sapyyn patient referral system.

## Changes Made

### 1. Database Backend Replacement
- **Removed**: NoCodeBackend integration
- **Added**: Native MongoDB integration with pymongo

### 2. New Files Created
- `mongodb_client.py` - Core MongoDB client with CRUD operations
- `services/mongodb_service.py` - Service layer for MongoDB operations
- `controllers/mongodb_controller.py` - Flask API controller (maintains same endpoints)
- `utils/mongodb_utils.py` - Utility functions for MongoDB operations
- `migrate_to_mongodb.py` - Data migration script from SQLite to MongoDB
- `test_mongodb_integration.py` - Integration test suite

### 3. Files Modified
- `app.py` - Updated imports to use MongoDB controller
- `requirements.txt` - Added pymongo dependency
- `.env.example` - Updated configuration for MongoDB
- `routes/nocode_routes.py` - Updated to use MongoDB utils
- `controllers/nocodebackend_controller.py` - Kept for backward compatibility

### 4. Configuration Changes
- **Added MongoDB settings**:
  - `MONGODB_URL=mongodb://localhost:27017/sapyyn`
  - `MONGODB_DB_NAME=sapyyn`
- **Removed NoCodeBackend settings**:
  - `NOCODEBACKEND_SECRET_KEY`
  - `NOCODEBACKEND_REFERRAL_INSTANCE`
  - `NOCODEBACKEND_UPLOADS_INSTANCE`

## MongoDB Schema

### Collections

#### referrals
```javascript
{
  _id: ObjectId,
  user_id: String,
  referral_id: String,
  patient_name: String,
  referring_doctor: String,
  target_doctor: String,
  medical_condition: String,
  urgency_level: String,
  status: String,
  notes: String,
  qr_code: String,
  created_at: Date,
  updated_at: Date,
  // Additional fields from SQLite migration
  case_status: String,
  consultation_date: Date,
  estimated_value: Number,
  actual_value: Number
}
```

#### documents
```javascript
{
  _id: ObjectId,
  referral_id: String,
  user_id: String,
  file_id: String, // GridFS file ID
  filename: String,
  content_type: String,
  file_size: Number,
  metadata: Object,
  created_at: Date,
  updated_at: Date
}
```

## API Endpoints (Unchanged)

All existing API endpoints remain the same for backward compatibility:

- `GET /api/nocodebackend/referrals` - List referrals
- `POST /api/nocodebackend/referrals` - Create referral
- `PUT /api/nocodebackend/referrals/{id}` - Update referral
- `GET /api/nocodebackend/referrals/{id}` - Get referral details
- `POST /api/nocodebackend/documents` - Upload document
- `GET /api/nocodebackend/documents` - List documents

### New Endpoints Added
- `GET /api/nocodebackend/referrals/{id}/documents` - Get referral documents
- `GET /api/nocodebackend/search/referrals?q={query}` - Search referrals
- `GET /api/nocodebackend/stats` - Get database statistics

## Installation & Setup

### 1. Install Dependencies
```bash
pip install pymongo>=4.6.0
```

### 2. Start MongoDB
```bash
# Using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest

# Or install MongoDB locally
# https://docs.mongodb.com/manual/installation/
```

### 3. Update Environment Variables
```bash
cp .env.example .env
# Edit .env with your MongoDB connection string
MONGODB_URL=mongodb://localhost:27017/sapyyn
MONGODB_DB_NAME=sapyyn
```

### 4. Migrate Existing Data (Optional)
```bash
python migrate_to_mongodb.py
```

## Testing

Run the integration test suite:
```bash
python test_mongodb_integration.py
```

## Features & Benefits

### Advantages of MongoDB over NoCodeBackend
1. **No External Dependencies** - Self-hosted, no API limits
2. **Better Performance** - Direct database access, no HTTP overhead
3. **Advanced Querying** - MongoDB's powerful query language
4. **File Storage** - GridFS for efficient file handling
5. **Scalability** - MongoDB's horizontal scaling capabilities
6. **Cost Effective** - No per-API-call costs

### New Capabilities
- Full-text search across referrals
- Aggregation pipelines for analytics
- Geospatial queries (future enhancement)
- Real-time change streams
- Advanced indexing strategies

## Backward Compatibility

The migration maintains full backward compatibility:
- All existing API endpoints work unchanged
- Response formats remain the same
- Authentication mechanisms unchanged
- Existing frontend code requires no changes

## Production Deployment

### MongoDB Production Setup
1. Use MongoDB Atlas for managed hosting
2. Configure proper authentication and authorization
3. Set up backup and monitoring
4. Configure indexes for optimal performance

### Environment Variables for Production
```bash
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net/sapyyn
MONGODB_DB_NAME=sapyyn_production
```

### Recommended Indexes
```javascript
// Referrals collection
db.referrals.createIndex({ "user_id": 1 })
db.referrals.createIndex({ "status": 1 })
db.referrals.createIndex({ "referral_id": 1 }, { unique: true })
db.referrals.createIndex({ "created_at": -1 })

// Documents collection
db.documents.createIndex({ "referral_id": 1 })
db.documents.createIndex({ "user_id": 1 })
db.documents.createIndex({ "filename": "text" })
```

## Troubleshooting

### Common Issues
1. **Connection refused** - Ensure MongoDB is running on port 27017
2. **Import errors** - Install pymongo: `pip install pymongo`
3. **Authentication failed** - Check MongoDB credentials in .env
4. **Migration fails** - Ensure SQLite database exists and is readable

### Support
For issues related to this migration, please:
1. Check the logs in `migration.log`
2. Run the test suite with `python test_mongodb_integration.py`
3. Review MongoDB connection strings and credentials