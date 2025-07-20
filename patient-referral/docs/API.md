# Sapyyn API Documentation

## Overview

The Sapyyn Patient Referral System API provides endpoints for managing patient documents, referrals, and healthcare provider connections.

## Base URL

- Development: `http://localhost:3000/api`
- Production: `https://api.sapyyn.com`

## Authentication

All API endpoints require authentication using JWT tokens.

```
Authorization: Bearer <token>
```

## Endpoints

### Authentication

#### POST /auth/login
Login with credentials

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "token": "jwt-token",
  "user": {
    "id": "user-id",
    "email": "user@example.com",
    "role": "provider"
  }
}
```

### Documents

#### GET /documents
List all documents for authenticated user

**Query Parameters:**
- `category`: Filter by document category
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20)

#### POST /documents/upload
Upload a new document

**Request:**
- Content-Type: multipart/form-data
- Fields:
  - `file`: Document file
  - `category`: Document category
  - `description`: Optional description

#### GET /documents/:id
Get specific document details

#### DELETE /documents/:id
Delete a document

### Referrals

#### POST /referrals
Create a new patient referral

**Request:**
```json
{
  "patientId": "patient-id",
  "providerId": "provider-id",
  "documentIds": ["doc1", "doc2"],
  "notes": "Additional information"
}
```

#### GET /referrals
List referrals

#### GET /referrals/:id
Get referral details

### QR Codes

#### POST /qr-codes/generate
Generate QR code for patient/document access

**Request:**
```json
{
  "type": "patient|document",
  "id": "resource-id",
  "expiresIn": "24h"
}
```

## Error Responses

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {}
  }
}
```

Common error codes:
- `UNAUTHORIZED`: Missing or invalid authentication
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Invalid request data
- `SERVER_ERROR`: Internal server error