import platform
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.storage import default_storage
from media_manager.models import MediaFile
from .tasks import compress_media_file

def sync_to_media_manager(instance):
    """Syncs all file and image fields from any model to MediaFile."""
    for field in instance._meta.get_fields():
        if field.get_internal_type() in ['FileField', 'ImageField']:
            file_field = getattr(instance, field.name, None)
            if file_field and hasattr(file_field, 'name') and file_field.name:
                relative_path = file_field.name
                if not MediaFile.objects.filter(file=relative_path).exists():
                    media_file = MediaFile.objects.create(file=relative_path)
                    
                    # Auto-compress only on Linux (production)
                    if platform.system() != 'Windows':
                        compress_media_file.delay(media_file.id)

@receiver(post_save, sender=MediaFile)
def compress_new_media(sender, instance, created, **kwargs):
    """Compress newly uploaded MediaFile instances - Linux only"""
    if created and instance.file and platform.system() != 'Windows':
        compress_media_file.delay(instance.id)

@receiver(post_save)
def media_post_save(sender, instance, **kwargs):
    """Global signal for syncing uploaded files."""
    if sender.__name__ == 'MediaFile':
        return
    sync_to_media_manager(instance)