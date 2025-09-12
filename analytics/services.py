# analytics/services.py
from django.db.models import Count
from .models import PageView, AnalyticsManager


class AnalyticsService:
    """Single service to handle all analytics data"""
    
    
    @staticmethod
    def get_dashboard_data(period='today'):
        """Get all dashboard data in one call"""
        page_views = PageView.objects.all()
        chart_data_result = AnalyticsService.get_chart_data(period)
        
        return {
            'total_views': AnalyticsManager.get_views_by_period(page_views, period),
            'traffic_sources': list(AnalyticsManager.get_traffic_sources(page_views, period)),
            'top_pages': AnalyticsService.get_top_pages(period),
            'chart_data': [item['value'] for item in chart_data_result],
            'labels': [item['label'] for item in chart_data_result],  
        }
    
    @staticmethod
    def get_top_pages(period='today', limit=10):
        """Get top performing pages"""
        page_views = PageView.objects.all()
        
        # Apply period filter
        filtered_views = AnalyticsService._filter_by_period(page_views, period)
        
        return list(
            filtered_views
            .values('page_url', 'page_title')
            .annotate(views=Count('id'))
            .order_by('-views')[:limit]
        )
    
    @staticmethod
    def get_blog_analytics(period='today'):
        """Get blog-specific analytics"""
        blog_views = PageView.objects.filter(page_url__startswith='/blog/')
        
        return {
            'total_blog_views': AnalyticsManager.get_views_by_period(blog_views, period),
            'blog_traffic_sources': list(AnalyticsManager.get_traffic_sources(blog_views, period)),
            'top_blog_posts': list(AnalyticsService._filter_by_period(blog_views, period)
            .values('page_url', 'page_title')
            .annotate(views=Count('id'))
            .order_by('-views')[:5])
        }
    
    @staticmethod
    def _filter_by_period(queryset, period):
        """Helper to filter queryset by period"""
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        
        if period == 'today':
            return queryset.filter(date=today)
        elif period == 'week':
            start_week = today - timedelta(days=today.weekday())
            return queryset.filter(date__gte=start_week)
        elif period == 'month':
            start_month = today.replace(day=1)
            return queryset.filter(date__gte=start_month)
        elif period == 'year':
            start_year = today.replace(month=1, day=1)
            return queryset.filter(date__gte=start_year)
        
        return queryset
    
    @staticmethod
    def get_chart_data(period='week'):
        """Get chart data for visualization"""
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Count
        
        today = timezone.now().date()
        
        if period == 'today':
        # Daily data for past 7 days
            data = []
            for i in range(7):
                date = today - timedelta(days=6-i)
                count = PageView.objects.filter(date=date).count()
                data.append({'label': date.strftime('%b %d'), 'value': count})
        elif period == 'week':
            # Weekly data for past 4 weeks
            data = []
            for i in range(4):
                week_start = today - timedelta(days=today.weekday() + (3-i)*7)
                week_end = week_start + timedelta(days=6)
                count = PageView.objects.filter(date__range=[week_start, week_end]).count()
                data.append({'label': f'Week {week_start.strftime("%b %d")}', 'value': count})
        elif period == 'month':
            # Weekly data for past 4 weeks
            data = []
            for i in range(4):
                week_start = today - timedelta(days=today.weekday() + (3-i)*7)
                week_end = week_start + timedelta(days=6)
                count = PageView.objects.filter(date__range=[week_start, week_end]).count()
                data.append({'label': f'Week {i+1}', 'value': count})
        else:  # year
            # Monthly data for past 12 months
            data = []
            for i in range(12):
                month_date = (today.replace(day=1) - timedelta(days=32*i)).replace(day=1)
                count = PageView.objects.filter(
                    date__year=month_date.year, 
                    date__month=month_date.month
                ).count()
                data.append({'label': month_date.strftime('%b'), 'value': count})
            data.reverse()
        
        return data
    
    @staticmethod
    def get_location_data(location_type, period='week'):
        """Get location analytics data dynamically"""
        page_views = PageView.objects.all()
        
        # Apply period filter
        filtered_views = AnalyticsService._filter_by_period(page_views, period)
        
        if location_type == 'countries':
            # Group by country and count views
            location_data = list(
                filtered_views
                .exclude(country__isnull=True)
                .exclude(country='')
                .values('country')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            )
            # Format for frontend
            return [{'name': item['country'], 'count': item['count']} for item in location_data]
        
        else:  # regions/cities
            # Group by city/region and count views
            location_data = list(
                filtered_views
                .exclude(city__isnull=True)
                .exclude(city='')
                .values('city', 'region')
                .annotate(count=Count('id'))
                .order_by('-count')[:10]
            )
            # Format for frontend - show city, region format
            return [
                {
                    'name': f"{item['city']}, {item['region']}" if item['region'] else item['city'],
                    'count': item['count']
                } 
                for item in location_data
            ]