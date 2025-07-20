# Promotional-Partner / Ad-Space Module Technical Documentation

## Overview

The Promotional-Partner / Ad-Space Module enables dental practices to monetize their Sapyyn portal by displaying sponsored content from partners while maintaining HIPAA compliance. This document provides technical details about the implementation.

## Database Schema

### Promotions Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| title | String | Title of the promotion |
| description | Text | Optional description |
| image_url | String | Path to the promotion image |
| target_url | String | Destination URL when clicked |
| location | Enum | Placement location |
| start_date | DateTime | When to start showing the promotion |
| end_date | DateTime | When to stop showing the promotion |
| is_active | Boolean | Whether the promotion is currently active |
| impression_count | Integer | Number of times the promotion was displayed |
| click_count | Integer | Number of times the promotion was clicked |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last update timestamp |

### Promotion Roles Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| promotion_id | Integer | Foreign key to promotions table |
| role | String | User role that can see this promotion |
| created_at | DateTime | Creation timestamp |

### User Promotion Preferences Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key to users table |
| opt_out | Boolean | Whether user has opted out of targeted promotions |
| updated_at | DateTime | Last update timestamp |

### Compliance Audit Trail Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key |
| user_id | Integer | Foreign key to users table |
| action_type | String | The action performed |
| entity_type | String | The type of entity |
| entity_id | String | The ID of the entity |
| action_details | Text (JSON) | Additional details about the action |
| ip_address | String | IP address of the user |
| user_agent | String | User agent of the browser |
| timestamp | DateTime | When the action occurred |

## API Endpoints

### Admin Endpoints

- `GET /admin/promotions/` - List all promotions
- `GET /admin/promotions/create` - Show promotion creation form
- `POST /admin/promotions/create` - Create a new promotion
- `GET /admin/promotions/<id>/edit` - Show promotion edit form
- `POST /admin/promotions/<id>/edit` - Update a promotion
- `POST /admin/promotions/<id>/delete` - Delete a promotion
- `POST /admin/promotions/<id>/toggle` - Toggle promotion status
- `GET /admin/promotions/<id>/stats` - Get promotion statistics

### User-Facing Endpoints

- `GET /promotions/slot/<location>` - Get a promotion for a location
- `GET /promotions/api/slot/<location>` - API endpoint to get a promotion
- `GET /promotions/redirect/<id>` - Record click and redirect to target URL
- `POST /promotions/preferences` - Update user promotion preferences

## Components

### PromotionService

The `PromotionService` class provides methods for managing promotions:

- `create_promotion(promotion_data)` - Create a new promotion
- `update_promotion(promotion_id, promotion_data)` - Update an existing promotion
- `get_promotion(promotion_id)` - Get a promotion by ID
- `list_promotions(filters=None)` - List promotions with optional filters
- `delete_promotion(promotion_id)` - Delete a promotion
- `toggle_promotion_status(promotion_id, is_active)` - Activate or deactivate a promotion
- `get_promotion_for_location(location, user=None)` - Get an appropriate promotion for a location
- `record_impression(promotion_id)` - Increment impression count
- `record_click(promotion_id)` - Increment click count
- `expire_outdated_promotions()` - Deactivate promotions past their end date

### ImageService

The `ImageService` class handles promotion images:

- `validate_promotion_image(image_file)` - Validate image size and format
- `save_promotion_image(image_file)` - Save and optimize promotion image

### AuditService

The `AuditService` class provides audit logging functionality:

- `log_action(action, entity_type, entity_id, details=None)` - Log an action in the audit log
- `log_promotion_action(action_type, promotion_id, details=None)` - Log a promotion-related action
- `log_promotion_view(promotion_id, location)` - Log a promotion view (impression)
- `log_promotion_click(promotion_id)` - Log a promotion click
- `log_preference_update(user_id, opt_out)` - Log a user preference update

## Promotion Selection Algorithm

The promotion selection algorithm uses a weighted round-robin approach:

1. Filter promotions by location, active status, and date range
2. If user is provided, check opt-out preference
3. If user has opted out, return no promotion
4. Filter promotions by user role if applicable
5. Calculate weights based on inverse of impression count
6. Select a promotion using weighted random selection
7. Return the selected promotion

## HIPAA Compliance Measures

The module implements several measures to ensure HIPAA compliance:

1. **Data Separation**: Promotion tracking data is completely separate from patient data
2. **URL Sanitization**: Sensitive parameters are removed from redirect URLs
3. **Audit Logging**: All promotion management actions are logged
4. **User Consent**: Users can opt out of targeted promotions
5. **Transparent Labeling**: All promotional content is clearly labeled as "Sponsored"

### URL Sanitization

The URL sanitization function removes potentially sensitive parameters from redirect URLs:

```python
def sanitize_url(url, user=None):
    # Parse the URL
    parsed = urlparse(url)
    
    # Get query parameters
    query_params = parse_qs(parsed.query)
    
    # Remove potentially sensitive parameters
    sensitive_params = ['token', 'auth', 'key', 'password', 'secret', 'session', 
                       'user', 'patient', 'medical', 'health', 'record', 'mrn', 
                       'ssn', 'dob', 'birth']
    
    # Remove any parameter that contains sensitive keywords
    sanitized_params = {}
    for key, value in query_params.items():
        is_sensitive = False
        for param in sensitive_params:
            if param.lower() in key.lower():
                is_sensitive = True
                break
        if not is_sensitive:
            sanitized_params[key] = value
    
    # Rebuild the URL
    sanitized_url = urlunparse((
        parsed.scheme,
        parsed.netloc,
        parsed.path,
        parsed.params,
        urlencode(sanitized_params, doseq=True) if sanitized_params else '',
        ''  # Remove fragment to prevent tracking
    ))
    
    return sanitized_url
```

### Data Isolation

The tracking functionality is implemented with data isolation in mind:

1. Tracking operations are performed in isolated transactions
2. Error handling ensures that tracking failures don't affect the main application
3. No PHI is ever associated with tracking data
4. Tracking data is stored in separate tables from patient data

## Cron Jobs

The module includes a cron job to expire outdated promotions:

- `expire_promotions.py` - Deactivates promotions past their end date

## CSS Styles

The module includes CSS styles for promotion slots:

- `.promotion-slot` - Base style for promotion slots
- `.promotion-slot-<location>` - Location-specific styles
- `.promotion-content` - Container for promotion content
- `.promotion-link` - Style for the promotion link
- `.promotion-image` - Style for the promotion image
- `.promotion-info` - Container for promotion information
- `.promotion-label` - Style for the "Sponsored" label
- `.promotion-title` - Style for the promotion title
- `.promotion-description` - Style for the promotion description

## JavaScript Functionality

The module includes JavaScript functionality for loading promotion slots:

- `loadPromotionSlots()` - Load all promotion slots on the page
- `loadPromotionSlot(placeholder, location)` - Load a single promotion slot
- `setupPromotionSettings()` - Set up event listeners for promotion settings
- `showNotification(message, type)` - Show a notification message

## Testing

The module includes comprehensive tests:

- Unit tests for all service methods
- Integration tests for controllers
- Tests for URL sanitization
- Tests for data isolation
- Tests for audit logging

## Deployment Considerations

When deploying the Promotional-Partner module, consider the following:

1. **Database Migrations**: Run migrations to create the necessary tables
2. **Cron Job Setup**: Configure the cron job to run daily
3. **Image Storage**: Ensure the image storage directory is writable
4. **Audit Log Rotation**: Set up log rotation for audit logs
5. **Backup Strategy**: Include promotion data in regular backups