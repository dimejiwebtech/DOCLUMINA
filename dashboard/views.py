import json
import os
from urllib import request
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from .decorators import administrator_required, author_or_admin_required
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from blog.models import UserProfile
from .forms import UserCreateForm, UserEditForm, UserProfileEditForm, BulkActionForm, set_user_permissions_by_role
import json
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.utils import timezone
from django.contrib import messages
from blog.models import Post, Category, Comment, Page
from django.utils.text import slugify
from .forms import PostForm, PageForm
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from media_manager.models import MediaFile
from django.http import JsonResponse, QueryDict
from django.urls import reverse
from main.models import MentorApplication, MentorshipApplication, Testimonial
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.db import transaction


# first option in bulk_action
def build_filtered_url(base_url, **params):
    """Build URL with query parameters, excluding empty values"""
    query_dict = QueryDict(mutable=True)
    for key, value in params.items():
        if value and value != 'all' and value != '':
            query_dict[key] = value
    
    if query_dict:
        return f"{base_url}?{query_dict.urlencode()}"
    return base_url
@login_required(login_url='login')
def dashboard(request):
    # Get counts for dashboard widgets
    posts_count = Post.objects.filter(is_trashed=False).count()
    pages_count = Page.objects.filter(is_trashed=False).count()
    comments_count = Comment.objects.filter(approved=True).count()
    pending_comments_count = Comment.objects.filter(approved=False).count()
    
    context = {
        'posts_count': posts_count,
        'pages_count': pages_count,
        'comments_count': comments_count,
        'pending_comments_count': pending_comments_count,
    }
    
    return render(request, 'dashboard/dashboard.html', context)


@login_required(login_url='login')
def posts(request):
    # Handle search and filters from GET parameters
    status_filter = request.GET.get('status', 'all')
    category_filter = request.GET.get('category', 'all')
    date_filter = request.GET.get('date', 'all')
    search_query = request.GET.get('search', '').strip()
    
    # Base queryset with comment counts
    posts_queryset = Post.objects.select_related('author').prefetch_related('category').annotate(
    comment_count=Count('comments', filter=Q(comments__approved=True))
)
    
    # Filter by trash status first
    if status_filter == 'trash':
        posts_queryset = posts_queryset.filter(is_trashed=True)
    else:
        posts_queryset = posts_queryset.filter(is_trashed=False)
    
    # Apply other filters
    if search_query:
        posts_queryset = posts_queryset.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query) |
            Q(excerpt__icontains=search_query)
        )
    
    # Status filtering
    if status_filter == 'mine':
        posts_queryset = posts_queryset.filter(author=request.user)
    elif status_filter == 'published':
        posts_queryset = posts_queryset.filter(status='published')
    elif status_filter == 'draft':
        posts_queryset = posts_queryset.filter(status='draft')
    
    # Category filtering
    if category_filter != 'all':
        try:
            posts_queryset = posts_queryset.filter(category_id=int(category_filter))
        except (ValueError, TypeError):
            pass
    
    # Date filtering
    if date_filter != 'all':
        try:
            year, month = date_filter.split('-')
            posts_queryset = posts_queryset.filter(
                published_date__year=int(year),
                published_date__month=int(month)
            )
        except (ValueError, IndexError):
            pass
    
    # Order by creation date (newest first)
    posts_queryset = posts_queryset.order_by('-created_at')
    
    # Get counts for tabs
    def get_tab_counts(user):
        base_posts = Post.objects.select_related('author')
        return {
            'all': base_posts.filter(is_trashed=False).count(),
            'mine': base_posts.filter(is_trashed=False, author=user).count(),
            'published': base_posts.filter(is_trashed=False, status='published').count(),
            'draft': base_posts.filter(is_trashed=False, status='draft').count(),
            'trash': base_posts.filter(is_trashed=True).count(),
        }

    tab_counts = get_tab_counts(request.user)

    categories = Category.objects.all().order_by('category_name')
    
    # Pagination
    paginator = Paginator(posts_queryset, 20)
    page_number = request.GET.get('page', 1)
    posts_page = paginator.get_page(page_number)
    
    
    # Generate date options (last 12 months)
    def get_date_options():
        date_options = []
        current_date = timezone.now()
        for i in range(12):
            if current_date.month - i <= 0:
                month = current_date.month - i + 12
                year = current_date.year - 1
            else:
                month = current_date.month - i
                year = current_date.year
            
            date = current_date.replace(year=year, month=month, day=1)
            date_options.append({
                'value': date.strftime('%Y-%m'),
                'label': date.strftime('%B %Y')
            })
        return date_options
    
    context = {
        'posts': posts_page,
        'categories': categories,
        # 'date_options': date_options,
        'tab_counts': tab_counts,
        'current_status': status_filter,
        'current_category': category_filter,
        'current_date': date_filter,
        'search_query': search_query,
        'total_items': paginator.count,
        'current_page': posts_page.number,
        'total_pages': paginator.num_pages,
        'has_previous': posts_page.has_previous(),
        'has_next': posts_page.has_next(),
        'previous_page': posts_page.previous_page_number() if posts_page.has_previous() else None,
        'next_page': posts_page.next_page_number() if posts_page.has_next() else None,
    }
    
    return render(request, 'dashboard/posts.html', context)

@administrator_required
@login_required(login_url='login')
def bulk_action(request):
    """Handle bulk actions for posts"""
    if request.method == 'POST':
        action = request.POST.get('action')
        post_ids = request.POST.getlist('post_ids')
        
        # Get current filter parameters to preserve state
        status_filter = request.GET.get('status', 'all')
        category_filter = request.GET.get('category', 'all')
        date_filter = request.GET.get('date', 'all')
        search_query = request.GET.get('search', '').strip()
        page = request.GET.get('page', '1')
        
        if not post_ids:
            messages.error(request, 'No posts selected.')
            return redirect(f'posts?status={status_filter}&category={category_filter}&date={date_filter}&search={search_query}&page={page}')
        
        posts_to_update = Post.objects.filter(id__in=post_ids)
        
        if action == 'trash':
            posts_to_update.update(
                is_trashed=True,
                trashed_at=timezone.now(),
                trashed_by=request.user,
                status='trashed'  
            )
            messages.success(request, f'{len(post_ids)} posts moved to trash.')
            
        elif action == 'restore':
            posts_to_update.update(
                is_trashed=False,
                trashed_at=None,
                trashed_by=None,
                status='draft' 
            )
            messages.success(request, f'{len(post_ids)} posts restored as drafts.')
            
        elif action == 'delete':
            posts_to_update.delete()
            messages.success(request, f'{len(post_ids)} posts permanently deleted.')
            
        elif action == 'publish':
            posts_to_update = posts_to_update.exclude(status='published')
            posts_to_update.update(status='published', published_date=timezone.now())
            messages.success(request, f'{len(post_ids)} posts published.')
            
        elif action == 'draft':
            posts_to_update.update(status='draft')
            messages.success(request, f'{len(post_ids)} posts moved to draft.')
        
        # Build redirect URL with preserved parameters
        redirect_url = reverse('posts') + f'?status={status_filter}&category={category_filter}&date={date_filter}&search={search_query}&page={page}'
        return redirect(redirect_url)
    
    return redirect('posts')


@administrator_required
@login_required(login_url='login')
def trash_post(request, post_id):
    """Move single post to trash"""
    post = get_object_or_404(Post, id=post_id)
    
    if request.method == 'POST':
        post.is_trashed = True
        post.trashed_at = timezone.now()
        post.trashed_by = request.user
        post.status = 'trashed'  
        post.save()
        
        messages.success(request, f'Post "{post.title}" moved to trash.')
        
    
    # Preserve current filters
    status = request.GET.get('status', 'all')
    category = request.GET.get('category', 'all')
    date = request.GET.get('date', 'all')
    search = request.GET.get('search', '')
    page = request.GET.get('page', '1')
    
    redirect_url = build_filtered_url('posts', status=status, category=category, date=date, search=search, page=page)
    return redirect(redirect_url)
    
@administrator_required
@login_required(login_url='login')
def restore_post(request, post_id):
    """Restore single post from trash"""
    post = get_object_or_404(Post, id=post_id, is_trashed=True)
    
    if request.method == 'POST':
        post.is_trashed = False
        post.trashed_at = None
        post.trashed_by = None
        post.status = 'draft'  
        post.save()
        
        messages.success(request, f'Post "{post.title}" restored as draft.')
    
    # Preserve current filters
    status = request.GET.get('status', 'all')
    category = request.GET.get('category', 'all')
    date = request.GET.get('date', 'all')
    search = request.GET.get('search', '')
    page = request.GET.get('page', '1')
    
    redirect_url = build_filtered_url('posts', status=status, category=category, date=date, search=search, page=page)
    return redirect(redirect_url)


@login_required(login_url='login')
def add_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            featured_image_id = request.POST.get('featured_image_id')
            if featured_image_id:
                try:
                    from media_manager.models import MediaFile  
                    media_obj = MediaFile.objects.get(id=featured_image_id)
                    post = form.save(commit=False)
                    post.featured_image = media_obj.file 
                except MediaFile.DoesNotExist:
                    pass
            else:
                post = form.save(commit=False)
            post.author = request.user
            
            # Handle status
            if 'save_draft' in request.POST:
                post.status = 'draft'
            elif 'publish' in request.POST:
                post.status = 'published'
                if not post.published_date:
                    post.published_date = timezone.now()
            
            # Generate slug if not provided
            if not post.slug and post.title:
                post.slug = generate_unique_slug(post.title)
            
            post.save()
            
            # Handle categories - get selected category IDs from POST data
            selected_categories = request.POST.getlist('category')
            if selected_categories:
                post.category.set(selected_categories)
            
            if post.status == 'published':
                messages.success(request, 'Post published successfully!')
            else:
                messages.success(request, 'Post saved as draft!')
                
            return redirect('edit_post', pk=post.pk)
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PostForm()
    
    all_categories = Category.objects.all()
    return render(request, 'dashboard/add_post.html', {
        'form': form,
        'all_categories': all_categories,
    })

@login_required(login_url='login')
def edit_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user owns the post or is superuser
    if post.author != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only edit your own posts.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            featured_image_id = request.POST.get('featured_image_id')
            if featured_image_id:
                try:
                    from media_manager.models import MediaFile 
                    media_obj = MediaFile.objects.get(id=featured_image_id)
                    post = form.save(commit=False)
                    post.featured_image = media_obj.file  
                except MediaFile.DoesNotExist:
                    pass
            else:
                post = form.save(commit=False)
            post = form.save(commit=False)
            
            # Handle status
            if 'save_draft' in request.POST:
                post.status = 'draft'
            elif 'publish' in request.POST:
                post.status = 'published'
                if not post.published_date:
                    post.published_date = timezone.now()
            
            # Generate slug if not provided
            if not post.slug and post.title:
                post.slug = generate_unique_slug(post.title, exclude_id=post.id)
            
            post.save()
            
            # Handle categories - get selected category IDs from POST data
            selected_categories = request.POST.getlist('category')
            post.category.set(selected_categories)
            
            if post.status == 'published':
                messages.success(request, 'Post updated and published!')
            else:
                messages.success(request, 'Post updated and saved as draft!')
                
            return redirect('edit_post', pk=post.pk)
        else:
            # Add form errors to messages
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PostForm(instance=post)
    
    all_categories = Category.objects.all()
    return render(request, 'dashboard/add_post.html', {
        'form': form,
        'post': post,
        'all_categories': all_categories,
    })

@login_required(login_url='login')
def post_form_view(request, pk=None):
    """Unified view for both add and edit post functionality"""
    post = get_object_or_404(Post, pk=pk) if pk else None
    
    # Check permissions for editing
    if post and post.author != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only edit your own posts.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            featured_image_id = request.POST.get('featured_image_id')
            if featured_image_id:
                try:
                    from media_manager.models import MediaFile  
                    media_obj = MediaFile.objects.get(id=featured_image_id)
                    post = form.save(commit=False)
                    post.featured_image = media_obj.file  
                except MediaFile.DoesNotExist:
                    pass
            else:
                post = form.save(commit=False)
            post_obj = form.save(commit=False)
            
            if not post:  # New post
                post_obj.author = request.user
            
            # Handle status and publish date
            if 'save_draft' in request.POST:
                post_obj.status = 'draft'
            elif 'publish' in request.POST:
                post_obj.status = 'published'
                if not post_obj.published_date:
                    post_obj.published_date = timezone.now()
            
            # Auto-generate slug if needed
            if not post_obj.slug and post_obj.title:
                post_obj.slug = generate_unique_slug(post_obj.title, exclude_id=post_obj.id if post else None)
            
            post_obj.save()
            
            # Handle category (multiple selection)
            selected_categories = request.POST.getlist('category')
            post_obj.save()
            if selected_categories:
                post_obj.category.set(selected_categories)
            else:
                post_obj.category.clear()
            
            success_msg = f"Post {'updated' if post else 'created'} and {'published' if post_obj.status == 'published' else 'saved as draft'}!"
            messages.success(request, success_msg)
            
            return redirect('edit_post', pk=post_obj.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = PostForm(instance=post)
    
    return render(request, 'dashboard/add_post.html', {
        'form': form,
        'post': post,
        'all_categories': Category.objects.all(),
    })

# URL patterns will use:
# add_post = post_form_view
# edit_post = post_form_view (with pk parameter)

def generate_unique_slug(title, exclude_id=None):
    """Generate a unique slug from title"""
    base_slug = slugify(title) or 'post'
    slug = base_slug
    counter = 1
    
    while True:
        queryset = Post.objects.filter(slug=slug)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        
        if not queryset.exists():
            return slug
            
        slug = f"{base_slug}-{counter}"
        counter += 1

@csrf_exempt
@login_required(login_url='login')
def auto_save_post(request):
    """Enhanced auto-save with comprehensive field support"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        post_id = data.get('post_id')
        
        saveable_fields = ['title', 'content', 'excerpt', 'seo_description', 'seo_keywords', 'slug']
        
        if post_id:
            # Update existing post
            post = get_object_or_404(Post, pk=post_id, author=request.user)
            
            # Update basic fields
            for field in saveable_fields:
                if field in data and data[field] is not None:
                    setattr(post, field, data[field])
            
            # Auto-generate slug if title changed and no custom slug
            if data.get('title') and not data.get('slug'):
                post.slug = generate_unique_slug(data['title'], exclude_id=post.id)
            elif not post.slug:  # Add this line
                post.slug = generate_unique_slug(post.title or 'untitled', exclude_id=post.id)
            
            post.status = 'draft'
            post.save()
            
            # Handle category after saving
            category_ids = data.get('category', [])
            if category_ids:
                try:
                    valid_categories = Category.objects.filter(pk__in=category_ids)
                    post.category.set(valid_categories)
                except (ValueError, TypeError):
                    pass
            else:
                post.category.clear()
            
        else:
            # Create new post
            post_data = {field: data.get(field, '') for field in saveable_fields}
            post_data.update({
                'author': request.user,
                'status': 'draft'
            })
            
            if post_data['title'] and not post_data['slug']:
                post_data['slug'] = generate_unique_slug(post_data['title'])
            elif not post_data['slug']:  
                post_data['slug'] = generate_unique_slug('untitled')  
            
            post = Post.objects.create(**post_data)
            
            # Handle category for new post
            category_id = data.get('category')
            if category_id and category_id != '':
                try:
                    category = Category.objects.get(pk=int(category_id))
                    post.category = category
                    post.save()
                except (Category.DoesNotExist, ValueError, TypeError):
                    pass
        
        return JsonResponse({
            'success': True,
            'post_id': post.pk,
            'slug': post.slug,
            'message': 'Auto-saved'
        })
        
    except Exception as e:
        print(f"Auto-save error: {str(e)}")
        return JsonResponse({'success': False, 'error': str(e)})

@login_required(login_url='login')
def generate_slug_ajax(request):
    """Generate slug from title via AJAX"""
    title = request.GET.get('title', '')
    post_id = request.GET.get('post_id')
    
    if not title:
        return JsonResponse({'slug': '', 'error': 'No title provided'})
    
    exclude_id = int(post_id) if post_id and post_id.isdigit() else None
    slug = generate_unique_slug(title, exclude_id=exclude_id)
    
    return JsonResponse({'slug': slug})

@csrf_exempt
@login_required(login_url='login')
def remove_featured_image(request):
    """Remove featured image via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        data = json.loads(request.body)
        post_id = data.get('post_id')
        
        if not post_id:
            return JsonResponse({'success': False, 'error': 'No post ID provided'})
        
        post = get_object_or_404(Post, pk=post_id, author=request.user)
        
        if post.featured_image:
            # Remove file from storage
            if os.path.exists(post.featured_image.path):
                os.remove(post.featured_image.path)
            
            post.featured_image = None
            post.save()
        
        return JsonResponse({'success': True, 'message': 'Featured image removed successfully'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@administrator_required  
@login_required(login_url='login')
def delete_post(request, pk):
    """Delete single post (move to trash)"""
    post = get_object_or_404(Post, pk=pk, author=request.user)
    
    if request.method == 'POST':
        post.is_trashed = True
        post.trashed_at = timezone.now()
        post.trashed_by = request.user
        post.status = 'trashed'
        post.save()
        
        messages.success(request, f'Post "{post.title}" moved to trash.')
    
    return redirect('posts')

@administrator_required
@login_required(login_url='login')
def restore_post(request, pk):
    """Restore single post from trash"""
    post = get_object_or_404(Post, pk=pk, is_trashed=True)
    
    if request.method == 'POST':
        post.is_trashed = False
        post.trashed_at = None
        post.trashed_by = None
        post.status = 'draft'  
        post.save()
        
        messages.success(request, f'Post "{post.title}" restored as draft.')
    return redirect('posts')
    
@login_required(login_url='login')
def preview_post(request, pk):
    """Preview post functionality - renders post in single_blog.html template"""
    post = get_object_or_404(Post, pk=pk)
    
    # Check if user owns the post or is superuser
    if post.author != request.user and not request.user.is_superuser:
        messages.error(request, 'You can only preview your own posts.')
        return redirect('dashboard')
    
    
    if post.status == 'published':
        return redirect('posts_by_category_or_post', slug=post.slug)
    
    
    if post.status == 'draft':
        context = {
            'single_post': post,  
            'is_preview': True,
            'preview_notice': 'This is a preview of your draft post.',
            'comments': [], 
            # 'related_posts': Post.objects.filter(
            #     category=post.category, 
            #     status='published'
            # ).exclude(pk=post.pk)[:3] if post.category else []
        }
        return render(request, 'blog/preview_single_blog.html', context)
    
    # Fallback for other statuses
    return redirect('dashboard')


@administrator_required
@login_required(login_url='login')
def categories(request):
    search_query = request.GET.get('search', '')
    categories = Category.objects.annotate(
        post_count=Count('posts', distinct=True, filter=Q(posts__status='published'))
    ).order_by('category_name')
    
    if search_query:
        categories = categories.filter(
            Q(category_name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(slug__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(categories, 20) 
    page_number = request.GET.get('page')
    categories = paginator.get_page(page_number)
    
    context = {
        'categories': categories,
        'search_query': search_query,
    }
    return render(request, 'dashboard/categories.html', context)

@administrator_required
@login_required(login_url='login')
def add_category(request):
    if request.method == 'POST':
        category_name = request.POST.get('category_name', '').strip()
        slug = request.POST.get('slug', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not category_name:
            messages.error(request, 'Category name is required')
            return redirect('categories')
        
        if not slug:
            slug = slugify(category_name)
        
        if Category.objects.filter(category_name__iexact=category_name).exists():
            messages.error(request, 'Category with this name already exists')
            return redirect('categories')
        
        if Category.objects.filter(slug=slug).exists():
            messages.error(request, 'Category with this slug already exists')
            return redirect('categories')
        
        try:
            Category.objects.create(
                category_name=category_name,
                slug=slug,
                description=description if description else None
            )
            messages.success(request, f'Category "{category_name}" added successfully')
        except Exception as e:
            messages.error(request, 'Error adding category')
    return render(request, 'dashboard/categories.html')

@administrator_required
@login_required(login_url='login')
def edit_category(request, category_id):
    """Edit existing category"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category_name = request.POST.get('category_name', '').strip()
        slug = request.POST.get('slug', '').strip()
        description = request.POST.get('description', '').strip()
        
        # Check for duplicates (excluding current category)
        if Category.objects.filter(category_name__iexact=category_name).exclude(id=category_id).exists():
            messages.error(request, 'Category with this name already exists')
            return redirect('categories')
        
        if Category.objects.filter(slug=slug).exclude(id=category_id).exists():
            messages.error(request, 'Category with this slug already exists')
            return redirect('categories')
        
        try:
            category.category_name = category_name
            category.slug = slug
            category.description = description if description else None
            category.save()
            messages.success(request, f'Category "{category_name}" updated successfully')
        except Exception as e:
            messages.error(request, 'Error updating category')
    
    return redirect('categories')

@administrator_required
@login_required(login_url='login')
def delete_category(request, pk):
    if request.method == 'POST':
        category = get_object_or_404(Category, pk=pk)
        category_name = category.category_name
        
        try:
            category.delete()
            messages.success(request, f'Category "{category_name}" deleted successfully')
        except Exception as e:
            messages.error(request, 'Error deleting category')
    
    return redirect('categories')

@administrator_required
@login_required(login_url='login')
def view_category(request, slug):
    category = get_object_or_404(Category, slug=slug)
    
    # Get posts for this category (same logic as posts_by_category_or_post)
    posts = Post.objects.filter(status='published', category=category)
    paginator = Paginator(posts, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'blog/posts_by_category.html', context)

@author_or_admin_required
@login_required(login_url='login')
def comment(request):
    # Get filter parameters
    status = request.GET.get('status', 'all')
    page = request.GET.get('page', 1)
    
    # Base queryset
    comments = Comment.objects.select_related('post').order_by('-created_on')
    
    # Apply status filters
    if status == 'mine':
        # Assuming you want comments on posts by the current user
        comments = comments.filter(post__author=request.user)
    elif status == 'pending':
        comments = comments.filter(approved=False)
    elif status == 'approved':
        comments = comments.filter(approved=True)
    
    # Count for each status
    all_count = Comment.objects.count()
    mine_count = Comment.objects.filter(post__author=request.user).count()
    pending_count = Comment.objects.filter(approved=False).count()
    approved_count = Comment.objects.filter(approved=True).count()
    
    # Pagination
    paginator = Paginator(comments, 10)  # 10 comments per page
    page_obj = paginator.get_page(page)
    
    context = {
        'comments': page_obj,
        'current_status': status,
        'all_count': all_count,
        'mine_count': mine_count,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'paginator': paginator,
        'page_obj': page_obj,
    }
    
    return render(request, 'dashboard/comments.html', context)
@administrator_required
@login_required(login_url='login')
def bulk_comment_action(request):
    if request.method == 'POST':
        action = request.POST.get('bulk_action')
        comment_ids = request.POST.getlist('comment_ids')
        
        if comment_ids:
            comments = Comment.objects.filter(id__in=comment_ids)
            
            if action == 'approve':
                comments.update(approved=True)
            elif action == 'unapprove':
                comments.update(approved=False)
            elif action == 'delete':
                comments.delete()
    
    return redirect('comments')

@login_required(login_url='login')
def comment_approve(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.approved = True
    comment.save()
    return redirect('comments')

@login_required(login_url='login')
def comment_unapprove(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.approved = False
    comment.save()
    return redirect('comments')
@administrator_required
@login_required(login_url='login')
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    comment.delete()
    return redirect('comments')

@login_required(login_url='login')
def comment_edit(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        new_body = request.POST.get('comment_body')
        if new_body:
            comment.body = new_body
            comment.save()
    return redirect('comments')

@login_required(login_url='login')
def comment_reply(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.method == 'POST':
        reply_text = request.POST.get('reply_text')
        if reply_text:
            Comment.objects.create(
                post=comment.post,
                parent=comment,
                name=request.user.get_full_name() or request.user.username,
                email=request.user.email,
                body=reply_text,
                approved=True
            )
    return redirect('comments')

@login_required(login_url='login')
def media_library(request):
    """Main media library view with filtering and pagination"""
    
    # Get filter parameters
    media_type = request.GET.get('type', 'all')
    search_query = request.GET.get('search', '')
    date_filter = request.GET.get('date', 'all')
    
    # Base queryset
    media_files = MediaFile.objects.all()
    
    # Apply filters
    if media_type != 'all':
        media_files = media_files.filter(category=media_type)
    
    if search_query:
        media_files = media_files.filter(
            Q(file__icontains=search_query) |
            Q(alt_text__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Date filtering (simplified)
    if date_filter != 'all':
        # You can expand this based on your needs
        pass
    
    # Pagination (12 items per page for grid layout)
    paginator = Paginator(media_files, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # AJAX request for load more
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Check if this is NOT a request from the post editor
        if 'post-editor' in request.GET:
            # Return JSON for post editor modal
            media_data = []
            for media in page_obj:
                media_data.append({
                    'id': media.id,
                    'url': media.file.url,
                    'name': os.path.basename(media.file.name),
                    'type': media.file_type,
                    'size': media.file_size,
                    'alt_text': media.alt_text,
                    'description': media.description,
                    'created_at': media.created_at.strftime('%B %d, %Y'),
                    'file_extension': media.file_extension,
                    'thumbnail_url': media.get_thumbnail_url(),
                })
            
            return JsonResponse({
                'media_files': media_data,
                'has_next': page_obj.has_next(),
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            })
        elif request.GET.get('page'):  # This handles the load more button
            media_data = []
            for media in page_obj:
                media_data.append({
                    'id': media.id,
                    'url': media.file.url,
                    'name': os.path.basename(media.file.name),
                    'type': media.file_type,
                    'size': media.file_size,
                    'alt_text': media.alt_text,
                    'description': media.description,
                    'created_at': media.created_at.strftime('%B %d, %Y'),
                    'file_extension': media.file_extension,
                    'thumbnail_url': media.get_thumbnail_url(),
                })
            
            return JsonResponse({
                'media_files': media_data,
                'has_next': page_obj.has_next(),
                'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
            })
    
    # Get media type counts for filter buttons
    media_counts = {
        'all': MediaFile.objects.count(),
        'image': MediaFile.objects.filter(category='image').count(),
        'document': MediaFile.objects.filter(category='document').count(),
        'video': MediaFile.objects.filter(category='video').count(),
        'audio': MediaFile.objects.filter(category='audio').count(),
        'other': MediaFile.objects.filter(category='other').count(),
    }
    
    context = {
        'media_files': page_obj,
        'media_type': media_type,
        'search_query': search_query,
        'date_filter': date_filter,
        'media_counts': media_counts,
        'has_next': page_obj.has_next(),
        'next_page_number': page_obj.next_page_number() if page_obj.has_next() else None,
    }
    
    return render(request, 'dashboard/media_library.html', context)

@login_required(login_url='login')
def add_media(request):
    """Add new media files page"""
    if request.method == 'POST':
        files = request.FILES.getlist('files')
        uploaded_files = []
        
        for file in files:
            # Create MediaFile instance
            media_file = MediaFile(file=file)
            
            # Set alt_text to filename without extension
            media_file.alt_text = os.path.splitext(file.name)[0]
            
            media_file.save()
            uploaded_files.append(media_file)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            # AJAX response - check if request came from media library
            referer = request.META.get('HTTP_REFERER', '')
            
            files_data = []
            for media in uploaded_files:
                files_data.append({
                    'id': media.id,
                    'name': os.path.basename(media.file.name),
                    'url': media.file.url,
                    'type': media.file_type,
                    'size': media.file_size,
                })
            
            response_data = {
                'success': True,
                'files': files_data,
                'message': f'Successfully uploaded {len(uploaded_files)} file(s)'
            }
            
            # If not from media library page, redirect to media library
            if 'media/' not in referer or 'add-media' in referer:
                response_data['redirect'] = '/dashboard/media/' 
            
            return JsonResponse(response_data)
        else:
            messages.success(request, f'Successfully uploaded {len(uploaded_files)} file(s)')
            return redirect('/dashboard/media/')  
    
    return render(request, 'dashboard/add_media.html')

@login_required(login_url='login')
def media_detail(request, media_id):
    """Get media file details for modal"""
    media_file = get_object_or_404(MediaFile, id=media_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'id': media_file.id,
            'url': media_file.file.url,
            'name': os.path.basename(media_file.file.name),
            'type': media_file.file_type,
            'size': media_file.file_size,
            'alt_text': media_file.alt_text,
            'description': media_file.description,
            'created_at': media_file.created_at.strftime('%B %d, %Y'),
            'file_extension': media_file.file_extension,
            'thumbnail_url': media_file.get_thumbnail_url(),
            'dimensions': getattr(media_file, 'dimensions', None),  
        }
        return JsonResponse(data)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@require_http_methods(["POST"])
def update_media(request, media_id):
    """Update media file details"""
    media_file = get_object_or_404(MediaFile, id=media_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = json.loads(request.body)
        
        # Update fields
        media_file.alt_text = data.get('alt_text', media_file.alt_text)
        media_file.description = data.get('description', media_file.description)
        media_file.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Media updated successfully'
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@require_http_methods(["POST"])
def delete_media(request, media_id):
    """Delete media file"""
    media_file = get_object_or_404(MediaFile, id=media_id)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        media_file.delete() 
        
        return JsonResponse({
            'success': True,
            'message': 'Media deleted successfully'
        })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@require_http_methods(["POST"])
def bulk_delete_media(request):
    """Bulk delete media files"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = json.loads(request.body)
        media_ids = data.get('media_ids', [])
        
        if media_ids:
            deleted_count = 0
            for media_id in media_ids:
                try:
                    media_file = MediaFile.objects.get(id=media_id)
                    media_file.delete()
                    deleted_count += 1
                except MediaFile.DoesNotExist:
                    continue
            
            return JsonResponse({
                'success': True,
                'message': f'Successfully deleted {deleted_count} file(s)'
            })
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


@administrator_required
@login_required(login_url='login')
def mentor_applications_dashboard(request):
    """Main dashboard view with filtering"""
    status_filter = request.GET.get('status', 'all')
    search = request.GET.get('search', '')
    
    # Base queryset
    applications = MentorApplication.objects.all().order_by('-submitted_at')
    
    # Apply status filters
    if status_filter == 'pending':
        applications = applications.filter(pending=True, approved=False, rejected=False)
    elif status_filter == 'approved':
        applications = applications.filter(approved=True)
    elif status_filter == 'rejected':
        applications = applications.filter(rejected=True)
    
    # Apply search
    if search:
        applications = applications.filter(
            Q(full_name__icontains=search) |
            Q(email__icontains=search) |
            Q(area_of_expertise__icontains=search)
        )
    
    # Get counts for filter tabs
    counts = {
        'all': MentorApplication.objects.count(),
        'pending': MentorApplication.objects.filter(pending=True, approved=False, rejected=False).count(),
        'approved': MentorApplication.objects.filter(approved=True).count(),
        'rejected': MentorApplication.objects.filter(rejected=True).count(),
    }
    
    context = {
        'applications': applications,
        'status_filter': status_filter,
        'search': search,
        'counts': counts,
    }
    return render(request, 'dashboard/mentors_dash.html', context)

@administrator_required
@login_required(login_url='login')
def application_detail_ajax(request, pk):
    """Return application details via AJAX for modal"""
    application = get_object_or_404(MentorApplication, pk=pk)
    
    data = {
        'id': application.pk,
        'full_name': application.full_name,
        'email': application.email,
        'phone_number': application.phone_number,
        'job_title': application.job_title or 'Not provided',
        'area_of_expertise': application.get_area_of_expertise_display(),
        'years_of_experience': application.years_of_experience,
        'bio': application.bio,
        'linkedin_link': application.linkedin_link,
        'facebook_link': application.facebook_link,
        'submitted_at': application.submitted_at.strftime('%B %d, %Y at %I:%M %p'),
        'professional_picture': application.professional_picture.url if application.professional_picture else None,
        'cv': application.cv.url if application.cv else None,
        'certificate': application.certificate.url if application.certificate else None,
        'status': {
            'approved': application.approved,
            'pending': application.pending,
            'rejected': application.rejected,
        }
    }
    return JsonResponse(data)

@administrator_required
@login_required(login_url='login')
@require_http_methods(["POST"])
def approve_application(request, pk):
    """Approve a mentor application"""
    application = get_object_or_404(MentorApplication, pk=pk)
    
    if not application.approved:
        application.approved = True
        application.pending = False
        application.rejected = False
        application.save()
        # Send approval email
        try:
            html_message = render_to_string('main/emails/mentor_approval_email.html', {
                'full_name': application.full_name,
            })
            
            send_mail(
                subject="Doclumina Mentorship Application Approved",
                message="",  # Plain text fallback
                from_email=f"Doclumina <{settings.CONTACT_EMAIL}>",
                recipient_list=[application.email],
                html_message=html_message,
                fail_silently=False
            )
            messages.success(request, f"Application for {application.full_name} approved and email sent.", extra_tags='mentor_dashboard')
        except Exception as e:
            messages.warning(request, f"Application approved but email failed to send: {str(e)}", extra_tags='mentor_dashboard')
    else:
        messages.info(request, f"Application for {application.full_name} is already approved.", extra_tags='mentor_dashboard')
    
    return redirect('mentor_applications_dashboard')

@administrator_required
@login_required(login_url='login')
@require_http_methods(["POST"])
def reject_application(request, pk):
    """Reject a mentor application with reason"""
    application = get_object_or_404(MentorApplication, pk=pk)
    reason = request.POST.get('reason', '').strip()
    
    if not reason:
        messages.error(request, "Rejection reason is required.", extra_tags='mentor_dashboard')
        return redirect('mentor_applications_dashboard')
    
    if not application.rejected:
        application.approved = False
        application.pending = False
        application.rejected = True
        application.save()
        
        # Send rejection email
        try:
            html_message = render_to_string('main/emails/mentor_rejection_email.html', {
                'full_name': application.full_name,
                'reason': reason,
            })
            
            send_mail(
                subject="Doclumina Mentorship Application Declined",
                message="",  # Plain text fallback
                from_email=f"Doclumina <{settings.CONTACT_EMAIL}>",
                recipient_list=[application.email],
                html_message=html_message,
                fail_silently=False
            )
            messages.success(request, f"Application for {application.full_name} rejected and email sent.", extra_tags='mentor_dashboard')
        except Exception as e:
            messages.warning(request, f"Application rejected but email failed to send: {str(e)}", extra_tags='mentor_dashboard')
    else:
        messages.info(request, f"Application for {application.full_name} is already rejected.", extra_tags='mentor_dashboard')
    
    return redirect('mentor_applications_dashboard')

@administrator_required
@login_required(login_url='login')
@require_http_methods(["POST"])
def delete_application(request, pk):
    """Delete any application permanently (approved, rejected, or pending)"""
    application = get_object_or_404(MentorApplication, pk=pk)
    
    name = application.full_name
    application.delete()  # Files will be deleted by the post_delete signal
    messages.success(request, f"Application for {name} has been permanently deleted.", extra_tags='mentor_dashboard')
    
    return redirect('mentor_applications_dashboard')

@administrator_required
@login_required
@require_http_methods(["POST"])
def change_status(request, pk):
    """Change application status (approve to reject, or reject to approve)"""
    application = get_object_or_404(MentorApplication, pk=pk)
    new_status = request.POST.get('new_status')
    
    if new_status == 'reject' and application.approved:
        reason = request.POST.get('reason', '').strip()
        
        if not reason:
            messages.error(request, "Rejection reason is required.", extra_tags='mentor_dashboard')
            return redirect('mentor_applications_dashboard')
        
        application.approved = False
        application.pending = False
        application.rejected = True
        application.save()
        
        # Send status change email with dynamic template
        try:
            html_message = render_to_string('main/emails/mentor_status_change_email.html', {
                'full_name': application.full_name,
                'status': 'rejected',
                'reason': reason,
            })
            
            send_mail(
                subject="Doclumina Mentorship Application Status Update",
                message="",
                from_email=f"Doclumina <{settings.CONTACT_EMAIL}>",
                recipient_list=[application.email],
                html_message=html_message,
                fail_silently=False
            )
            messages.success(request, f"Application for {application.full_name} changed to rejected and email sent.", extra_tags='mentor_dashboard')
        except Exception as e:
            messages.warning(request, f"Status changed but email failed to send: {str(e)}", extra_tags='mentor_dashboard')
    
    elif new_status == 'approve' and application.rejected:
        application.approved = True
        application.pending = False
        application.rejected = False
        application.save()
        
        # Send approval email with dynamic template
        try:
            html_message = render_to_string('main/emails/mentor_status_change_email.html', {
                'full_name': application.full_name,
                'status': 'approved',
            })
            
            send_mail(
                subject="Doclumina Mentorship Application Approved",
                message="",
                from_email=f"Doclumina <{settings.CONTACT_EMAIL}>",
                recipient_list=[application.email],
                html_message=html_message,
                fail_silently=False
            )
            messages.success(request, f"Application for {application.full_name} changed to approved and email sent.", extra_tags='mentor_dashboard')
        except Exception as e:
            messages.warning(request, f"Status changed but email failed to send: {str(e)}", extra_tags='mentor_dashboard')
    
    return redirect('mentor_applications_dashboard')

def mentorship_application_dashboard(request):
    """Dashboard view with search and pagination"""
    search_query = request.GET.get('search', '').strip()
    
    # Get all applications
    applications = MentorshipApplication.objects.all()
    
    # Apply search filter
    if search_query:
        applications = applications.filter(
            Q(full_name__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(payment_reference__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(applications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_count': paginator.count
    }
    return render(request, 'dashboard/mentorship_dashboard.html', context)

def mentorship_application_detail(request, application_id):
    """AJAX endpoint to get application details for modal"""
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        application = get_object_or_404(MentorshipApplication, pk=application_id)
        
        data = {
            'id': application.id,
            'full_name': application.full_name,
            'email': application.email,
            'phone_number': application.phone_number,
            'programs': application.get_program_names(),
            'total_amount': application.total_amount,
            'is_paid': application.is_paid,
            'payment_reference': application.payment_reference or 'N/A',
            'applied_at': application.applied_at.strftime('%B %d, %Y at %I:%M %p'),
            'payment_confirmed_at': application.payment_confirmed_at.strftime('%B %d, %Y at %I:%M %p') if application.payment_confirmed_at else 'N/A'
        }
        return JsonResponse(data)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def mentorship_application_delete(request, application_id):
    """AJAX endpoint to delete application"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        application = get_object_or_404(MentorshipApplication, pk=application_id)
        application.delete()
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Invalid request'}, status=400)

@administrator_required
@login_required(login_url='login')
def testimonials(request):
    """List all testimonials with pagination"""
    testimonials = Testimonial.objects.all().order_by('-created_at')
    paginator = Paginator(testimonials, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard/testimonials.html', {
        'page_obj': page_obj,
        'testimonials': page_obj.object_list,
    })

@administrator_required
@login_required(login_url='login')
@require_http_methods(["POST"])
def add_testimonial(request):
    """Create new testimonial"""
    try:
        data = json.loads(request.body)
        testimonial = Testimonial.objects.create(
            name=data['name'],
            current_job=data['current_job'],
            testimony=data['testimony']
        )
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@administrator_required    
@login_required(login_url='login')
def edit_testimonial(request, pk):
    """Edit testimonial - GET returns data, POST updates"""
    testimonial = get_object_or_404(Testimonial, pk=pk)
    
    if request.method == 'GET':
        return JsonResponse({
            'id': testimonial.id,
            'name': testimonial.name,
            'current_job': testimonial.current_job,
            'testimony': testimonial.testimony,
        })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            testimonial.name = data['name']
            testimonial.current_job = data['current_job']
            testimonial.testimony = data['testimony']
            testimonial.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

@administrator_required
@login_required(login_url='login')
@require_http_methods(["DELETE"])
def delete_testimonial(request, pk):
    """Delete testimonial"""
    try:
        testimonial = get_object_or_404(Testimonial, pk=pk)
        testimonial.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    




def is_admin(user):
    return user.groups.filter(name='Administrator').exists()


@login_required(login_url='login')
@user_passes_test(is_admin)
def user_list(request):
    search = request.GET.get('search', '')
    role_filter = request.GET.get('role', '')

    users = User.objects.select_related('profile').annotate(
        post_count=Count('blog_post_authored', distinct=True)
    ).order_by('-date_joined')
    
    users = User.objects.select_related('profile').prefetch_related('groups')
    
    if search:
        users = users.filter(
            Q(username__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search) |
            Q(email__icontains=search)
        )
    
    if role_filter:
        users = users.filter(groups__name=role_filter)
    
    # Get user counts
    all_count = User.objects.count()
    admin_count = User.objects.filter(groups__name='Administrator').count()
    author_count = User.objects.filter(groups__name='Author').count()
    
    # Pagination
    paginator = Paginator(users, 10)
    page = request.GET.get('page')
    users = paginator.get_page(page)

    
    # Handle bulk actions
    if request.method == 'POST':
        form = BulkActionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            selected_ids = json.loads(form.cleaned_data['selected_users'])
            
            if action == 'delete':
                User.objects.filter(id__in=selected_ids).exclude(id=request.user.id).delete()
                messages.success(request, f'Successfully deleted {len(selected_ids)} users.')
            elif action.startswith('change_role_'):
                role_name = action.split('_')[-1].title()
                try:
                    group = Group.objects.get(name=role_name)
                    for user_id in selected_ids:
                        user = User.objects.get(id=user_id)
                        user.groups.clear()
                        user.groups.add(group)
                        set_user_permissions_by_role(user, role_name)  # NEW: Set admin flags
                    messages.success(request, f'Successfully changed role for {len(selected_ids)} users.')
                except Group.DoesNotExist:
                    messages.error(request, f'Role {role_name} does not exist.')
            
            return redirect('users')
    
    bulk_form = BulkActionForm(initial={'selected_users': '[]'})
    
    context = {
        'users': users,
        'search': search,
        'role_filter': role_filter,
        'all_count': all_count,
        'admin_count': admin_count,
        'author_count': author_count,
        'bulk_form': bulk_form,
    }
    return render(request, 'dashboard/users.html', context)

@administrator_required
@login_required(login_url='login')
@user_passes_test(is_admin)
def add_user(request):
    if request.method == 'POST':
        form = UserCreateForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'User "{user.username}" has been created successfully.')
            return redirect('users')
    else:
        form = UserCreateForm()
    
    return render(request, 'dashboard/add_user.html', {'form': form})

@administrator_required
@login_required(login_url='login')
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.user.id == user.id:
        return JsonResponse({'success': False, 'message': 'You cannot delete your own account'})
    
    if request.method == 'POST':
        username = user.username
        user.delete()
        return JsonResponse({'success': True, 'message': f'User "{username}" has been deleted successfully'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required(login_url='login')
def profile(request, user_id=None):
    # Determine target user and permissions
    if user_id:
        if not (request.user.is_staff or request.user.groups.filter(name='Administrator').exists()):
            messages.error(request, 'You do not have permission to edit other users.')
            return redirect('profile')
        target_user = get_object_or_404(User, id=user_id)
        is_admin_editing = True
        redirect_url = 'users'
    else:
        target_user = request.user  # This should have an ID
        is_admin_editing = False
        redirect_url = 'profile'
    
    # Ensure target_user has an ID (should always be true for saved users)
    if not target_user.id:
        messages.error(request, 'User not found.')
        return redirect('dashboard')
    
    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    
    if request.method == 'POST':
        return handle_profile_update(request, target_user, profile, is_admin_editing, redirect_url)
    
    # GET request - show forms
    user_form = UserEditForm(instance=target_user, show_role=is_admin_editing)
    profile_form = UserProfileEditForm(instance=profile)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'profile': profile,
        'target_user': target_user,  # Make sure this has an ID
        'is_admin_editing': is_admin_editing,
        'can_edit_role': is_admin_editing,
    }
    
    return render(request, 'dashboard/profile.html', context)


def handle_profile_update(request, target_user, profile, is_admin_editing, redirect_url):
    """Handle POST request for profile updates"""
    user_form = UserEditForm(request.POST, instance=target_user, show_role=is_admin_editing)
    profile_form = UserProfileEditForm(request.POST, request.FILES, instance=profile)
    
    if not (user_form.is_valid() and profile_form.is_valid()):
        messages.error(request, 'Please correct the errors below.')
        return render(request, 'dashboard/profile.html', {
            'user_form': user_form,
            'profile_form': profile_form,
            'profile': profile,
            'target_user': target_user,
            'is_admin_editing': is_admin_editing,
            'can_edit_role': is_admin_editing,
        })
    
    try:
        with transaction.atomic():
            user = user_form.save()
            profile_form.save()
            
            # Handle role updates for admin edits
            if is_admin_editing and 'role' in user_form.cleaned_data:
                role = user_form.cleaned_data.get('role')
                if role:
                    user.groups.set([role])  # More efficient than clear + add
                    set_user_permissions_by_role(user, role.name)
        
        success_msg = f'{"Profile" if not is_admin_editing else f"User \"{user.username}\""} updated successfully.'
        return redirect(redirect_url)
        
    except Exception as e:
        messages.error(request, 'Error updating profile. Please try again.')
        return redirect(redirect_url)

# ==================== PAGES MANAGEMENT ====================

@administrator_required
@login_required(login_url='login')
def pages(request):
    # Get status filter from GET parameters
    status_filter = request.GET.get('status', 'all')
    
    # Base queryset with optimized queries
    pages_queryset = Page.objects.select_related('author').order_by('-created_at')
    
    # Apply status filtering
    if status_filter == 'trash':
        pages_queryset = pages_queryset.filter(is_trashed=True)
    else:
        # For non-trash filters, exclude trashed pages
        pages_queryset = pages_queryset.filter(is_trashed=False)
        
        # Apply specific status filters
        if status_filter == 'published':
            pages_queryset = pages_queryset.filter(status='published')
        elif status_filter == 'draft':
            pages_queryset = pages_queryset.filter(status='draft')
        # 'all' shows both published and draft (non-trashed)
    
    # Get tab counts using a single optimized query
    tab_counts = get_optimized_tab_counts()
    
    # Pagination
    paginator = Paginator(pages_queryset, 20)
    page_number = request.GET.get('page')
    pages_obj = paginator.get_page(page_number)
    
    context = {
        'pages': pages_obj,
        'tab_counts': tab_counts,
        'current_status': status_filter,
    }
    
    return render(request, 'dashboard/pages.html', context)


def get_optimized_tab_counts():
    """
    Get tab counts using a single optimized query with conditional aggregation
    """
    counts = Page.objects.aggregate(
        all=Count('id', filter=Q(is_trashed=False)),
        published=Count('id', filter=Q(status='published', is_trashed=False)),
        draft=Count('id', filter=Q(status='draft', is_trashed=False)),
        trash=Count('id', filter=Q(is_trashed=True))
    )
    return counts

@administrator_required
@login_required(login_url='login')
def add_page(request):
    if request.method == 'POST':
        form = PageForm(request.POST, request.FILES)
        if form.is_valid():
            page = form.save(commit=False)
            page.author = request.user
            
            # Handle featured image from media library
            featured_image_id = request.POST.get('featured_image_id')
            if featured_image_id:
                try:
                    media_file = MediaFile.objects.get(id=featured_image_id)
                    page.featured_image = media_file.file
                except MediaFile.DoesNotExist:
                    pass
            
            # Handle status
            if 'publish' in request.POST:
                page.status = 'published'
                if not page.published_date:
                    page.published_date = timezone.now()
            else:
                page.status = 'draft'
            
            # Generate slug if not provided
            if not page.slug and page.title:
                page.slug = generate_unique_page_slug(page.title)
            
            page.save()
            messages.success(request, f'Page "{page.title}" has been updated successfully.')
            return redirect('pages')
    else:
        form = PageForm()
    
    context = {
        'form': form,
        'page': None,
    }
    return render(request, 'dashboard/page_form.html', context)

@administrator_required
@login_required(login_url='login')
@require_http_methods(["POST"])
def delete_page(request, pk):
    page = get_object_or_404(Page, pk=pk)
    page.move_to_trash(request.user)
    return JsonResponse({'success': True, 'message': f'Page "{page.title}" has been moved to trash.'})

@administrator_required
@login_required(login_url='login')
@require_http_methods(["POST"])
def restore_page(request, pk):
    page = get_object_or_404(Page, pk=pk)
    page.restore_from_trash()
    return JsonResponse({'success': True, 'message': f'Page "{page.title}" has been restored from trash.'})

@administrator_required
@login_required(login_url='login')
@require_http_methods(["POST"])
def bulk_page_action(request):
    action = request.POST.get('action')
    page_ids = request.POST.getlist('page_ids')
    current_status = request.POST.get('current_status', 'all')
    
    if not page_ids:
        return JsonResponse({'success': False, 'message': 'No pages selected.'})
    
    pages = Page.objects.filter(id__in=page_ids)
    count = pages.count()
    
    try:
        if action == 'delete':
            for page in pages:
                page.move_to_trash(request.user)
            message = f'{count} page{"s" if count != 1 else ""} moved to trash.'
            
        elif action == 'delete_permanently':
            if current_status == 'trash':
                pages.delete()
                message = f'{count} page{"s" if count != 1 else ""} permanently deleted.'
            else:
                return JsonResponse({'success': False, 'message': 'Pages can only be permanently deleted from trash.'})
                
        elif action == 'restore':
            for page in pages:
                page.restore_from_trash()
            message = f'{count} page{"s" if count != 1 else ""} restored from trash.'
            
        elif action == 'publish':
            pages.update(status='published', published_date=timezone.now())
            message = f'{count} page{"s" if count != 1 else ""} published.'
            
        elif action == 'draft':
            pages.update(status='draft')
            message = f'{count} page{"s" if count != 1 else ""} moved to draft.'
            
        else:
            return JsonResponse({'success': False, 'message': 'Invalid action.'})
            
        return JsonResponse({'success': True, 'message': message})
        
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'An error occurred: {str(e)}'})


@csrf_exempt
@login_required(login_url='login')
@require_http_methods(["POST"])
def auto_save_page(request):
    try:
        data = json.loads(request.body)
        page_id = data.get('page_id')
        
        if page_id:
            # Update existing page
            try:
                page = Page.objects.get(id=page_id, author=request.user)
            except Page.DoesNotExist:
                return JsonResponse({
                    'success': False, 
                    'message': 'Page not found'
                })
        else:
            # Create new page only if we have title or content
            title = data.get('title', '').strip()
            content = data.get('content', '').strip()
            
            if not title and not content:
                return JsonResponse({
                    'success': False, 
                    'message': 'No content to save'
                })
            
            page = Page(author=request.user, status='draft')
        
        # Update page fields
        title = data.get('title', '').strip()
        page.title = title
        page.content = data.get('content', '')
        page.excerpt = data.get('excerpt', '')
        page.seo_description = data.get('seo_description', '')
        page.seo_keywords = data.get('seo_keywords', '')
        
        # Handle slug generation
        provided_slug = data.get('slug', '').strip()
        
        # Always regenerate slug if title changed and no custom slug provided
        if title:
            if not provided_slug or provided_slug == generate_unique_page_slug(title, page.id if hasattr(page, 'id') else None):
                # Auto-generate slug from title
                page.slug = generate_unique_page_slug(title, page.id if hasattr(page, 'id') else None)
            else:
                # Use provided slug
                page.slug = provided_slug
        elif provided_slug:
            page.slug = provided_slug
        elif not hasattr(page, 'slug') or not page.slug:
            # Generate default slug for pages without title
            page.slug = generate_unique_page_slug('untitled', page.id if hasattr(page, 'id') else None)
        
        # Handle featured image
        featured_image_id = data.get('featured_image_id')
        if featured_image_id:
            try:
                media_file = MediaFile.objects.get(id=featured_image_id)
                page.featured_image = media_file.file
            except MediaFile.DoesNotExist:
                pass
        
        page.save()
        
        return JsonResponse({
            'success': True,
            'page_id': page.id,
            'slug': page.slug,
            'message': 'Saved'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'Error auto-saving page: {str(e)}'})


@login_required(login_url='login')
def generate_page_slug_ajax(request):
    if request.method == 'GET':
        title = request.GET.get('title', '').strip()
        page_id = request.GET.get('page_id', '')
        
        if title:
            slug = generate_unique_page_slug(title, page_id)
            return JsonResponse({'slug': slug})
    
    return JsonResponse({'slug': ''})


@login_required(login_url='login')
@require_http_methods(["POST"])
def remove_page_featured_image(request):
    try:
        data = json.loads(request.body)
        page_id = data.get('page_id')
        
        if not page_id:
            return JsonResponse({'success': False, 'error': 'No page ID provided'})
        
        page = get_object_or_404(Page, id=page_id, author=request.user)
        
        if page.featured_image:
            # Store the path before clearing
            image_path = page.featured_image.path if hasattr(page.featured_image, 'path') else None
            
            # Clear the featured image
            page.featured_image = None
            page.save()
            
            # Remove file from storage if it exists
            if image_path and os.path.exists(image_path):
                try:
                    os.remove(image_path)
                except OSError:
                    pass  # File might be in use or already deleted
        
        return JsonResponse({'success': True, 'message': 'Featured image removed successfully'})
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON data'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


def generate_unique_page_slug(title, exclude_id=None):
    """Generate a unique slug from title"""
    if not title or not title.strip():
        title = 'untitled'
        
    base_slug = slugify(title.strip()) or 'page'
    slug = base_slug
    counter = 1
    
    while True:
        queryset = Page.objects.filter(slug=slug)
        if exclude_id:
            queryset = queryset.exclude(id=exclude_id)
        
        if not queryset.exists():
            return slug
            
        slug = f"{base_slug}-{counter}"
        counter += 1

@administrator_required
@login_required(login_url='login')
def edit_page(request, pk):
    page = get_object_or_404(Page, pk=pk)
    
    if request.method == 'POST':
        form = PageForm(request.POST, request.FILES, instance=page)
        if form.is_valid():
            page = form.save(commit=False)
            
            # Handle featured image from media library
            featured_image_id = request.POST.get('featured_image_id')
            if featured_image_id:
                try:
                    media_file = MediaFile.objects.get(id=featured_image_id)
                    page.featured_image = media_file.file
                except MediaFile.DoesNotExist:
                    pass
            elif 'remove_featured_image' in request.POST:
                page.featured_image = None
            
            # Handle status
            if 'publish' in request.POST:
                page.status = 'published'
                if not page.published_date:
                    page.published_date = timezone.now()
            else:
                page.status = 'draft'
            
            page.save()
            messages.success(request, f'Page "{page.title}" has been updated successfully.')
            return redirect('pages')
    else:
        form = PageForm(instance=page)
    
    context = {
        'form': form,
        'page': page,
    }
    return render(request, 'dashboard/page_form.html', context)



def login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    storage = messages.get_messages(request)
    for _ in storage:
        pass
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user:
            auth_login(request, user)
            
            # Handle the 'next' parameter for redirect after login
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard') 
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'dashboard/login.html')

def logout(request):
    auth_logout(request)
    return redirect('login')