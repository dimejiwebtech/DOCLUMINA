from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from blog.models import Category, Post, Page
from django.utils.text import slugify
from django.utils import timezone
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm
from blog.models import UserProfile

def set_user_permissions_by_role(user, role_name):
    """
    DRY function to set user permissions based on role.
    Call this whenever a user's role changes.
    """
    if role_name == 'Administrator':
        user.is_staff = True
        user.is_superuser = True
    elif role_name == 'Author':
        user.is_staff = True
        user.is_superuser = False
    else:
        user.is_staff = False
        user.is_superuser = False
    user.save()

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'title', 'slug', 'content', 'excerpt', 
            'featured_image', 'category', 'seo_description', 
            'seo_keywords', 'published_date'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 text-xl border-0 border-b border-gray-300 focus:border-blue-500 focus:outline-none bg-transparent placeholder-gray-500',
                'placeholder': 'Add title',
                'id': 'id_title'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'text-sm px-2 py-1 border-0 border-b border-dashed border-gray-300 focus:border-blue-500 focus:outline-none bg-transparent',
                'id': 'id_slug'
            }),
            'content': CKEditor5Widget(
                config_name='blog',
                attrs={'class': 'django_ckeditor_5'}
            ),
            'excerpt': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Write an excerpt (optional)',
                'id': 'id_excerpt'
            }),
            'seo_description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'SEO meta description',
                'maxlength': '160',
                'id': 'id_seo_description'
            }),
            'seo_keywords': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'SEO keywords (comma separated)',
                'id': 'id_seo_keywords'
            }),
            'published_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm',
                'type': 'datetime-local',
                'id': 'id_published_date'
            }),
            'featured_image': forms.FileInput(attrs={
                'accept': 'image/*',
                'id': 'id_featured_image',
                'style': 'display: none;'
            }),
            'featured_image_id': forms.HiddenInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make fields optional
        self.fields['slug'].required = False
        self.fields['published_date'].required = False
        self.fields['featured_image'].required = False  # ADD this line

            # ADD this field definition:
        self.fields['featured_image_id'] = forms.CharField(required=False, widget=forms.HiddenInput())
    
    # Set initial datetime value for new posts
        if not self.instance.pk and 'published_date' not in self.initial:
            self.initial['published_date'] = timezone.now().strftime('%Y-%m-%dT%H:%M')
        
        # Set initial datetime value for new posts
        if not self.instance.pk and 'published_date' not in self.initial:
            self.initial['published_date'] = timezone.now().strftime('%Y-%m-%dT%H:%M')

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        title = self.cleaned_data.get('title')
        
        if not slug and title:
            slug = slugify(title)
        
        if slug:
            queryset = Post.objects.filter(slug=slug)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                counter = 1
                original_slug = slug
                while Post.objects.filter(slug=slug).exclude(pk=self.instance.pk if self.instance.pk else 0).exists():
                    slug = f"{original_slug}-{counter}"
                    counter += 1
        
        return slug

    def clean_seo_description(self):
        seo_description = self.cleaned_data.get('seo_description', '')
        if len(seo_description) > 160:
            raise forms.ValidationError('Meta description should not exceed 160 characters.')
        return seo_description


class PageForm(forms.ModelForm):
    class Meta:
        model = Page
        fields = [
            'title', 'slug', 'content', 'excerpt', 
            'featured_image', 'seo_description', 
            'seo_keywords', 'published_date', 
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 text-xl border-0 border-b border-gray-300 focus:border-blue-500 focus:outline-none bg-transparent placeholder-gray-500',
                'placeholder': 'Add page title',
                'id': 'id_title'  # CHANGED: from 'id_page_title' to 'id_title'
            }),
            'slug': forms.TextInput(attrs={
                'class': 'text-sm px-2 py-1 border-0 border-b border-dashed border-gray-300 focus:border-blue-500 focus:outline-none bg-transparent',
                'id': 'id_slug'  # CHANGED: from 'id_page_slug' to 'id_slug'
            }),
            'content': CKEditor5Widget(
                config_name='blog',
                attrs={'class': 'django_ckeditor_5'}
            ),
            'excerpt': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'Write an excerpt (optional)',
                'id': 'id_excerpt'  # CHANGED: from 'id_page_excerpt' to 'id_excerpt'
            }),
            'seo_description': forms.Textarea(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'rows': 3,
                'placeholder': 'SEO meta description',
                'maxlength': '160',
                'id': 'id_seo_description'  # CHANGED: from 'id_page_seo_description' to 'id_seo_description'
            }),
            'seo_keywords': forms.TextInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'SEO keywords (comma separated)',
                'id': 'id_seo_keywords'  # CHANGED: from 'id_page_seo_keywords' to 'id_seo_keywords'
            }),
            'published_date': forms.DateTimeInput(attrs={
                'class': 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm',
                'type': 'datetime-local',
                'id': 'id_published_date'  # CHANGED: from 'id_page_published_date' to 'id_published_date'
            }),
            'featured_image': forms.FileInput(attrs={
                'accept': 'image/*',
                'id': 'id_featured_image',  # CHANGED: from 'id_page_featured_image' to 'id_featured_image'
                'style': 'display: none;'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make fields optional
        self.fields['slug'].required = False
        self.fields['published_date'].required = False
        self.fields['featured_image'].required = False
        
        # Add featured_image_id field
        self.fields['featured_image_id'] = forms.CharField(required=False, widget=forms.HiddenInput())
    
        # Set initial datetime value for new pages
        if not self.instance.pk and 'published_date' not in self.initial:
            self.initial['published_date'] = timezone.now().strftime('%Y-%m-%dT%H:%M')

    def clean_slug(self):
        slug = self.cleaned_data.get('slug')
        title = self.cleaned_data.get('title')
        
        if not slug and title:
            slug = slugify(title)
        
        if slug:
            queryset = Page.objects.filter(slug=slug)
            if self.instance.pk:
                queryset = queryset.exclude(pk=self.instance.pk)
            
            if queryset.exists():
                counter = 1
                original_slug = slug
                while Page.objects.filter(slug=slug).exclude(pk=self.instance.pk if self.instance.pk else 0).exists():
                    slug = f"{original_slug}-{counter}"
                    counter += 1
        
        return slug

    def clean_seo_description(self):
        seo_description = self.cleaned_data.get('seo_description', '')
        if len(seo_description) > 160:
            raise forms.ValidationError('Meta description should not exceed 160 characters.')
        return seo_description


# Base widget class for DRY styling
class StyledWidget:
    BASE_CLASSES = 'w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'


class UserCreateForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': StyledWidget.BASE_CLASSES}))
    first_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': StyledWidget.BASE_CLASSES}))
    last_name = forms.CharField(max_length=150, required=False, widget=forms.TextInput(attrs={'class': StyledWidget.BASE_CLASSES}))
    bio = forms.CharField(widget=forms.Textarea(attrs={'class': StyledWidget.BASE_CLASSES, 'rows': 4}), required=False)
    website = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': StyledWidget.BASE_CLASSES}))
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': StyledWidget.BASE_CLASSES})
    )
    profile_image = forms.ImageField(required=False, widget=forms.FileInput(attrs={'class': StyledWidget.BASE_CLASSES}))
    facebook = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': StyledWidget.BASE_CLASSES}))
    twitter = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': StyledWidget.BASE_CLASSES}))
    linkedin = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': StyledWidget.BASE_CLASSES}))
    instagram = forms.URLField(required=False, widget=forms.URLInput(attrs={'class': StyledWidget.BASE_CLASSES}))

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': StyledWidget.BASE_CLASSES}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': StyledWidget.BASE_CLASSES})
        self.fields['password2'].widget.attrs.update({'class': StyledWidget.BASE_CLASSES})

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            
            # Add user to selected group and set admin permissions
            role = self.cleaned_data.get('role')
            if role:
                user.groups.add(role)
                set_user_permissions_by_role(user, role.name)  
            
            # Create UserProfile (keep existing code)
            profile, created = UserProfile.objects.get_or_create(user=user)
            profile.first_name = self.cleaned_data['first_name']
            profile.last_name = self.cleaned_data['last_name']
            profile.bio = self.cleaned_data['bio']
            profile.website = self.cleaned_data['website']
            profile.facebook = self.cleaned_data['facebook']
            profile.twitter = self.cleaned_data['twitter']
            profile.linkedin = self.cleaned_data['linkedin']
            profile.instagram = self.cleaned_data['instagram']
            if self.cleaned_data['profile_image']:
                profile.profile_image = self.cleaned_data['profile_image']
            profile.save()
            
        return user


class UserEditForm(forms.ModelForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': StyledWidget.BASE_CLASSES}))
    role = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': StyledWidget.BASE_CLASSES})
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name')
        widgets = {
            'username': forms.TextInput(attrs={'class': StyledWidget.BASE_CLASSES}),
            'first_name': forms.TextInput(attrs={'class': StyledWidget.BASE_CLASSES}),
            'last_name': forms.TextInput(attrs={'class': StyledWidget.BASE_CLASSES}),
        }

    def __init__(self, *args, **kwargs):
        show_role = kwargs.pop('show_role', False)
        super().__init__(*args, **kwargs)
        
        if not show_role:
            # Remove role field if not needed
            del self.fields['role']
        elif self.instance.pk:
            # Set current role for existing users
            user_group = self.instance.groups.first()
            if user_group:
                self.fields['role'].initial = user_group



class UserProfileEditForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=30, 
        required=False,
        widget=forms.TextInput(attrs={'class': StyledWidget.BASE_CLASSES})
    )
    last_name = forms.CharField(
        max_length=30, 
        required=False,
        widget=forms.TextInput(attrs={'class': StyledWidget.BASE_CLASSES})
    )

    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name', 'bio', 'profile_image', 'website', 
                 'facebook', 'twitter', 'linkedin', 'instagram')
        widgets = {
            'bio': forms.Textarea(attrs={'class': StyledWidget.BASE_CLASSES, 'rows': 4}),
            'profile_image': forms.FileInput(attrs={'class': StyledWidget.BASE_CLASSES}),
            'website': forms.URLInput(attrs={'class': StyledWidget.BASE_CLASSES}),
            'facebook': forms.URLInput(attrs={'class': StyledWidget.BASE_CLASSES}),
            'twitter': forms.URLInput(attrs={'class': StyledWidget.BASE_CLASSES}),
            'linkedin': forms.URLInput(attrs={'class': StyledWidget.BASE_CLASSES}),
            'instagram': forms.URLInput(attrs={'class': StyledWidget.BASE_CLASSES}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-populate first_name and last_name from the User model
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
            # Update User model with first_name and last_name
            User.objects.filter(pk=profile.user.pk).update(
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name']
            )
        return profile


class BulkActionForm(forms.Form):
    action = forms.ChoiceField(choices=[
        ('', 'Bulk actions'),
        ('delete', 'Delete'),
        ('change_role_administrator', 'Change role to Administrator'),
        ('change_role_author', 'Change role to Author'),
    ], widget=forms.Select(attrs={'class': 'px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent'}))
    selected_users = forms.CharField(widget=forms.HiddenInput())