import unittest
import os
import sys
import io
from flask import session

# Add parent directory to path to import app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import app, scan_file_for_viruses

class DocumentUploadTestCase(unittest.TestCase):
    """Test cases for document upload functionality"""

    def setUp(self):
        """Set up test client and enable testing mode"""
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()
        
    def tearDown(self):
        """Clean up after tests"""
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
        
    def test_upload_page_requires_login(self):
        """Test that the upload page requires login"""
        response = self.client.get('/upload', follow_redirects=True)
        self.assertIn(b'Please log in', response.data)
        
    def test_virus_scan_clean_file(self):
        """Test virus scan function with clean file"""
        # Create a mock file
        file_data = io.BytesIO(b'Test file content')
        file_data.filename = 'test.txt'
        
        # Test the virus scan function
        result = scan_file_for_viruses(file_data)
        self.assertTrue(result['clean'])
        
    def test_virus_scan_dangerous_extension(self):
        """Test virus scan function with dangerous extension"""
        # Create a mock file with dangerous extension
        file_data = io.BytesIO(b'Test file content')
        file_data.filename = 'test.exe'
        
        # Test the virus scan function
        result = scan_file_for_viruses(file_data)
        self.assertFalse(result['clean'])
        
    def test_allowed_file_function(self):
        """Test the allowed_file function"""
        from app import allowed_file
        
        # Test allowed extensions
        self.assertTrue(allowed_file('test.pdf'))
        self.assertTrue(allowed_file('test.jpg'))
        self.assertTrue(allowed_file('test.png'))
        self.assertTrue(allowed_file('test.doc'))
        self.assertTrue(allowed_file('test.docx'))
        
        # Test disallowed extensions
        self.assertFalse(allowed_file('test.exe'))
        self.assertFalse(allowed_file('test.php'))
        self.assertFalse(allowed_file('test.js'))
        
    # The following tests would require a test database and file system
    # and would be implemented in a real test suite
    
    # def test_upload_file_success(self):
    #     """Test successful file upload"""
    #     self.login('user1', 'password123')
    #     
    #     # Create a test file
    #     file_data = io.BytesIO(b'Test file content')
    #     
    #     response = self.client.post('/upload', 
    #                               data={
    #                                   'file': (file_data, 'test.pdf'),
    #                                   'file_type': 'supporting_documents',
    #                                   'csrf_token': 'test_token'
    #                               },
    #                               content_type='multipart/form-data',
    #                               follow_redirects=True)
    #     
    #     self.assertIn(b'File uploaded successfully', response.data)
    #     self.logout()
    #     
    # def test_upload_file_invalid_type(self):
    #     """Test file upload with invalid file type"""
    #     self.login('user1', 'password123')
    #     
    #     # Create a test file with invalid extension
    #     file_data = io.BytesIO(b'Test file content')
    #     
    #     response = self.client.post('/upload', 
    #                               data={
    #                                   'file': (file_data, 'test.exe'),
    #                                   'file_type': 'supporting_documents',
    #                                   'csrf_token': 'test_token'
    #                               },
    #                               content_type='multipart/form-data',
    #                               follow_redirects=True)
    #     
    #     self.assertIn(b'Invalid file type', response.data)
    #     self.logout()
    #     
    # def test_upload_file_virus_detected(self):
    #     """Test file upload with virus detection"""
    #     # This would require mocking the virus scan function
    #     pass

if __name__ == '__main__':
    unittest.main()