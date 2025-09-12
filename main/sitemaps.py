# sitemaps.py
from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from blog.models import Post



class StaticViewSitemap(Sitemap):
    """Static pages sitemap"""
    priority = 0.5
    changefreq = 'weekly'
    
    def items(self):
        # Return URL paths that match your actual URL structure
        return [
            ('/', 'Homepage'),
            ('/about-us/', 'About Us'),
            ('/contact-us/', 'Contact Us'),
            ('/become-mentor/', 'Become Mentor'),
            ('/mentors/', 'Mentors'),
            ('/mentorship/', 'Mentorship'),
            ('/book-a-gp/', 'Book a GP'),
            ('/mental-health-service/', 'Mental Health Service'),
            ('/survival-loan/', 'Survival Loan'),
        ]
    
    def location(self, item):
        # item is a tuple (url, title)
        return item[0]


class BlogPostSitemap(Sitemap):
    """Blog posts sitemap"""
    changefreq = 'weekly'
    priority = 0.8
    
    def items(self):
        return Post.objects.filter(
            status='published', is_trashed=False  
        ).order_by('-created_at')
    

    
    def location(self, obj):
        # Direct URL construction matching your blog post pattern
        return f'/blog/{obj.slug}/'


class BlogPageSitemap(Sitemap):
    """Blog pages sitemap - for main app pages with slugs"""
    changefreq = 'monthly'
    priority = 0.6
    
    def items(self):
        from blog.models import Page  
        return Page.objects.filter(
            status='published', is_trashed=False
        ).order_by('title')
    

    
    def location(self, obj):
        # Main app page URLs
        return f'/page/{obj.slug}/'


class BlogCategorySitemap(Sitemap):
    """Blog categories sitemap"""
    changefreq = 'weekly'
    priority = 0.4
    
    def items(self):
        # Get unique category slugs from published posts
        return Post.objects.filter(
            status='published', is_trashed=False
        ).values_list('category__slug', flat=True).distinct().exclude(category__slug__isnull=True)
    
    def location(self, item):
        # Category URLs using your slug pattern
        return f'/blog/{item}/'



class AuthorSitemap(Sitemap):
    """Author pages sitemap"""
    changefreq = 'monthly' 
    priority = 0.3
    
    def items(self):
        # Get authors who have published posts
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        return User.objects.filter(
        blog_post_authored__status='published', blog_post_authored__is_trashed=False
                ).distinct().order_by('username')
    
    def location(self, obj):
        # Author page URLs using username
        return f'/blog/author/{obj.username}/'
    


# Sitemap registry
sitemaps = {
    'static': StaticViewSitemap,
    'blog_posts': BlogPostSitemap,
    'blog_pages': BlogPageSitemap,
    'categories': BlogCategorySitemap,
    'authors': AuthorSitemap,
}