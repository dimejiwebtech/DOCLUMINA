from datetime import timedelta, timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseBadRequest, JsonResponse
from django.conf import settings
import requests

from google_sitekit.services.analytics import AnalyticsService
from google_sitekit.services.auth import GoogleAuthService
from google_sitekit.services.pagespeed import PageSpeedService
from google_sitekit.services.search_console import SearchConsoleService

from .models import SiteKitSettings
from .forms import SiteKitConnectionForm, DisconnectForm


def get_sitekit_settings(user):
    """Get or create SiteKit settings for user"""
    settings_obj, created = SiteKitSettings.objects.get_or_create(user=user)
    return settings_obj

# ---- small helpers (DRY) -----------------------------------------------------

def _date_range(days=28):
    """Return (start_date, end_date) as YYYY-MM-DD strings."""
    end = timezone.now().date()
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()

def _safe_call(fn, default=None, err_msg=None):
    """
    Execute a callable and catch exceptions, returning a default.
    Optionally add a message for the user.
    """
    try:
        return fn()
    except Exception as e:
        if err_msg:
            messages.warning(err_msg)
        # In a real app you might log e with Sentry or logger
        return default

# ---- views -------------------------------------------------------------------

@login_required
def dashboard(request):
    """Main Site Kit dashboard."""
    settings_obj = get_sitekit_settings(request.user)
    context = {
        'sitekit_settings': settings_obj,
        'is_connected': settings_obj.is_connected,
        'needs_setup': not settings_obj.is_connected,
    }

    if not settings_obj.is_connected:
        # Nothing else to do; template will invite to connect.
        return render(request, 'google_sitekit/dashboard.html', context)

    # Date range for reports (28 days)
    start_date, end_date = _date_range(28)

    # Services — use DRY auth (auto refresh under the hood)
    ga = AnalyticsService(settings_obj)
    sc = SearchConsoleService(settings_obj)
    psi = PageSpeedService()  # API key optional via settings.GOOGLE_PAGESPEED_API_KEY

    # Pull data safely (each call isolated to avoid blocking the entire view on one failure)
    analytics_overview = _safe_call(
        lambda: ga.get_overview_data(start_date, end_date),
        default={'sessions': 0, 'users': 0, 'pageviews': 0, 'avg_session_duration': 0.0, 'bounce_rate': 0.0},
        err_msg="Could not load Analytics overview (check GA4 Property ID and permissions)."
    )
    realtime = _safe_call(
        lambda: ga.get_realtime_data(),
        default={'active_users': 0},
        err_msg="Realtime users unavailable right now."
    )
    top_pages = _safe_call(
        lambda: ga.get_top_pages(start_date, end_date, limit=10),
        default=[],
        err_msg="Could not load top pages from Analytics."
    )
    traffic_sources = _safe_call(
        lambda: ga.get_traffic_sources(start_date, end_date, limit=8),
        default=[],
        err_msg="Traffic sources unavailable."
    )
    traffic_series = _safe_call(
        lambda: ga.get_time_series(start_date, end_date, metric='sessions'),
        default={'labels': [], 'values': []},
        err_msg=None
    )
    sc_totals = _safe_call(
        lambda: sc.get_search_analytics(start_date, end_date),
        default={'clicks': 0, 'impressions': 0, 'ctr': 0.0, 'position': 0.0},
        err_msg="Could not load Search Console totals (check verified site URL and scope)."
    )
    sc_queries = _safe_call(
        lambda: sc.get_top_queries(start_date, end_date, limit=10),
        default=[],
        err_msg="Top queries unavailable."
    )
    sc_pages = _safe_call(
        lambda: sc.get_top_pages(start_date, end_date, limit=10),
        default=[],
        err_msg="Top pages (Search) unavailable."
    )

    # PageSpeed: analyse homepage (or the configured Search Console URL)
    # You can change this to any URL the user sets in Settings.
    target_url = settings_obj.search_console_site_url or request.build_absolute_uri("/")
    pagespeed_mobile = _safe_call(
        lambda: psi.analyze_url(target_url, strategy='mobile'),
        default=None,
        err_msg="PageSpeed (mobile) failed to load."
    )

    context.update({
        'analytics_overview': analytics_overview,
        'traffic_series':traffic_series,
        'realtime_users': realtime.get('active_users', 0),
        'top_pages': top_pages,
        'traffic_sources': traffic_sources,
        'sc_totals': sc_totals,
        'sc_queries': sc_queries,
        'sc_pages': sc_pages,
        'pagespeed_mobile': pagespeed_mobile,
        'report_start': start_date,
        'report_end': end_date,
        'target_url': target_url,
    })
    return render(request, 'google_sitekit/dashboard.html', context)



def connect(request):
    """Initial connection setup"""
    settings_obj = get_sitekit_settings(request.user)
    
    if request.method == 'POST':
        form = SiteKitConnectionForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings saved! Now connect to Google.')
            return redirect('google_sitekit:oauth_authorize')
    else:
        form = SiteKitConnectionForm(instance=settings_obj)
    
    return render(request, 'google_sitekit/connect.html', {'form': form})



def oauth_authorize(request):
    """Redirect the user to Google's OAuth consent screen."""
    auth = GoogleAuthService()
    return redirect(auth.get_authorization_url(request))



def oauth_callback(request):
    """Handle OAuth callback from Google."""
    error = request.GET.get("error")
    if error:
        messages.error(request, f"OAuth error: {error}")
        return redirect("google_sitekit:dashboard")

    code = request.GET.get("code")
    state = request.GET.get("state")
    session_state = request.session.get("gs_state")
    code_verifier = request.session.get("gs_code_verifier")

    if not code or not state or not session_state or not code_verifier or state != session_state:
        return HttpResponseBadRequest("Invalid OAuth state")

    from requests import HTTPError
    auth = GoogleAuthService()
    try:
        tokens = auth.exchange_code_for_tokens(code, code_verifier)
    except HTTPError as e:
        detail = e.response.text if getattr(e, "response", None) is not None else str(e)
        messages.error(request, f"Token exchange failed: {detail}")
        return redirect("google_sitekit:dashboard")

    # Clear one-time session values
    request.session.pop("gs_state", None)
    request.session.pop("gs_code_verifier", None)

    # Persist
    settings_obj = get_sitekit_settings(request.user)
    settings_obj.google_access_token = tokens.access_token
    if tokens.refresh_token:
        settings_obj.google_refresh_token = tokens.refresh_token
    settings_obj.token_expires_at = GoogleAuthService.compute_expiry_ts(tokens.expires_in)
    settings_obj.is_connected = True
    settings_obj.save()

    messages.success(request, "Google account connected successfully.")
    return redirect("google_sitekit:dashboard")


def api_realtime(request):
    """Lightweight endpoint to fetch realtime users (for periodic refresh on the dashboard)."""
    settings_obj = get_sitekit_settings(request.user)
    if not settings_obj.is_connected:
        return JsonResponse({'active_users': 0, 'error': 'not_connected'}, status=400)

    try:
        ga = AnalyticsService(settings_obj)
        data = ga.get_realtime_data()
    except Exception:
        return JsonResponse({'active_users': 0, 'error': 'fetch_failed'}, status=500)

    return JsonResponse({'active_users': data.get('active_users', 0)})



def disconnect(request):
    """Disconnect Google services"""
    settings_obj = get_sitekit_settings(request.user)
    
    if request.method == 'POST':
        form = DisconnectForm(request.POST)
        if form.is_valid():
            # Clear OAuth tokens and connection status
            settings_obj.google_access_token = ''
            settings_obj.google_refresh_token = ''
            settings_obj.token_expires_at = None
            settings_obj.is_connected = False
            settings_obj.save()
            
            # Clear cached data
            request.user.analytics_data.all().delete()
            request.user.search_data.all().delete()
            request.user.top_queries.all().delete()
            request.user.top_pages.all().delete()
            request.user.pagespeed_data.all().delete()
            
            messages.success(request, 'Successfully disconnected from Google Site Kit')
            return redirect('google_sitekit:dashboard')
    else:
        form = DisconnectForm()
    
    return render(request, 'google_sitekit/disconnect.html', {
        'form': form,
        'sitekit_settings': settings_obj
    })



def settings_view(request):
    """Site Kit settings management"""
    settings_obj = get_sitekit_settings(request.user)
    
    if request.method == 'POST':
        form = SiteKitConnectionForm(request.POST, instance=settings_obj)
        if form.is_valid():
            form.save()
            messages.success(request, 'Settings updated successfully')
            return redirect('google_sitekit:settings')
    else:
        form = SiteKitConnectionForm(instance=settings_obj)
    
    return render(request, 'google_sitekit/settings.html', {
        'form': form,
        'sitekit_settings': settings_obj
    })


# API Views for AJAX calls


def api_sync(request):
    """Sync data from Google APIs"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=405)
    
    settings_obj = get_sitekit_settings(request.user)
    
    if not settings_obj.is_connected:
        return JsonResponse({'error': 'Not connected to Google'}, status=400)
    
    # Sync implementation will be in Phase 2
    return JsonResponse({
        'status': 'success',
        'message': 'Sync will be implemented in Phase 2'
    })



def api_status(request):
    """Get connection status"""
    settings_obj = get_sitekit_settings(request.user)
    
    return JsonResponse({
        'is_connected': settings_obj.is_connected,
        'is_token_expired': settings_obj.is_token_expired,
        'auto_sync': settings_obj.auto_sync,
        'last_updated': settings_obj.updated_at.isoformat() if settings_obj.updated_at else None,
    })
