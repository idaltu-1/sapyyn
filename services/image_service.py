"""
Image service for handling promotion images
"""

import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import io

class ImageService:
    """Service for handling promotion images"""
    
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
    MAX_SIZE_KB = 500  # 500 KB
    UPLOAD_FOLDER = 'static/uploads/promotions'
    
    @classmethod
    def validate_promotion_image(cls, image_file):
        """Validate promotion image size and format
        
        Args:
            image_file: The uploaded file object
            
        Returns:
            dict: Validation result with 'valid' and 'message' keys
        """
        # Check if file exists
        if not image_file:
            return {'valid': False, 'message': 'No file provided'}
        
        # Check file extension
        filename = image_file.filename
        if not '.' in filename or filename.rsplit('.', 1)[1].lower() not in cls.ALLOWED_EXTENSIONS:
            return {'valid': False, 'message': f'Invalid file format. Allowed formats: {", ".join(cls.ALLOWED_EXTENSIONS)}'}
        
        # Check file size
        image_file.seek(0, os.SEEK_END)
        file_size_kb = image_file.tell() / 1024
        image_file.seek(0)  # Reset file pointer
        
        if file_size_kb > cls.MAX_SIZE_KB:
            return {'valid': False, 'message': f'File size exceeds maximum allowed ({cls.MAX_SIZE_KB} KB)'}
        
        # Validate image dimensions and format
        try:
            img = Image.open(image_file)
            img.verify()  # Verify it's a valid image
            image_file.seek(0)  # Reset file pointer after verification
            
            # Check image dimensions
            img = Image.open(image_file)
            width, height = img.size
            image_file.seek(0)  # Reset file pointer
            
            if width < 50 or height < 50:
                return {'valid': False, 'message': 'Image dimensions too small (minimum 50x50 pixels)'}
            
            if width > 2000 or height > 2000:
                return {'valid': False, 'message': 'Image dimensions too large (maximum 2000x2000 pixels)'}
            
            return {'valid': True, 'message': 'Image is valid'}
            
        except Exception as e:
            return {'valid': False, 'message': f'Invalid image: {str(e)}'}
    
    @classmethod
    def save_promotion_image(cls, image_file):
        """Save promotion image and return the URL
        
        Args:
            image_file: The uploaded file object
            
        Returns:
            str: URL of the saved image or None if failed
        """
        # Ensure upload directory exists
        os.makedirs(cls.UPLOAD_FOLDER, exist_ok=True)
        
        # Validate image
        validation = cls.validate_promotion_image(image_file)
        if not validation['valid']:
            return None
        
        # Generate unique filename
        original_filename = secure_filename(image_file.filename)
        file_extension = original_filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{file_extension}"
        
        # Save the image
        file_path = os.path.join(cls.UPLOAD_FOLDER, unique_filename)
        
        # Optimize image before saving
        try:
            img = Image.open(image_file)
            
            # Convert to RGB if RGBA (remove transparency)
            if img.mode == 'RGBA':
                img = img.convert('RGB')
            
            # Resize if too large
            max_dimension = 1200
            width, height = img.size
            if width > max_dimension or height > max_dimension:
                if width > height:
                    new_width = max_dimension
                    new_height = int(height * (max_dimension / width))
                else:
                    new_height = max_dimension
                    new_width = int(width * (max_dimension / height))
                img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Save with optimized quality
            img.save(file_path, optimize=True, quality=85)
            
            # Return the URL (relative to the application root)
            return f"/{file_path}"
            
        except Exception as e:
            print(f"Error saving image: {str(e)}")
            return None