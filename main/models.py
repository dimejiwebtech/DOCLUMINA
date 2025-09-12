from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.db.models.signals import post_delete
from django.dispatch import receiver
import os
from django.contrib.sessions.models import Session

class CookieConsent(models.Model):
    session_key = models.CharField(max_length=40, unique=True)
    analytics_consent = models.BooleanField(default=False)
    marketing_consent = models.BooleanField(default=False)
    necessary_consent = models.BooleanField(default=True)
    consent_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cookie_consent'

MENTORSHIP_CHOICES = [
    ("house_job", "House Job Mentorship"),
    ("nigerian_residency", "Nigerian Residency Mentorship"),
    ("usmle_canada", "USMLE/Canada Residency Mentorship"),
    ("amc_plab", "AMC/PLAB Pathway Mentorship"),
    ("mph", "US/UK/Canada MPH Mentorship"),
    ("express_entry", "Canadian Express Entry Mentorship"),
    ("non_clinical", "Non-clinical Role Mentorship"),
    ("mdcn_exam", "MDCN Exam"),
]

MENTORSHIP_PRICES = {
    "house_job": 15000,
    "nigerian_residency": 50000,
    "usmle_canada": 50000,
    "amc_plab": 50000,
    "mph": 50000,
    "express_entry": 50000,
    "non_clinical": 50000,
    "mdcn_exam": 50000,
}

class MentorApplication(models.Model):
    full_name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)  
    phone_number = models.CharField(max_length=20, unique=True) 
    job_title = models.CharField(max_length=100, help_text="Current professional job title", null=True)
    professional_picture = models.ImageField(upload_to='uploads/%Y/%m/%d/', null=True,  )
    linkedin_link = models.URLField(blank=True, null=True)
    facebook_link = models.URLField(blank=True, null=True)
    area_of_expertise = models.CharField(choices=MENTORSHIP_CHOICES, max_length=50)
    years_of_experience = models.PositiveIntegerField()
    bio = models.TextField(help_text="Short professional bio")
    cv = models.FileField(upload_to='uploads/%Y/%m/%d/')
    certificate = models.FileField(upload_to='uploads/%Y/%m/%d/')
    approved = models.BooleanField(default=False)
    pending = models.BooleanField(default=True)
    rejected = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['full_name', 'email']

    def clean(self):
        """Custom validation to prevent duplicate applications"""
        super().clean()

        # Check for duplicate full_name
        if self.full_name:
            existing_names = MentorApplication.objects.filter(
                full_name__iexact=self.full_name.strip()
            )
            if self.pk:
                existing_names = existing_names.exclude(pk=self.pk)
            if existing_names.exists():
                raise ValidationError({
                    'full_name': 'An application with this name already exists.'
                })

        # Check for duplicate email
        if self.email:
            existing_emails = MentorApplication.objects.filter(
                email__iexact=self.email.strip()
            )
            if self.pk:
                existing_emails = existing_emails.exclude(pk=self.pk)
            if existing_emails.exists():
                raise ValidationError({
                    'email': 'An application with this email already exists.'
                })

        # Check for duplicate phone_number
        if self.phone_number:
            cleaned_phone = ''.join(filter(str.isdigit, self.phone_number))
            existing_phones = MentorApplication.objects.exclude(pk=self.pk if self.pk else None)
            for app in existing_phones:
                existing_cleaned = ''.join(filter(str.isdigit, app.phone_number))
                if cleaned_phone == existing_cleaned:
                    raise ValidationError({
                        'phone_number': 'An application with this phone number already exists.'
                    })

    def save(self, *args, **kwargs):
        """Override save to ensure validation runs"""
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name
    
# To delete cv, certificates and profile photos
@receiver(post_delete, sender=MentorApplication)
def delete_files_on_application_delete(sender, instance, **kwargs):
    if instance.professional_picture and os.path.isfile(instance.professional_picture.path):
        os.remove(instance.professional_picture.path)
    if instance.cv and os.path.isfile(instance.cv.path):
        os.remove(instance.cv.path)
    if instance.certificate and os.path.isfile(instance.certificate.path):
        os.remove(instance.certificate.path)


# Mentorship Application Model
class MentorshipApplication(models.Model):
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(max_length=20)
    mentorship_choice = models.CharField(
        choices=MENTORSHIP_CHOICES, max_length=50
    )
    amount_paid = models.PositiveIntegerField(editable=False)
    is_paid = models.BooleanField(default=False)
    payment_reference = models.CharField(
        max_length=100, blank=True, null=True
    )
    applied_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Automatically set amount_paid based on mentorship_choice
        if self.mentorship_choice:
            self.amount_paid = MENTORSHIP_PRICES.get(self.mentorship_choice, 0)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.full_name} - {self.get_mentorship_choice_display()}"
    

# Testimonials Model

class Testimonial(models.Model):
    name = models.CharField(max_length=100)
    current_job = models.CharField(max_length=150)
    testimony = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.current_job}"


class GmailToken(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    access_token = models.TextField()
    refresh_token = models.TextField()
    token_expiry = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class NewsletterSubscription(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    university = models.CharField(max_length=150)
    current_role = models.CharField(max_length=100)
    whatsapp_line = models.CharField(max_length=20)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-subscribed_at']
    
    def __str__(self):
        return f"{self.full_name} - {self.email}"