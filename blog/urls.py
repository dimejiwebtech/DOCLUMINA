from django.urls import path
from . import views

urlpatterns = [
    path('', views.blog_main, name="blog"),
    path('search/', views.search, name='search'),
    path('author/<str:username>/', views.author_page, name='author_page'),
    path('<slug:slug>/', views.posts_by_category_or_post, name='posts_by_category_or_post'),
]