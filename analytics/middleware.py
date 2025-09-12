# analytics/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.urls import resolve
from .models import PageView
from .utils import TrafficSourceDetector, TRACKED_PAGES

class AnalyticsMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Only track GET requests with 200 status
        if request.method != 'GET' or response.status_code != 200:
            return response
        
        # Skip admin, static files, and API endpoints
        if any(skip in request.path for skip in ['/admin/', '/static/', '/media/', '/api/']):
            return response
        
        try:
            self.track_page_view(request)
        except Exception:
            # Fail silently to avoid breaking the app
            pass
        
        return response
    
    def track_page_view(self, request):
        referrer = request.META.get('HTTP_REFERER', '')
        traffic_source = TrafficSourceDetector.detect_source(referrer)
        
        # Get page title
        page_title = TRACKED_PAGES.get(request.path, '')
        
        # Handle blog posts dynamically
        if request.path.startswith('/blog/') and not page_title:
            try:
                resolved = resolve(request.path)
                if hasattr(resolved, 'kwargs') and 'slug' in resolved.kwargs:
                    page_title = f"Blog: {resolved.kwargs['slug'].replace('-', ' ').title()}"
                else:
                    page_title = 'Blog Post'
            except:
                page_title = 'Blog'
        
        # Skip if page not in tracking list and not a blog post
        if not page_title:
            return
        
        PageView.objects.create(
            page_url=request.path,
            page_title=page_title,
            traffic_source=traffic_source,
            referrer=referrer if referrer else None,
            ip_address=self.get_client_ip(request),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500]
        )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '127.0.0.1')