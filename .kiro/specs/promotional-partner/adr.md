# Architectural Decision Record: Promotional-Partner / Ad-Space Module

## Status

Accepted

## Context

The Sapyyn Patient Referral System needs a feature that allows practices to sell, place, and track sponsored content throughout the portal. This feature must generate additional revenue while maintaining HIPAA compliance and providing a good user experience.

## Decision Drivers

1. **HIPAA Compliance**: The system must maintain strict compliance with healthcare privacy regulations.
2. **User Experience**: Promotional content should be relevant and non-intrusive.
3. **Revenue Generation**: The system should provide value to both the practice and promotional partners.
4. **Performance**: The promotion system should not significantly impact application performance.
5. **Maintainability**: The code should be well-structured and easy to maintain.
6. **Flexibility**: The system should support various promotion types and placement locations.

## Decisions

### 1. Database Schema

We decided to use a relational database schema with the following tables:
- `promotions`: Stores promotion details including title, image URL, target URL, location, date range, and tracking metrics.
- `promotion_roles`: Stores role-based targeting information for promotions.
- `user_promotion_preferences`: Stores user preferences for opting out of targeted promotions.

This approach provides:
- Clear separation of concerns between promotion content and targeting rules
- Efficient querying for promotion selection
- Support for user preferences and privacy controls

### 2. Ad Slot Locations

We defined specific locations for promotional content:
- `DASHBOARD_TOP`: Banner at the top of the dashboard
- `DASHBOARD_SIDEBAR`: Sidebar placement on the dashboard
- `DOCUMENTS_BANNER`: Banner in the documents section
- `REFERRALS_PAGE`: Placement on the referrals listing page
- `PROFILE_PAGE`: Placement on user profile pages

These locations were chosen to:
- Provide visibility without disrupting core workflows
- Offer contextually relevant placement options
- Ensure consistent user experience across the application

### 3. Promotion Selection Algorithm

We implemented a weighted round-robin selection algorithm that:
- Prioritizes promotions with fewer impressions to ensure fair rotation
- Filters promotions based on user role and preferences
- Respects date ranges and active status
- Falls back to house ads when no matching promotions are available

This approach:
- Ensures fair distribution of impressions across all active promotions
- Respects user preferences and targeting rules
- Provides a consistent experience even when no partner promotions are available

### 4. Privacy Safeguards

We implemented several privacy safeguards:
- No PHI (Protected Health Information) is ever associated with promotion tracking
- User role-based targeting without exposing individual user data
- Opt-out mechanism for users who prefer not to see targeted promotions
- Clear labeling of all promotional content as "Sponsored"
- Secure redirect mechanism that prevents leaking of user data to partners
- No cookies or tracking pixels from third parties

### 5. Tracking Mechanism

We decided to implement server-side tracking that:
- Records impressions when promotions are rendered
- Tracks clicks through a redirect endpoint that logs the click before forwarding to the target URL
- Uses atomic database updates to ensure accurate metrics
- Provides real-time statistics in the admin interface

This approach:
- Ensures accurate tracking without relying on client-side scripts
- Prevents data leakage to third parties
- Provides reliable metrics for reporting

### 6. Admin Interface

We implemented a comprehensive admin interface that:
- Provides CRUD operations for promotions
- Includes image upload with validation
- Offers date range selection and targeting options
- Displays real-time performance metrics
- Supports filtering and sorting of promotions

## Consequences

### Positive

1. **Revenue Generation**: Practices can generate additional revenue through promotional partnerships.
2. **User Control**: Users have control over their promotional experience with opt-out options.
3. **HIPAA Compliance**: The system maintains strict privacy controls and data separation.
4. **Performance**: Server-side rendering and tracking minimizes client-side performance impact.
5. **Flexibility**: The system supports various promotion types and targeting options.

### Negative

1. **Increased Complexity**: The addition of the promotion system increases the overall complexity of the application.
2. **Database Load**: Tracking impressions and clicks adds additional database operations.
3. **Maintenance Overhead**: The promotion system requires ongoing maintenance and monitoring.

### Neutral

1. **Storage Requirements**: The system requires additional storage for promotion images, but the impact is minimal with size restrictions.
2. **User Interface Changes**: The application UI now includes promotional slots, which may affect the visual design but is controlled and consistent.

## Compliance Considerations

The Promotional-Partner / Ad-Space Module has been designed with HIPAA compliance as a primary concern:

1. **Data Separation**: Promotion tracking data is completely separate from patient data.
2. **No PHI Transmission**: No Protected Health Information is ever transmitted to promotional partners.
3. **User Consent**: Users can opt out of targeted promotions at any time.
4. **Transparent Labeling**: All promotional content is clearly labeled as "Sponsored".
5. **Audit Trail**: All promotion management actions are logged for compliance purposes.

## Future Considerations

1. **Advanced Targeting**: Consider adding more sophisticated targeting options based on specialization or geography.
2. **A/B Testing**: Implement A/B testing capabilities for promotional content.
3. **Automated Optimization**: Develop algorithms to automatically optimize promotion placement based on performance.
4. **Integration with External Ad Networks**: Consider integration with healthcare-specific ad networks while maintaining compliance.
5. **Enhanced Analytics**: Provide more detailed analytics and reporting capabilities.

## References

1. HIPAA Privacy Rule: [HHS.gov](https://www.hhs.gov/hipaa/for-professionals/privacy/index.html)
2. Healthcare Advertising Guidelines: [FDA.gov](https://www.fda.gov/medical-devices/device-advice-comprehensive-regulatory-assistance/advertising-and-promotional-labeling-medical-devices)
3. Web Content Accessibility Guidelines: [WCAG 2.1](https://www.w3.org/TR/WCAG21/)