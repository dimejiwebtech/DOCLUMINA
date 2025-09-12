import os
from PIL import Image, ImageOps
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
import PyPDF2
from io import BytesIO

class MediaCompressor:
    # Image settings
    IMAGE_QUALITY = 85
    MAX_IMAGE_SIZE = (1920, 1080)
    
    @staticmethod
    def compress_image(file_path):
        """Compress image files"""
        try:
            with default_storage.open(file_path, 'rb') as f:
                image = Image.open(f)
                
                # Convert RGBA to RGB if needed
                if image.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', image.size, (255, 255, 255))
                    if image.mode == 'P':
                        image = image.convert('RGBA')
                    background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                    image = background
                
                # Auto-orient based on EXIF
                image = ImageOps.exif_transpose(image)
                
                # Resize if too large
                image.thumbnail(MediaCompressor.MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
                
                # Save compressed
                output = BytesIO()
                image.save(output, format='JPEG', quality=MediaCompressor.IMAGE_QUALITY, optimize=True)
                output.seek(0)
                
                # Replace original file
                default_storage.delete(file_path)
                default_storage.save(file_path, ContentFile(output.read()))
                
                return True
        except Exception as e:
            print(f"Image compression failed for {file_path}: {e}")
            return False
    
    @staticmethod
    def compress_pdf(file_path):
        """Basic PDF compression by removing metadata"""
        try:
            with default_storage.open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                writer = PyPDF2.PdfWriter()
                
                for page in reader.pages:
                    writer.add_page(page)
                
                # Remove metadata
                writer.add_metadata({})
                
                output = BytesIO()
                writer.write(output)
                output.seek(0)
                
                # Replace original
                default_storage.delete(file_path)
                default_storage.save(file_path, ContentFile(output.read()))
                
                return True
        except Exception as e:
            print(f"PDF compression failed for {file_path}: {e}")