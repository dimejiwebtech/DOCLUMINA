# management/commands/cleanup_trash.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from blog.models import Post


class Command(BaseCommand):
    help = 'Permanently delete posts that have been in trash for more than 30 days'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days after which trashed posts are permanently deleted',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        cutoff_date = timezone.now() - timedelta(days=days)
        expired_posts = Post.all_objects.filter(
            is_trashed=True,
            trashed_at__lt=cutoff_date
        )
        
        count = expired_posts.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No posts found to delete.')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would permanently delete {count} posts:')
            )
            for post in expired_posts:
                days_in_trash = (timezone.now() - post.trashed_at).days
                self.stdout.write(f'  - "{post.title}" ({days_in_trash} days in trash)')
        else:
            # List posts before deletion
            self.stdout.write(f'Permanently deleting {count} posts:')
            for post in expired_posts:
                days_in_trash = (timezone.now() - post.trashed_at).days
                self.stdout.write(f'  - "{post.title}" ({days_in_trash} days in trash)')
            
            # Delete posts
            expired_posts.delete()
            
            self.stdout.write(
                self.style.SUCCESS(f'Successfully deleted {count} posts.')
            )