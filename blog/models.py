import math
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.template.defaultfilters import slugify
from django.utils.html import strip_tags
from django.db.models import Sum
from django_ckeditor_5.fields import CKEditor5Field


class BaseContentQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_trashed=False)
    
    def trashed(self):
        return self.filter(is_trashed=True)
    
    def published(self):
        return self.active().filter(status='published')

class BaseContentManager(models.Manager):
    def get_queryset(self):
        return BaseContentQuerySet(self.model, using=self._db)
    
    def active(self):
        return self.get_queryset().active()
    
    def published(self):
        return self.get_queryset().published()
    



class BaseContent(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('trashed', 'Trashed'),
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='%(app_label)s_%(class)s_authored')
    author_name = models.CharField(max_length=150, blank=True) 
    content = CKEditor5Field('Content', config_name='blog')
    excerpt = models.TextField(blank=True, null=True)
    featured_image = models.ImageField(upload_to='uploads/%Y/%m/%d/', null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    published_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    seo_description = models.TextField(max_length=160, null=True, blank=True)
    seo_keywords = models.CharField(max_length=255, blank=True, null=True)
    is_trashed = models.BooleanField(default=False)
    trashed_at = models.DateTimeField(null=True, blank=True)
    trashed_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='%(app_label)s_%(class)s_trashed')
    
    objects = BaseContentManager()
    all_objects = models.Manager() 

    def move_to_trash(self, user=None):
        self.is_trashed = True
        self.trashed_at = timezone.now()
        self.trashed_by = user
        self.save(update_fields=['is_trashed', 'trashed_at', 'trashed_by'])

    def restore_from_trash(self):
        self.is_trashed = False
        self.trashed_at = None
        self.trashed_by = None
        self.save(update_fields=['is_trashed', 'trashed_at', 'trashed_by'])

    def delete_permanently(self):
        super().delete()

    @property
    def author_display_name(self):
        if self.author:
            return self.author.get_full_name() or self.author.username
        return self.author_name or "Unknown Author"

    @property
    def days_in_trash(self):
        if self.is_trashed and self.trashed_at:
            return (timezone.now() - self.trashed_at).days
        return 0

    @property
    def can_auto_delete(self):
        return self.days_in_trash >= 30
    
    class Meta:
        abstract = True

class Post(BaseContent):
    category = models.ManyToManyField('Category', blank=True, related_name='posts')
    is_featured = models.BooleanField(default=False)
    
    read_time = models.PositiveIntegerField(default=0, help_text="Estimated reading time in minutes.")
    page_views = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-published_date']

    def __str__(self):
        return self.title    

class Page(BaseContent):
    is_in_menu = models.BooleanField(default=False, help_text="Show in navigation menu")
    menu_order = models.PositiveIntegerField(default=0, help_text="Order in menu (lower numbers first)")
    
    class Meta:
        ordering = ['menu_order', 'title']
        
    def __str__(self):
        return self.title

    def calculate_read_time(self):
        plain_text = strip_tags(self.content)
        word_count = len(plain_text.split())
        words_per_minute = 200  
        return math.ceil(word_count / words_per_minute)

    def save(self, *args, **kwargs):
        
        if not self.author_name and self.author:
            self.author_name = self.author.get_full_name() or self.author.username
        
        
        if not self.slug:
            self.slug = slugify(self.title)
        
        self.read_time = self.calculate_read_time()
        
        super().save(*args, **kwargs)



    def views_today(self):
        return self.views.filter(date=timezone.now().date()).aggregate(Sum('count'))['count__sum'] or 0

    def views_this_week(self):
        start_week = timezone.now().date() - timedelta(days=timezone.now().weekday())
        return self.views.filter(date__gte=start_week).aggregate(Sum('count'))['count__sum'] or 0

    def views_this_year(self):
        start_year = timezone.now().date().replace(month=1, day=1)
        return self.views.filter(date__gte=start_year).aggregate(Sum('count'))['count__sum'] or 0

    def __str__(self):
        return self.title

class Category(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(max_length=200, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.category_name
    
    @property
    def post_count(self):
        return self.posts.count()

class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    name = models.CharField(max_length=80)
    email = models.EmailField()
    website = models.URLField(blank=True, null=True)
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_on']

    def __str__(self):
        return f'Comment by {self.name} on {self.post}'

class PostView(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='views')
    date = models.DateField(auto_now_add=True)
    count = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('post', 'date')

    def __str__(self):
        return f"{self.post.title} - {self.date}: {self.count} views"


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to='uploads/%Y/%m/%d/', blank=True, null=True)
    facebook = models.URLField(max_length=255, blank=True, null=True)
    twitter = models.URLField(max_length=255, blank=True, null=True)
    linkedin = models.URLField(max_length=255, blank=True, null=True)
    instagram = models.URLField(max_length=255, blank=True, null=True)
    website = models.URLField(max_length=255, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Update User model fields to keep them in sync
        if self.first_name != self.user.first_name or self.last_name != self.user.last_name:
            User.objects.filter(pk=self.user.pk).update(
                first_name=self.first_name,
                last_name=self.last_name
            )

    def __str__(self):
        return f"{self.user.username}'s profile"
    
    @property
    def social_links(self):
        links = []
        if self.facebook:
            links.append({'url': self.facebook, 'icon': 'fab fa-facebook-f', 'name': 'Facebook', 'color': 'bg-blue-600 hover:bg-blue-700'})
        if self.twitter:
            links.append({'url': self.twitter, 'icon': 'fab fa-twitter', 'name': 'Twitter', 'color': 'bg-sky-500 hover:bg-sky-600'})
        if self.linkedin:
            links.append({'url': self.linkedin, 'icon': 'fab fa-linkedin-in', 'name': 'LinkedIn', 'color': 'bg-blue-600 hover:bg-blue-700'})
        if self.instagram:
            links.append({'url': self.instagram, 'icon': 'fab fa-instagram', 'name': 'Instagram', 'color': 'bg-pink-600 hover:bg-pink-700'})
        if self.website:
            links.append({'url': self.website, 'icon': 'fas fa-globe', 'name': 'Website', 'color': 'bg-gray-600 hover:bg-gray-700'})
        return links
    
