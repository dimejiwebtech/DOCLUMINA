from django.contrib import admin
from .models import (
    SiteKitSettings, AnalyticsData, SearchConsoleData, 
    TopQuery, TopPage, PageSpeedData
)


@admin.register(SiteKitSettings)
class SiteKitSettingsAdmin(admin.ModelAdmin):
    list_display = ['user', 'is_connected', 'analytics_property_id', 'auto_sync', 'updated_at']
    list_filter = ['is_connected', 'auto_sync', 'created_at']
    search_fields = ['user__username', 'user__email']
    readonly_fields = ['google_access_token', 'google_refresh_token', 'token_expires_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Connection Status', {
            'fields': ('is_connected', 'token_expires_at')
        }),
        ('Service Configuration', {
            'fields': ('analytics_property_id', 'search_console_site_url', 'auto_sync')
        }),
        ('OAuth Tokens', {
            'fields': ('google_access_token', 'google_refresh_token'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AnalyticsData)
class AnalyticsDataAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'sessions', 'users', 'pageviews', 'bounce_rate']
    list_filter = ['date', 'created_at']
    search_fields = ['user__username']
    date_hierarchy = 'date'
    ordering = ['-date', '-sessions']


@admin.register(SearchConsoleData) 
class SearchConsoleDataAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'clicks', 'impressions', 'ctr', 'position']
    list_filter = ['date', 'created_at']
    search_fields = ['user__username']
    date_hierarchy = 'date'
    ordering = ['-date', '-clicks']


@admin.register(TopQuery)
class TopQueryAdmin(admin.ModelAdmin):
    list_display = ['query', 'user', 'date', 'clicks', 'impressions', 'ctr']
    list_filter = ['date', 'created_at']
    search_fields = ['query', 'user__username']
    ordering = ['-clicks']


@admin.register(TopPage)
class TopPageAdmin(admin.ModelAdmin):
    list_display = ['page_url', 'user', 'date', 'pageviews', 'clicks']
    list_filter = ['date', 'created_at']
    search_fields = ['page_url', 'user__username']
    ordering = ['-pageviews']


@admin.register(PageSpeedData)
class PageSpeedDataAdmin(admin.ModelAdmin):
    list_display = ['url', 'user', 'device', 'performance_score', 'tested_at']
    list_filter = ['device', 'performance_score', 'tested_at']
    search_fields = ['url', 'user__username']
    ordering = ['-tested_at']
