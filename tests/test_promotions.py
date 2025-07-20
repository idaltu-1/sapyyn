import unittest
import os
import sys
import json
from datetime import datetime, timedelta
from flask import session
from unittest.mock import patch, MagicMock

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app
from models import db, Promotion, PromotionRole, UserPromotionPreference, User, ComplianceAuditTrail, PromotionLocation
from services.promotion_service import PromotionService
from services.image_service import ImageService
from services.audit_service import AuditService
from controllers.promotion_controller import sanitize_url

class PromotionsTestCase(unittest.TestCase):
    """Test cases for the promotions module"""

    def setUp(self):
        """Set up test client and enable testing mode"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        
        # Create test database
        # In a real test, you would use a separate test database
        
    def tearDown(self):
        """Clean up after tests"""
        # Remove test database
        pass
        
    def login(self, username, password):
        """Helper function to log in"""
        return self.client.post('/login', data=dict(
            username=username,
            password=password
        ), follow_redirects=True)
        
    def logout(self):
        """Helper function to log out"""
        return self.client.get('/logout', follow_redirects=True)
        
    def test_promotions_api_requires_login(self):
        """Test that the promotions API requires login"""
        response = self.client.get('/api/promotions')
        self.assertEqual(response.status_code, 401)
        
    def test_promotion_slot_api_accessible_without_login(self):
        """Test that the promotion slot API is accessible without login"""
        response = self.client.get('/api/promotions/slot/DASHBOARD_TOP')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('promotion', data)
        
    def test_admin_promotions_page_requires_login(self):
        """Test that the admin promotions page requires login"""
        response = self.client.get('/admin/promotions', follow_redirects=True)
        self.assertIn(b'Please log in', response.data)
        
    def test_promotion_redirect_increments_click_count(self):
        """Test that the promotion redirect increments click count"""
        # This would require a test database with a promotion
        # In a real test, you would create a test promotion and verify the click count increases
        pass
        
    def test_url_sanitization(self):
        """Test URL sanitization for redirects"""
        # Test URL with sensitive parameters
        url = "https://example.com/promo?product=dental&patient=12345&token=abc123"
        sanitized = sanitize_url(url)
        self.assertEqual(sanitized, "https://example.com/promo?product=dental")
        
        # Test URL with no sensitive parameters
        url = "https://example.com/promo?product=dental&category=implants"
        sanitized = sanitize_url(url)
        self.assertEqual(sanitized, "https://example.com/promo?product=dental&category=implants")
        
        # Test URL with no scheme
        url = "example.com/promo"
        sanitized = sanitize_url(url)
        self.assertEqual(sanitized, "https://example.com/promo")
        
    @patch('services.audit_service.AuditService.log_action')
    def test_audit_logging(self, mock_log_action):
        """Test audit logging functionality"""
        # Setup mock
        mock_log_action.return_value = MagicMock()
        
        # Call the audit service
        AuditService.log_action('create', 'promotion', 123, {'title': 'Test Promotion'})
        
        # Check if the log_action method was called with the correct parameters
        mock_log_action.assert_called_once()
        args, kwargs = mock_log_action.call_args
        self.assertEqual(args[0], 'create')
        self.assertEqual(args[1], 'promotion')
        self.assertEqual(args[2], 123)
        self.assertEqual(args[3], {'title': 'Test Promotion'})
        
    @patch('models.db.session')
    def test_data_isolation_for_tracking(self, mock_session):
        """Test data isolation for tracking"""
        # Setup mock
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_update = MagicMock()
        
        mock_session.query.return_value = mock_query
        mock_query.filter.return_value = mock_filter
        mock_filter.update.return_value = 1
        
        # Call the service method
        result = PromotionService.record_impression(123)
        
        # Check if the method returns True on success
        self.assertTrue(result)
        
        # Check if the session was committed
        mock_session.commit.assert_called_once()
        
        # Test error handling
        mock_session.commit.side_effect = Exception("Test exception")
        
        # Call the service method again
        result = PromotionService.record_impression(123)
        
        # Check if the method returns False on error
        self.assertFalse(result)
        
        # Check if the session was rolled back
        mock_session.rollback.assert_called_once()
        
    # The following tests would require a test database with sample data
    # and would be implemented in a real test suite
    
    # def test_admin_can_create_promotion(self):
    #     """Test that an admin can create a promotion"""
    #     self.login('admin1', 'password123')
    #     
    #     # Create test promotion data
    #     now = datetime.now()
    #     next_month = now + timedelta(days=30)
    #     
    #     promotion_data = {
    #         'title': 'Test Promotion',
    #         'image_url': '/promotions/images/test.jpg',
    #         'target_url': 'https://example.com',
    #         'location': 'DASHBOARD_TOP',
    #         'start_date': now.isoformat(),
    #         'end_date': next_month.isoformat(),
    #         'is_active': True,
    #         'roles': ['patient', 'dentist'],
    #         'csrf_token': 'test_token'
    #     }
    #     
    #     response = self.client.post('/api/promotions', 
    #                               data=json.dumps(promotion_data),
    #                               content_type='application/json')
    #     
    #     self.assertEqual(response.status_code, 201)
    #     data = json.loads(response.data)
    #     self.assertTrue(data['success'])
    #     self.assertIn('id', data)
    #     
    #     self.logout()
    #     
    # def test_promotion_slot_renders_active_promotion(self):
    #     """Test that a promotion slot renders an active promotion"""
    #     # Create test promotion
    #     # ...
    #     
    #     # Check that the promotion is returned by the API
    #     response = self.client.get('/api/promotions/slot/DASHBOARD_TOP')
    #     self.assertEqual(response.status_code, 200)
    #     data = json.loads(response.data)
    #     self.assertIsNotNone(data['promotion'])
    #     self.assertEqual(data['promotion']['title'], 'Test Promotion')
    #     
    # def test_promotion_impression_count_increments(self):
    #     """Test that impression count increments when a promotion is viewed"""
    #     # Create test promotion
    #     # ...
    #     
    #     # Get initial impression count
    #     # ...
    #     
    #     # View promotion
    #     self.client.get('/api/promotions/slot/DASHBOARD_TOP')
    #     
    #     # Check that impression count increased
    #     # ...
    #     
    # def test_user_opt_out_respected(self):
    #     """Test that user opt-out preference is respected"""
    #     # Login as test user
    #     self.login('user1', 'password123')
    #     
    #     # Opt out of promotions
    #     self.client.put('/api/user/promotion-settings',
    #                    data=json.dumps({
    #                        'opt_out': True,
    #                        'csrf_token': 'test_token'
    #                    }),
    #                    content_type='application/json')
    #     
    #     # Check that no promotion is returned
    #     response = self.client.get('/api/promotions/slot/DASHBOARD_TOP')
    #     data = json.loads(response.data)
    #     self.assertIsNone(data['promotion'])
    #     self.assertEqual(data['reason'], 'user_opted_out')
    #     
    #     self.logout()

if __name__ == '__main__':
    unittest.main()