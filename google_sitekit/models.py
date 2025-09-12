from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from google_sitekit.managers import AnalyticsDataManager, SearchConsoleDataManager


User = get_user_model()


class SiteKitSettings(models.Model):
    """Store user's Google API credentials and Site Kit configuration"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='sitekit_settings')
    
    # OAuth tokens
    google_access_token = models.TextField(blank=True, help_text="Google OAuth access token")
    google_refresh_token = models.TextField(blank=True, help_text="Google OAuth refresh token")
    token_expires_at = models.DateTimeField(null=True, blank=True)
    
    # Service configurations
    analytics_property_id = models.CharField(max_length=50, blank=True, help_text="GA4 Property ID")
    search_console_site_url = models.URLField(blank=True, help_text="Search Console site URL")
    
    # Settings
    is_connected = models.BooleanField(default=False)
    auto_sync = models.BooleanField(default=True, help_text="Automatically sync data")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Site Kit Settings"
        verbose_name_plural = "Site Kit Settings"

    def __str__(self):
        return f"{self.user.username}'s Site Kit Settings"
    
    @property
    def is_token_expired(self):
        """Check if access token has expired"""
        if not self.token_expires_at:
            return True
        return timezone.now() >= self.token_expires_at
    
    def get_dashboard_url(self):
        """Get dashboard URL for this user"""
        return reverse('google_sitekit:dashboard')


class BaseMetricsModel(models.Model):
    """Base model for storing cached metrics data"""
    date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-date']


class AnalyticsData(BaseMetricsModel):
    """Store cached Google Analytics data"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='analytics_data')
    
    # Core metrics
    sessions = models.IntegerField(default=0)
    users = models.IntegerField(default=0)
    new_users = models.IntegerField(default=0)
    pageviews = models.IntegerField(default=0)
    pages_per_session = models.FloatField(default=0.0)
    avg_session_duration = models.FloatField(default=0.0, help_text="In seconds")
    bounce_rate = models.FloatField(default=0.0, help_text="Percentage")

    objects = AnalyticsDataManager()

    class Meta:
        verbose_name = "Analytics Data"
        verbose_name_plural = "Analytics Data"
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.sessions} sessions"


class SearchConsoleData(BaseMetricsModel):
    """Store cached Search Console data"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='search_data')
    
    # Search metrics
    clicks = models.IntegerField(default=0)
    impressions = models.IntegerField(default=0)
    ctr = models.FloatField(default=0.0, help_text="Click-through rate percentage")
    position = models.FloatField(default=0.0, help_text="Average position in search results")

    objects = SearchConsoleDataManager()

    class Meta:
        verbose_name = "Search Console Data"
        verbose_name_plural = "Search Console Data"
        unique_together = ['user', 'date']
        indexes = [
            models.Index(fields=['user', 'date']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.clicks} clicks"


class TopQuery(models.Model):
    """Store top performing search queries"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='top_queries')
    date = models.DateField()
    query = models.CharField(max_length=200)
    clicks = models.IntegerField(default=0)
    impressions = models.IntegerField(default=0)
    ctr = models.FloatField(default=0.0)
    position = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Top Query"
        verbose_name_plural = "Top Queries"
        unique_together = ['user', 'date', 'query']
        ordering = ['-clicks']

    def __str__(self):
        return f"{self.query} - {self.clicks} clicks"


class TopPage(models.Model):
    """Store top performing pages"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='top_pages')
    date = models.DateField()
    page_url = models.URLField()
    
    # Analytics data
    pageviews = models.IntegerField(default=0)
    unique_pageviews = models.IntegerField(default=0)
    avg_time_on_page = models.FloatField(default=0.0)
    
    # Search Console data
    clicks = models.IntegerField(default=0)
    impressions = models.IntegerField(default=0)
    ctr = models.FloatField(default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Top Page"
        verbose_name_plural = "Top Pages"
        unique_together = ['user', 'date', 'page_url']
        ordering = ['-pageviews']

    def __str__(self):
        return f"{self.page_url} - {self.pageviews} views"


class PageSpeedData(models.Model):
    """Store PageSpeed Insights data"""
    DEVICE_CHOICES = [
        ('mobile', 'Mobile'),
        ('desktop', 'Desktop'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pagespeed_data')
    url = models.URLField()
    device = models.CharField(max_length=10, choices=DEVICE_CHOICES, default='mobile')
    
    # Core Web Vitals
    performance_score = models.IntegerField(null=True, blank=True, help_text="0-100 score")
    accessibility_score = models.IntegerField(null=True, blank=True)
    best_practices_score = models.IntegerField(null=True, blank=True)
    seo_score = models.IntegerField(null=True, blank=True)
    
    # Detailed metrics
    first_contentful_paint = models.FloatField(null=True, blank=True, help_text="In seconds")
    largest_contentful_paint = models.FloatField(null=True, blank=True)
    first_input_delay = models.FloatField(null=True, blank=True)
    cumulative_layout_shift = models.FloatField(null=True, blank=True)
    
    tested_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "PageSpeed Data"
        verbose_name_plural = "PageSpeed Data"
        ordering = ['-tested_at']

    def __str__(self):
        return f"{self.url} ({self.device}) - Score: {self.performance_score}"
    
    @property
    def performance_status(self):
        """Get performance status based on score"""
        if not self.performance_score:
            return 'unknown'
        if self.performance_score >= 90:
            return 'good'
        elif self.performance_score >= 50:
            return 'needs-improvement'
        return 'poor'