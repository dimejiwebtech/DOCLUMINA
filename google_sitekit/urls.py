from django.urls import path
from . import views

app_name = 'google_sitekit'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),

    # Authentication
    path('connect/', views.connect, name='connect'),
    path('oauth/authorize/', views.oauth_authorize, name='oauth_authorize'),
    path('oauth/callback/', views.oauth_callback, name='oauth_callback'),
    path('disconnect/', views.disconnect, name='disconnect'),

    # Settings
    path('settings/', views.settings_view, name='settings'),

    # API endpoints
    path('api/sync/', views.api_sync, name='api_sync'),
    path('api/status/', views.api_status, name='api_status'),
    path('api/realtime/', views.api_realtime, name='api_realtime'),  # NEW
]
