from celery import shared_task
from .services.analytics import AnalyticsService
from .services.search_console import SearchConsoleService
from .services.pagespeed import PageSpeedService

@shared_task
def sync_sitekit_data():
    ga = AnalyticsService()
    sc = SearchConsoleService()
    ps = PageSpeedService()

    # Example: fetch and store data (implement your own save logic)
    analytics_data = ga.get_kpis()
    search_console_data = sc.get_top_queries()
    pagespeed_data = ps.get_performance('https://example.com')

    print("Synced SiteKit Data")
