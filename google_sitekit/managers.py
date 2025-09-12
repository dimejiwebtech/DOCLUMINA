from django.db import models
from django.utils import timezone
from datetime import timedelta


class AnalyticsDataManager(models.Manager):
    def get_date_range(self, user, days=30):
        """Get analytics data for the last N days"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        return self.filter(
            user=user,
            date__range=[start_date, end_date]
        ).order_by('date')
    
    def get_totals(self, user, days=30):
        """Get total metrics for date range"""
        queryset = self.get_date_range(user, days)
        return queryset.aggregate(
            total_sessions=models.Sum('sessions'),
            total_users=models.Sum('users'),
            total_pageviews=models.Sum('pageviews'),
            avg_bounce_rate=models.Avg('bounce_rate'),
        )


class SearchConsoleDataManager(models.Manager):
    def get_date_range(self, user, days=30):
        """Get search console data for the last N days"""
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        return self.filter(
            user=user,
            date__range=[start_date, end_date]
        ).order_by('date')
    
    def get_totals(self, user, days=30):
        """Get total metrics for date range"""
        queryset = self.get_date_range(user, days)
        return queryset.aggregate(
            total_clicks=models.Sum('clicks'),
            total_impressions=models.Sum('impressions'),
            avg_ctr=models.Avg('ctr'),
            avg_position=models.Avg('position'),
        )