from django.core.management.base import BaseCommand
from media_manager.models import MediaFile
from media_manager.tasks import compress_media_file

class Command(BaseCommand):
    help = 'Compress uncompressed media files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Compress all images (including WebP)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=10,
            help='Number of files to process at once',
        )

    def handle(self, *args, **options):
        if options['all']:
            queryset = MediaFile.objects.filter(category='image')
        else:
            # Only compress non-WebP images
            queryset = MediaFile.objects.filter(
                category='image'
            ).exclude(file__endswith='.webp')

        files = queryset[:options['limit']]
        
        if not files:
            self.stdout.write(
                self.style.SUCCESS('No files to compress')
            )
            return

        for media_file in files:
            compress_media_file.delay(media_file.id)
            self.stdout.write(
                f'Queued compression for: {media_file.file.name}'
            )

        self.stdout.write(
            self.style.SUCCESS(
                f'Queued {len(files)} files for compression'
            )
        )