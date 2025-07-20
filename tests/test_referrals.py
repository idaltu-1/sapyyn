import unittest
import os
import sys
import json
from flask import session

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app

class ReferralsTestCase(unittest.TestCase):
    """Test cases for the referrals module"""

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
        
    def test_referrals_page_requires_login(self):
        """Test that the referrals page requires login"""
        response = self.client.get('/referrals', follow_redirects=True)
        self.assertIn(b'Please log in', response.data)
        
    def test_referrals_api_requires_login(self):
        """Test that the referrals API requires login"""
        response = self.client.get('/api/referrals')
        self.assertEqual(response.status_code, 401)
        
    def test_referral_detail_api_requires_login(self):
        """Test that the referral detail API requires login"""
        response = self.client.get('/api/referrals/1')
        self.assertEqual(response.status_code, 401)
        
    def test_create_referral_api_requires_login(self):
        """Test that the create referral API requires login"""
        response = self.client.post('/api/referrals', 
                                   data=json.dumps({'patient_id': 1, 'patient_name': 'Test Patient'}),
                                   content_type='application/json')
        self.assertEqual(response.status_code, 401)
        
    def test_update_referral_status_api_requires_login(self):
        """Test that the update referral status API requires login"""
        response = self.client.patch('/api/referrals/1/status', 
                                    data=json.dumps({'status': 'completed'}),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 401)
        
    def test_patients_api_requires_login(self):
        """Test that the patients API requires login"""
        response = self.client.get('/api/patients')
        self.assertEqual(response.status_code, 401)
        
    # The following tests would require a test database with sample data
    # and would be implemented in a real test suite
    
    # def test_dentist_can_see_own_referrals(self):
    #     """Test that a dentist can see their own referrals"""
    #     self.login('dentist1', 'password123')
    #     response = self.client.get('/api/referrals')
    #     self.assertEqual(response.status_code, 200)
    #     data = json.loads(response.data)
    #     self.assertIn('referrals', data)
    #     self.logout()
    #     
    # def test_patient_can_see_own_referrals(self):
    #     """Test that a patient can see referrals where they are the patient"""
    #     self.login('patient1', 'password123')
    #     response = self.client.get('/api/referrals')
    #     self.assertEqual(response.status_code, 200)
    #     data = json.loads(response.data)
    #     self.assertIn('referrals', data)
    #     self.logout()
    #     
    # def test_admin_can_see_all_referrals(self):
    #     """Test that an admin can see all referrals"""
    #     self.login('admin1', 'password123')
    #     response = self.client.get('/api/referrals')
    #     self.assertEqual(response.status_code, 200)
    #     data = json.loads(response.data)
    #     self.assertIn('referrals', data)
    #     self.logout()
    #     
    # def test_dentist_can_create_referral(self):
    #     """Test that a dentist can create a referral"""
    #     self.login('dentist1', 'password123')
    #     response = self.client.post('/api/referrals', 
    #                                data=json.dumps({
    #                                    'patient_id': 1, 
    #                                    'patient_name': 'Test Patient',
    #                                    'csrf_token': 'test_token'
    #                                }),
    #                                content_type='application/json')
    #     self.assertEqual(response.status_code, 201)
    #     data = json.loads(response.data)
    #     self.assertTrue(data['success'])
    #     self.assertIn('referral_id', data)
    #     self.logout()
    #     
    # def test_dentist_can_update_referral_status(self):
    #     """Test that a dentist can update the status of their referral"""
    #     self.login('dentist1', 'password123')
    #     # First create a referral
    #     create_response = self.client.post('/api/referrals', 
    #                                      data=json.dumps({
    #                                          'patient_id': 1, 
    #                                          'patient_name': 'Test Patient',
    #                                          'csrf_token': 'test_token'
    #                                      }),
    #                                      content_type='application/json')
    #     data = json.loads(create_response.data)
    #     referral_id = data['id']
    #     
    #     # Then update its status
    #     update_response = self.client.patch(f'/api/referrals/{referral_id}/status', 
    #                                       data=json.dumps({
    #                                           'status': 'completed',
    #                                           'csrf_token': 'test_token'
    #                                       }),
    #                                       content_type='application/json')
    #     self.assertEqual(update_response.status_code, 200)
    #     update_data = json.loads(update_response.data)
    #     self.assertTrue(update_data['success'])
    #     self.logout()
    #     
    # def test_patient_cannot_update_referral_status(self):
    #     """Test that a patient cannot update referral status"""
    #     self.login('patient1', 'password123')
    #     response = self.client.patch('/api/referrals/1/status', 
    #                                 data=json.dumps({
    #                                     'status': 'completed',
    #                                     'csrf_token': 'test_token'
    #                                 }),
    #                                 content_type='application/json')
    #     self.assertEqual(response.status_code, 403)
    #     self.logout()

if __name__ == '__main__':
    unittest.main()