# Link Mapping Analysis - Missing Routes

## Critical Missing Routes Found

Based on the search results, the following routes are referenced in templates but missing from app.py:

### 1. Missing Core Routes
- `get_started_page` - Referenced in login.html and base.html
- `forgot_password` - Referenced in login.html and forgot_password.html
- `change_password` - Referenced in settings.html
- `profile` - Referenced in multiple templates
- `edit_profile` - Referenced in profile.html
- `view_documents` - Referenced in dashboard.html and other templates
- `conversion_dashboard` - Referenced in dashboard.html
- `track_referral` - Referenced in track_referral.html

### 2. Missing Portal Routes
- `portal_appointments` - Referenced in portal templates (should be `/portal/appointments`)
- `messages_portal` - Referenced in portal templates (should be `/portal/messages`)
- `rewards_dashboard` - Referenced in multiple templates
- `rewards_admin` - Referenced in rewards templates
- `new_reward_program` - Referenced in rewards templates
- `edit_reward_program` - Referenced in rewards templates
- `rewards_leaderboard` - Referenced in rewards templates
- `compliance_audit` - Referenced in rewards templates

### 3. Missing Admin Routes
- `admin_panel` - Referenced in base.html
- `serve_static_page` - Referenced in base.html for admin pages
- `new_promotion` - Referenced in admin_promotions.html
- `toggle_promotion` - Referenced in admin_promotions.html

### 4. Missing Promotion Routes
- `promotions_list` - Referenced in promotion templates
- `promotions_create` - Referenced in promotion templates
- `promotions_edit` - Referenced in promotion templates
- `promotion_click` - Referenced in promotion templates

### 5. Missing Static Page Routes
- `about` - Referenced in base.html
- `blog` - Referenced in base.html
- `surgical_instruction` - Referenced in base.html
- `how_to_guides` - Referenced in base.html

### 6. Missing Subscription Routes
- `subscribe` - Referenced in pricing.html
- `start_free_trial` - Referenced in index.html and pricing.html

## Routes That Exist But May Have Different Names
- `my_referrals` - Exists in app.py
- `dashboard` - Exists in app.py
- `new_referral` - Exists in app.py
- `login` - Exists in app.py
- `register` - Exists in app.py
- `logout` - Exists in app.py

## Recommendations

1. **Add missing core routes** to app.py
2. **Create proper portal route mappings**
3. **Add missing admin and promotion routes**
4. **Ensure all static page routes are properly mapped**
5. **Add subscription and payment routes**
6. **Update templates to use correct route names where needed**

## Priority Fixes Needed

### High Priority (Breaking Navigation)
1. `get_started_page` - Critical for user onboarding
2. `profile` and `edit_profile` - User account management
3. `view_documents` - Core functionality
4. `portal_appointments` - Portal navigation
5. `messages_portal` - Portal navigation

### Medium Priority (Feature Completion)
1. Rewards system routes
2. Admin panel routes
3. Promotion management routes
4. Static page routes

### Low Priority (Enhancement)
1. Analytics routes
2. Advanced admin features
3. Additional static pages
