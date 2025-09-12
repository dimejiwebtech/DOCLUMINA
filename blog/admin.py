# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect
from django.contrib import messages
from .models import Post, Category, Comment, PostView, UserProfile, Page


class ActivePostFilter(admin.SimpleListFilter):
    title = 'Post Status'
    parameter_name = 'trash_status'

    def lookups(self, request, model_admin):
        return (
            ('active', 'Active Posts'),
            ('trashed', 'Trash'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.active()
        elif self.value() == 'trashed':
            return queryset.trashed()
        return queryset


class BaseContentAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'published_date', 'trash_status', 'trash_actions')
    list_filter = ('status', 'author')
    search_fields = ('title', 'content', 'author_name')
    prepopulated_fields = {'slug': ('title',)}
    actions = ['move_to_trash', 'restore_from_trash', 'delete_permanently']
    
    date_hierarchy = 'published_date'
    ordering = ('is_trashed', '-published_date')
    
    readonly_fields = ('trashed_at', 'trashed_by', 'author_name')

    def get_queryset(self, request):
        # Show all posts including trashed ones
        return self.model.all_objects.get_queryset()

    def author_display_name(self, obj):
        return obj.author_display_name
    author_display_name.short_description = 'Author'

    def trash_status(self, obj):
        if obj.is_trashed:
            days = obj.days_in_trash
            color = "red" if obj.can_auto_delete else "orange"
            return format_html(
                '<span style="color: {};">In Trash ({} days)</span>', 
                color, days
            )
        return format_html('<span style="color: green;">Active</span>')
    trash_status.short_description = 'Trash Status'

    def trash_actions(self, obj):
        model_name = self.model._meta.model_name
        if obj.is_trashed:
            restore_url = reverse(f'admin:restore_{model_name}', args=[obj.pk])
            delete_url = reverse(f'admin:delete_{model_name}_permanently', args=[obj.pk])
            return format_html(
                '<a href="{}" class="button">Restore</a> '
                '<a href="{}" class="button" style="background-color: #ba2121;">Delete Permanently</a>',
                restore_url, delete_url
            )
        else:
            trash_url = reverse(f'admin:move_{model_name}_to_trash', args=[obj.pk])
            return format_html(
                '<a href="{}" class="button" style="background-color: #ffc107;">Move to Trash</a>',
                trash_url
            )

    def get_urls(self):
        urls = super().get_urls()
        model_name = self.model._meta.model_name
        custom_urls = [
            path(
                'move-to-trash/<int:post_id>/',
                self.admin_site.admin_view(self.move_post_to_trash),
                name=f'move_{model_name}_to_trash',
            ),
            path(
                'restore/<int:post_id>/',
                self.admin_site.admin_view(self.restore_post),
                name=f'restore_{model_name}',
            ),
            path(
                'delete-permanently/<int:post_id>/',
                self.admin_site.admin_view(self.delete_post_permanently),
                name=f'delete_{model_name}_permanently',
            ),
        ]
        return custom_urls + urls

    def move_post_to_trash(self, request, post_id):
        obj = self.model.all_objects.get(pk=post_id) 
        obj.move_to_trash(request.user)
        messages.success(request, f'{self.model._meta.verbose_name} "{obj.title}" moved to trash.')
        return redirect(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist')

    def restore_post(self, request, post_id):
        obj = self.model.all_objects.get(pk=post_id)
        obj.restore_from_trash()
        messages.success(request, f'{self.model._meta.verbose_name} "{obj.title}" restored from trash.')
        return redirect(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist')

    def delete_post_permanently(self, request, post_id):
        obj = self.model.all_objects.get(pk=post_id)
        title = obj.title
        obj.delete_permanently()
        messages.warning(request, f'{self.model._meta.verbose_name} "{title}" permanently deleted.')
        return redirect(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_changelist')

    # Admin actions
    def move_to_trash(self, request, queryset):
        count = 0
        for post in queryset:
            if not post.is_trashed:
                post.move_to_trash(request.user)
                count += 1
        messages.success(request, f'{count} posts moved to trash.')
    move_to_trash.short_description = "Move selected posts to trash"

    def restore_from_trash(self, request, queryset):
        count = 0
        for post in queryset:
            if post.is_trashed:
                post.restore_from_trash()
                count += 1
        messages.success(request, f'{count} posts restored from trash.')
    restore_from_trash.short_description = "Restore selected posts from trash"

    def delete_permanently(self, request, queryset):
        trashed_posts = queryset.filter(is_trashed=True)
        count = trashed_posts.count()
        trashed_posts.delete()
        messages.warning(request, f'{count} posts permanently deleted.')
    delete_permanently.short_description = "Permanently delete selected posts (trashed only)"

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Post)
class PostAdmin(BaseContentAdmin):
    list_filter = (ActivePostFilter, 'status', 'category', 'author')
    list_editable = ('author',)
    fieldsets = (
        ("Content", {
            'fields': ('title', 'slug', 'author', 'content', 'excerpt', 'featured_image', 'category', 'status', 'is_featured')
        }),
        ("SEO", {
            'fields': ('seo_description', 'seo_keywords'),
            'classes': ('collapse',)
        }),
        ("Analytics", {
            'fields': ('page_views',),
        }),
        ("Trash Info", {
            'fields': ('is_trashed', 'trashed_at', 'trashed_by', 'author_name'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('trashed_at', 'trashed_by', 'author_name')

@admin.register(Page)
class PageAdmin(BaseContentAdmin):
    list_display = ('title', 'author', 'status', 'published_date', 'trash_status', 'trash_actions')
    list_filter = ('status', 'author',)
    
    fieldsets = (
        ("Content", {
            'fields': ('title', 'slug', 'author', 'content', 'featured_image', 'status')
        }),
        ("SEO", {
            'fields': ('seo_description', 'seo_keywords'),
            'classes': ('collapse',)
        }),
        ("Trash Info", {
            'fields': ('is_trashed', 'trashed_at', 'trashed_by', 'author_name'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('category_name',)}


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'post', 'created_on', 'approved']
    list_filter = ['approved', 'created_on']
    search_fields = ['name', 'email', 'body']
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
    approve_comments.short_description = "Approve selected comments"


@admin.register(PostView)
class PostViewAdmin(admin.ModelAdmin):
    list_display = ('post', 'date', 'count')
    list_filter = ('date',)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'bio',)
    search_fields = ('user__username', 'user__email', 'bio')