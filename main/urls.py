from django.urls import path, include
from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from .sitemaps import sitemaps
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('newsletter/subscribe/', views.NewsletterSubscribeView.as_view(), name='newsletter_subscribe'),
    path('about-us/', views.about, name='about'),
    path('contact-us/', views.contact, name='contact'),
    path('become-mentor/', views.become_mentor, name='become_mentor'),
    path('page/<slug:slug>/', views.single_page, name='single_page'),
    path('mentors/', views.mentors, name='mentors'),
    # mentorship
    path('mentorship/', views.mentorship, name='mentorship'),
    path('payment/<int:application_id>/', views.payment_page, name='payment_page'),
    path('success/', views.payment_success, name='payment_success'),
    path('ajax/program-price/', views.get_program_price, name='get_program_price'),
    # mentorship
    path('book-a-gp/', views.book_gp, name="book_gp"),
    path('mental-health-service/', views.mental_health, name="mental_health"),
    path('survival-loan/', views.survival_loan, name="survival_loan"),

    # cookie
    path('set-cookie-consent', views.set_cookie_consent, name='set_cookie_consent'),

]