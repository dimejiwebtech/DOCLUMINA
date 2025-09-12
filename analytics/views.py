# analytics/views.py
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_GET
from django.shortcuts import render
from .services import AnalyticsService

@login_required
@require_GET
def dashboard_data(request):
    """Main analytics endpoint for dashboard widget"""
    period = request.GET.get('period', 'week')
    
    if period not in ['today', 'week', 'month', 'year']:
        period = 'week'
    
    data = AnalyticsService.get_dashboard_data(period)
    return JsonResponse(data)

@login_required
def traffic_stats(request):
    """Traffic stats page"""
    return render(request, 'analytics/traffic_stats.html')

@login_required 
@require_GET
def traffic_data(request):
    """Detailed traffic analytics for stats page"""
    period = request.GET.get('period', 'week')
    
    if period not in ['today', 'week', 'month', 'year']:
        period = 'week'
    
    dashboard_data = AnalyticsService.get_dashboard_data(period)
    blog_data = AnalyticsService.get_blog_analytics(period)
    chart_data = AnalyticsService.get_chart_data(period)
    
    return JsonResponse({
        **dashboard_data,
        'blog_analytics': blog_data,
        'chart_data': chart_data
    })

@login_required
@require_GET
def location_data(request):
    """Location analytics data"""
    location_type = request.GET.get('type', 'countries')
    period = request.GET.get('period', 'week')
    
    if location_type not in ['countries', 'regions']:
        location_type = 'countries'
    
    if period not in ['today', 'week', 'month', 'year']:
        period = 'week'
    
    # Get location data from your service
    location_data = AnalyticsService.get_location_data(location_type, period)
    
    return JsonResponse({
        'locations': location_data
    })