import os
import sys
import django
from django.conf import settings

# Add your Django project to the Python path
sys.path.append(r'C:\Users\Grimes\Desktop\DOCLUMINA')  # Raw string for Windows paths

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DOCLUMINA.settings')  # Update with your project name
django.setup()

from django.core.mail import send_mail
from django.core.mail import EmailMessage

def test_simple_email():
    """Test sending a simple email"""
    try:
        result = send_mail(
            subject='Test Email from Django OAuth2',
            message='This is a test email sent using Gmail OAuth2 authentication.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=['fearsomegrimes@gmail.com'],  # Replace with a real email
            fail_silently=False,
        )
        print(f"Simple email sent successfully. Result: {result}")
        return True
    except Exception as e:
        print(f"Failed to send simple email: {e}")
        return False

def test_html_email():
    """Test sending an HTML email"""
    try:
        email = EmailMessage(
            subject='Test HTML Email from Django OAuth2',
            body='<h1>Test Email</h1><p>This is a <strong>test email</strong> sent using Gmail OAuth2 authentication.</p>',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=['fearsomegrimes@gmail.com'],  # Replace with a real email
        )
        email.content_subtype = 'html'
        result = email.send()
        print(f"HTML email sent successfully. Result: {result}")
        return True
    except Exception as e:
        print(f"Failed to send HTML email: {e}")
        return False

def main():
    print("Testing Gmail OAuth2 Email Backend...")
    print(f"Email backend: {settings.EMAIL_BACKEND}")
    print(f"Email host: {settings.EMAIL_HOST}")
    print(f"Email port: {settings.EMAIL_PORT}")
    print(f"From email: {settings.DEFAULT_FROM_EMAIL}")
    print("-" * 50)
    
    # Test simple email
    print("Testing simple email...")
    test_simple_email()
    
    print("-" * 50)
    
    # Test HTML email
    print("Testing HTML email...")
    test_html_email()

if __name__ == '__main__':
    main()