from django.conf import settings
from django.contrib import messages
from django.contrib.messages import get_messages
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect, render
import re
from django.core.paginator import Paginator
from blog.forms import CommentForm
from blog.models import Category, Comment, Post
from django.db.models import Q
from media_manager.models import User


def blog_main(request):
    featured_post = Post.objects.filter(is_featured=True, status='published')
    
    posts = Post.objects.filter(is_featured=False, status='published')
    paginator = Paginator(posts, 6)

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        'featured_post': featured_post,
        'page_obj': page_obj,
    }
    return render(request, 'blog/blog.html', context)


def posts_by_category_or_post(request, slug):
    
    category = Category.objects.filter(slug=slug).first()
    if category:
        posts = Post.objects.filter(status='published', category=category)
        paginator = Paginator(posts, 6)  
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context = {
            'page_obj': page_obj,
            'category': category,
        }
        return render(request, 'blog/posts_by_category.html', context)

    single_post = Post.objects.filter(slug=slug, status='published').first()

    show_newsletter = False
    if single_post:
        show_newsletter = single_post.category.filter(category_name__icontains='House Job Content').exists()


    featured_posts = Post.objects.filter(is_featured=True, status='published')
    posts = Post.objects.filter(is_featured=False, status='published')
    
    
    if single_post:
        comment_form = CommentForm()
    
        if request.method == 'POST':
            comment_form = CommentForm(request.POST)
            parent_id = request.POST.get('parent_id')
        
            if comment_form.is_valid():
                comment = comment_form.save(commit=False)
                comment.post = single_post
                if parent_id:
                    comment.parent = Comment.objects.get(id=parent_id)
                comment.save()
            
            
            send_mail(
                subject=f'New comment on "{single_post.title}"',
                message=f'A new comment by {comment.name} is awaiting approval.\n\nComment: {comment.body}',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=True,
            )
            
            messages.success(request, 'Your comment is awaiting approval.')
            return redirect('posts_by_category_or_post', slug=slug)
        
        else:
            if 'captcha' in comment_form.errors:
                messages.error(request, 'reCAPTCHA verification failed. Please try again.')
        
    else:
        comment_form = CommentForm()
    
    show_all = request.GET.get('show_all_comments')
    if show_all:
        comments = single_post.comments.filter(approved=True, parent=None).prefetch_related('replies')
    else:
        comments = single_post.comments.filter(approved=True, parent=None).prefetch_related('replies')[:10]

    total_comments = single_post.comments.filter(approved=True, parent=None).count()

    storage = get_messages(request)
    view_messages = []
    for message in storage:
        
        pass

    
    if request.method == 'POST' and comment_form.is_valid():
        view_messages = [msg for msg in get_messages(request) if 'comment' in str(msg).lower()]
    
    context = {
        'single_post': single_post,
        'author': single_post.author,
        'featured_posts': featured_posts,
        'posts': posts,
        'comment_form': comment_form,
        'comments': comments,
        'total_comments': total_comments,
        'show_all': show_all,
        'view_messages': view_messages,
        'show_newsletter': show_newsletter,
    }
    return render(request, 'blog/single_blog.html', context)

def search(request):
    keyword = request.GET.get('keyword')
    
    if keyword:
        posts = Post.objects.filter(
            Q(title__icontains=keyword) | Q(excerpt__icontains=keyword) | Q(content__icontains=keyword), 
            status='published'
        )
    else:
        posts = Post.objects.none()
    
    paginator = Paginator(posts, 6)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'keyword': keyword,
    }
    return render(request, 'blog/search.html', context)

def author_page(request, username):
    author = get_object_or_404(User, username=username)
    posts = Post.objects.published().filter(author=author)

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'author': author,
        'page_obj': page_obj,
    }
    return render(request, 'blog/author_page.html', context)

