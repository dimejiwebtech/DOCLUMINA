from django import forms
from django.contrib.auth import get_user_model
from .models import SiteKitSettings

User = get_user_model()


class SiteKitConnectionForm(forms.ModelForm):
    """Form for connecting Google services"""
    
    class Meta:
        model = SiteKitSettings
        fields = ['analytics_property_id', 'search_console_site_url', 'auto_sync']
        widgets = {
            'analytics_property_id': forms.TextInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'e.g., 123456789'
            }),
            'search_console_site_url': forms.URLInput(attrs={
                'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'placeholder': 'https://yoursite.com'
            }),
            'auto_sync': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300 text-indigo-600 shadow-sm focus:border-indigo-500 focus:ring-indigo-500'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['analytics_property_id'].help_text = "Your GA4 Property ID (found in Google Analytics)"
        self.fields['search_console_site_url'].help_text = "The site URL registered in Google Search Console"
        self.fields['auto_sync'].help_text = "Automatically sync data every 6 hours"


class DisconnectForm(forms.Form):
    """Simple form to confirm disconnection"""
    confirm = forms.BooleanField(
        required=True,
        label="I confirm that I want to disconnect Google Site Kit",
        widget=forms.CheckboxInput(attrs={
            'class': 'rounded border-gray-300 text-red-600 shadow-sm focus:border-red-500 focus:ring-red-500'
        })
    )