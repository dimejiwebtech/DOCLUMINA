from celery import shared_task
from .models import MediaFile
from .compression import MediaCompressor

@shared_task(bind=True, max_retries=3)
def compress_media_file(self, media_file_id):
    """Background compression task"""
    try:
        media_file = MediaFile.objects.get(id=media_file_id)
        file_path = media_file.file.name
        
        if media_file.file_type == 'image':
            success = MediaCompressor.compress_image(file_path)
        elif media_file.file_type == 'document' and file_path.lower().endswith('.pdf'):
            success = MediaCompressor.compress_pdf(file_path)
        else:
            return f"No compression for file type: {media_file.file_type}"
        
        if success:
            return f"Compressed: {file_path}"
        else:
            raise Exception("Compression failed")
            
    except MediaFile.DoesNotExist:
        return "Media file not found"
    except Exception as e:
        # Shorter retry delay for Windows file locks
        self.retry(countdown=30, exc=e)

    @property
    def file_type(self):
        """Auto-detect file type based on extension"""
        if not self.file:
            return 'other'
        
        name = self.file.name.lower()
        if name.endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp')):
            return 'image'
        elif name.endswith(('.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv')):
            return 'video'
        elif name.endswith(('.mp3', '.wav', '.ogg', '.m4a', '.flac')):
            return 'audio'
        elif name.endswith(('.pdf', '.docx', '.pptx', '.doc', '.txt', '.rtf')):
            return 'document'
        elif name.endswith(('.xlsx', '.xls', '.csv', '.ods')):
            return 'spreadsheet'
        return 'other'