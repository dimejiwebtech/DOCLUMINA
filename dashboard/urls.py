from django.urls import path
from . import views


urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('posts/', views.posts, name='posts'),
    path('posts/bulk-action/', views.bulk_action, name='bulk_action'),
    # add post, edit, delete, restore & preview
    path('posts/add-post/', views.add_post, name='add_post'),
    path('posts/edit-post/<int:pk>/', views.edit_post, name='edit_post'),
    path('posts/delete-post/<int:pk>/', views.delete_post, name='delete_post'),
    path('posts/restore-post/<int:pk>/', views.restore_post, name='restore_post'),
    path('post-preview/<int:pk>/', views.preview_post, name='preview_post'),
    # add post, edit, delete, restore & preview

    # categories, add, edit, view & delete
    path('posts/categories/', views.categories, name='categories'),
    path('posts/categories/add/', views.add_category, name='add_category'),
    path('posts/categories/edit/<int:category_id>/', views.edit_category, name='edit_category'),
    path('posts/categories/delete/<int:pk>/', views.delete_category, name='delete_category'),
    path('categories/<slug:slug>/', views.view_category, name='view_category'),
    # categories, add, edit, view & delete

    # AJAX endpoints
    path('auto-save-post/', views.auto_save_post, name='auto_save_post'),
    path('generate-slug/', views.generate_slug_ajax, name='generate_slug'),
    path('remove-featured-image/', views.remove_featured_image, name='remove_featured_image'),

    # comments
    path('comments/', views.comment, name='comments'),
    path('comments/bulk-action/', views.bulk_comment_action, name='bulk_comment_action'),
    path('comments/<int:comment_id>/approve/', views.comment_approve, name='comment_approve'),
    path('comments/<int:comment_id>/unapprove/', views.comment_unapprove, name='comment_unapprove'),
    path('comments/<int:comment_id>/delete/', views.comment_delete, name='comment_delete'),
    path('comments/<int:comment_id>/edit/', views.comment_edit, name='comment_edit'),
    path('comments/<int:comment_id>/reply/', views.comment_reply, name='comment_reply'),
    # comments

    # Media management URLs
    path('media/', views.media_library, name='media_library'),
    path('media/add-media/', views.add_media, name='add_media'),
    path('media/<int:media_id>/', views.media_detail, name='media_detail'),
    path('media/<int:media_id>/update/', views.update_media, name='update_media'),
    path('media/<int:media_id>/delete/', views.delete_media, name='delete_media'),
    path('media/bulk-delete/', views.bulk_delete_media, name='bulk_delete_media'),
    # Media management URLs

    # Mentors Application
    path('mentors/', views.mentor_applications_dashboard, name='mentor_applications_dashboard'),
    path('mentors/detail/<int:pk>/', views.application_detail_ajax, name='application_detail_ajax'),
    path('mentors/approve/<int:pk>/', views.approve_application, name='approve_application'),
    path('mentors/reject/<int:pk>/', views.reject_application, name='reject_application'),
    path('mentors/delete/<int:pk>/', views.delete_application, name='delete_application'),
    path('mentors/change-status/<int:pk>/', views.change_status, name='change_status'),
    # Mentors Application

    #Mentorship Payment
    path('mentorship/', views.mentorship_application_dashboard, name='mentorship_dashboard'),
    path('mentorship/detail/<int:application_id>/', views.mentorship_application_detail, name='mentorship_detail'),
    path('mentorship/delete/<int:application_id>/', views.mentorship_application_delete, name='mentorship_delete'),
    #Mentorship Payment
    
    # Testimonials
    path('testimonials/', views.testimonials, name='testimonials'),
    path('testimonials/add/', views.add_testimonial, name='add_testimonial'),
    path('testimonials/<int:pk>/edit/', views.edit_testimonial, name='edit_testimonial'),
    path('testimonials/<int:pk>/delete/', views.delete_testimonial, name='delete_testimonial'),
    # Testimonials

    # Pages Management URLs
    path('pages/', views.pages, name='pages'),
    path('pages/bulk-action/', views.bulk_page_action, name='bulk_page_action'),
    path('pages/add-page/', views.add_page, name='add_page'),
    path('pages/edit-page/<int:pk>/', views.edit_page, name='edit_page'),
    path('pages/delete-page/<int:pk>/', views.delete_page, name='delete_page'),
    path('pages/restore-page/<int:pk>/', views.restore_page, name='restore_page'),
    
    # AJAX endpoints for pages
    path('auto-save-page/', views.auto_save_page, name='auto_save_page'),
    path('generate-page-slug/', views.generate_page_slug_ajax, name='generate_page_slug_ajax'),
    path('remove-page-featured-image/', views.remove_page_featured_image, name='remove_page_featured_image'),
    # Pages Management URLs

    # Users
    path('users/', views.user_list, name='users'),
    path('users/add-user/', views.add_user, name='add_user'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    path('users/profile/', views.profile, name='profile'),
    path('users/<int:user_id>/profile/', views.profile, name='edit_user_profile'),
    # Users
]

# Traffic