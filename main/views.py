from django.utils import timezone
import json
from django.db import IntegrityError
from django.forms import ValidationError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.views import View
import requests

from blog.models import Page, Post
from .forms import ContactForm, MentorApplicationForm, MentorshipApplicationForm, NewsletterForm
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import MENTORSHIP_PRICES, CookieConsent, MentorApplication, MentorshipApplication, Testimonial
from django.core.paginator import Paginator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

def homepage(request):
    testimonials = Testimonial.objects.all().order_by('-created_at')
    posts = Post.objects.filter(status='published')
    context = {
        'testimonials': testimonials,
        'posts': posts,
        'newsletter_form': NewsletterForm(),
        'show_newsletter': True
    }
    return render(request, 'main/homepage.html', context)


def about(request):
    return render(request, 'main/about.html')


def contact(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            email = form.cleaned_data['email']
            subject = form.cleaned_data['subject']
            message = form.cleaned_data['message']
            
            subject_display = dict(form.SUBJECT_CHOICES)[subject]
            email_subject = f"Contact Form: {subject_display}"
            
            try:
                # Send admin notification email
                admin_html_message = render_to_string('main/emails/contact_admin_email.html', {
                    'name': name,
                    'email': email,
                    'subject_display': subject_display,
                    'message': message,
                })
                
                send_mail(
                    subject=email_subject,
                    message="",  # Plain text fallback
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.CONTACT_EMAIL],
                    html_message=admin_html_message,
                    fail_silently=False,
                )
                
                # Send confirmation email to user
                confirmation_html_message = render_to_string('main/emails/contact_confirmation_email.html', {
                    'name': name,
                    'subject_display': subject_display,
                    'message': message,
                })
                
                send_mail(
                    subject="Thank you for contacting Doclumina",
                    message="",  # Plain text fallback
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[email],
                    html_message=confirmation_html_message,
                    fail_silently=True,
                )
                
                # Store success message in session (only for contact page)
                request.session['contact_message'] = {
                    'type': 'success',
                    'text': 'Your message has been sent successfully! We will respond within 24 hours.'
                }
                return redirect('contact')
                
            except Exception as e:    
                # Store error message in session (only for contact page)
                request.session['contact_message'] = {
                    'type': 'error',
                    'text': 'Sorry, there was an error sending your message. Please try again later.'
                }
        else:
            if 'captcha' in form.errors:
                # Store captcha error message in session (only for contact page)
                request.session['contact_message'] = {
                    'type': 'error',
                    'text': 'reCAPTCHA verification failed.'
                }
    else:
        form = ContactForm()
    
    # Retrieve and clear contact-specific message from session
    contact_message = request.session.pop('contact_message', None)
    
    context = {
        'form': form,
        'contact_message': contact_message,  # Pass to template
    }
    return render(request, 'main/contact.html', context)


def become_mentor(request):
    if request.method == "POST":
        form = MentorApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                application = form.save()

                # Send styled HTML acknowledgment email to applicant
                html_message = render_to_string('main/emails/mentor_applicant_confirmation_email.html', {
                    'full_name': application.full_name,
                })
                plain_message = strip_tags(html_message)
                
                send_mail(
                    subject="Mentor Application Received",
                    message=plain_message,
                    from_email=f"Doclumina <{settings.CONTACT_EMAIL}>",
                    recipient_list=[application.email],
                    html_message=html_message,
                    fail_silently=False
                )

                # Send styled HTML notification email to admin
                admin_html_message = render_to_string('main/emails/admin_notification_email.html', {
                    'full_name': application.full_name,
                    'email': application.email,
                    'phone_number': application.phone_number,
                    'area_of_expertise': application.get_area_of_expertise_display(),
                    'years_of_experience': application.years_of_experience,
                    'bio': application.bio,
                    'submitted_at': application.submitted_at.strftime('%B %d, %Y at %I:%M %p'),
                })
                admin_plain_message = strip_tags(admin_html_message)
                
                send_mail(
                    subject="New Mentor Application Received",
                    message=admin_plain_message,
                    from_email=f"Doclumina <{settings.CONTACT_EMAIL}>",
                    recipient_list=[settings.CONTACT_EMAIL],
                    html_message=admin_html_message,
                    fail_silently=False
                )

                messages.success(request, "Your application has been submitted successfully. You will receive an email once it is reviewed.")
                return redirect("become_mentor")
                
            except IntegrityError as e:
                
                if 'email' in str(e).lower():
                    messages.error(request, "An application with this email has already been submitted.")
                elif 'phone' in str(e).lower():
                    messages.error(request, "An application with this phone number has already been submitted.")
                else:
                    messages.error(request, "This application has already been submitted.")
                    
            except ValidationError as e:
                
                messages.error(request, "Please correct the errors below and try again.")      
                
        else:
            if 'captcha' in form.errors:
                messages.error(request, 'reCAPTCHA verification failed. Please try again.')
            
            messages.error(request, "Please correct the errors below and try again.")
            print(messages.error)
        

    else:
        form = MentorApplicationForm()
    
    context = {
        'form': form,
    }
    return render(request, "main/become_mentor.html", context)



def mentors(request):
    mentors = MentorApplication.objects.filter(approved=True).order_by("-submitted_at")
    paginator = Paginator(mentors, 4)  

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context ={
        'page_obj': page_obj,
    }

    
    return render(request, 'main/mentors/mentors.html', context)


def mentorship(request):
    """Display mentorship application form"""
    if request.method == "POST":
        form = MentorshipApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.save()
            
            # Redirect to payment page
            return redirect(reverse("payment_page", args=[application.id]))
        else:
            if 'captcha' in form.errors:
                messages.error(request, 'reCAPTCHA verification failed. Please try again.')
    else:
        form = MentorshipApplicationForm()

    context = {
        'form': form,
        'mentorship_prices': json.dumps(MENTORSHIP_PRICES)
    }
    return render(request, 'main/mentors/mentorship.html', context)

def payment_page(request, application_id):
    """Handle payment page and confirmation"""
    application = get_object_or_404(MentorshipApplication, pk=application_id)
    
    if application.is_paid:
        messages.info(request, 'This application has already been paid for.')
        return redirect(reverse("payment_success"))

    if request.method == "POST":
    # payment confirmation 
        application.payment_reference = f"PAY{application.id}{timezone.now().strftime('%Y%m%d%H%M')}"
        application.payment_confirmed_at = timezone.now()
        application.is_paid = True
        application.save()

    # Send confirmation email to applicant (after saving the payment details)
        send_applicant_confirmation_email(application)
        
        # Send notification email to admin
        send_admin_notification_email(application)

        messages.success(request, 'Payment confirmed successfully!')
        return redirect(reverse("payment_success"))

    context = {
        'application': application,
    }
    return render(request, "main/mentors/mentorship_payment_page.html", context)

def payment_success(request):
    """Display payment success page"""
    return render(request, "main/mentors/mentorship_payment_success.html")

def send_applicant_confirmation_email(application):
    """Send confirmation email to the applicant"""
    try:
        # Get fresh data from database
        application.refresh_from_db()
        
        context = {
            'application': application,
            'name': application.full_name,
            'reference': application.payment_reference,
            'date': application.payment_confirmed_at.strftime('%B %d, %Y') if application.payment_confirmed_at else 'N/A',
            'amount': application.total_amount,
            'whatsapp_links': application.get_whatsapp_links(),
        }
        
        
        html_message = render_to_string('main/emails/mentorship_payment_confirmation.html', context)
        plain_message = strip_tags(html_message)

        send_mail(
            subject="Mentorship Payment Confirmed - Welcome to Doclumina!",
            message=plain_message,
            from_email=f"Doclumina Mentorship <{settings.CONTACT_EMAIL}>",
            recipient_list=[application.email],
            html_message=html_message,
            fail_silently=False
        )
        # For debugging
        print(f"Confirmation email sent to {application.email}")  
    except Exception as e:
        print(f"Error sending applicant email: {e}")

def send_admin_notification_email(application):
    """Send notification email to admin"""
    try:
        html_message = render_to_string('main/emails/admin_mentorship_notification.html', {
            'application': application,
        })
        plain_message = strip_tags(html_message)

        # Send to admin email (you can configure multiple admins)
        admin_emails = [settings.ADMIN_EMAIL] if hasattr(settings, 'ADMIN_EMAIL') else [settings.CONTACT_EMAIL]
        
        send_mail(
            subject=f"New Mentorship Payment - {application.full_name}",
            message=plain_message,
            from_email=f"Doclumina System <{settings.CONTACT_EMAIL}>",
            recipient_list=admin_emails,
            html_message=html_message,
            fail_silently=False
        )
    except Exception as e:
        print(f"Error sending admin notification: {e}")

def get_program_price(request):
    """AJAX endpoint to get price for selected programs"""
    if request.method == 'GET':
        programs = request.GET.getlist('programs[]')
        total = sum(MENTORSHIP_PRICES.get(program, 0) for program in programs)
        return JsonResponse({'total_price': total})
    return JsonResponse({'error': 'Invalid request'}, status=400)



def book_gp(request):
    return render(request, 'main/book_gp.html')


def mental_health(request):
    return render(request, 'main/mental_health.html')


def survival_loan(request):
    return render(request, 'main/survival_loan.html')

def single_page(request, slug):
    single_page = get_object_or_404(Page, slug=slug, status='published')

    context = {
        'single_page': single_page,
    }
    return render(request, 'main/single_page.html', context)


class NewsletterSubscribeView(View):
    def post(self, request):
        form = NewsletterForm(request.POST)
        
        if form.is_valid():
            try:
                subscription = form.save()
                self.save_to_google_sheets(subscription)
                return JsonResponse({
                    'success': True,
                    'message': 'Thank you! You\'re now part of our exclusive healthcare community.'
                })
            except IntegrityError:  
                return JsonResponse({
                    'success': False,
                    'message': 'This email is already subscribed to our newsletter.'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': 'An error occurred. Please try again.'
                })
        
        error_message = 'Please check your input and try again.'
        if form.errors:
            # Get the first error from the first field that has errors
            first_field_errors = list(form.errors.values())[0]
            if first_field_errors:
                error_message = first_field_errors[0]

        return JsonResponse({
            'success': False,
            'message': error_message
        })
    
    def save_to_google_sheets(self, subscription):
        google_script_url = settings.GOOGLE_SHEETS_WEBHOOK_URL
        
        data = {
            'full_name': subscription.full_name,
            'email': subscription.email,
            'university': subscription.university,
            'current_role': subscription.current_role,
            'whatsapp_line': subscription.whatsapp_line,
            'subscribed_at': subscription.subscribed_at.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        try:
            response = requests.post(google_script_url, json=data, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            # Log error but don't fail the subscription
            return False
        

@csrf_exempt
@require_POST
def set_cookie_consent(request):
    try:
        data = json.loads(request.body)
        session_key = request.session.session_key
        
        if not session_key:
            request.session.save()
            session_key = request.session.session_key
        
        consent, created = CookieConsent.objects.update_or_create(
            session_key=session_key,
            defaults={
                'analytics_consent': data.get('analytics', False),
                'marketing_consent': data.get('marketing', False),
                'necessary_consent': True
            }
        )
        
        return JsonResponse({'status': 'success'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
class RobotsTxtView(TemplateView):
    template_name = 'robots.txt'
    content_type = 'text/plain'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['sitemap_url'] = self.request.build_absolute_uri('/sitemap.xml')
        return context
