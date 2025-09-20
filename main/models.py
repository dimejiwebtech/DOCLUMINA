from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
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
    "house_job": 30000,
    "nigerian_residency": 100000,
    "usmle_canada": 100000,
    "amc_plab": 100000,
    "mph": 100000,
    "express_entry": 100000,
    "non_clinical": 100000,
    "mdcn_exam": 100000,
}

MENTORSHIP_DESCRIPTIONS = {
    "house_job": "Get guidance on securing house job positions in top Nigerian hospitals and excel during your internship.",
    "nigerian_residency": "Navigate the Nigerian residency application process with expert mentorship and insider tips.",
    "usmle_canada": "Master USMLE Step 1, 2, 3 and Canadian residency match with personalized guidance.",
    "amc_plab": "Ace AMC and PLAB exams for Australian and UK medical practice with proven strategies.",
    "mph": "Successfully apply to top MPH programs in US, UK, and Canada with tailored application support.",
    "express_entry": "Navigate Canadian immigration through Express Entry with medical professional expertise.",
    "non_clinical": "Transition to non-clinical healthcare roles including consulting, pharma, and health tech.",
    "mdcn_exam": "Pass MDCN examinations with comprehensive study plans and expert guidance.",
}

# WhatsApp group links for each mentorship program
MENTORSHIP_WHATSAPP_LINKS = {
    "house_job": "https://chat.whatsapp.com/housejob-group-link",
    "nigerian_residency": "https://chat.whatsapp.com/nigerian-residency-group-link",
    "usmle_canada": "https://chat.whatsapp.com/usmle-canada-group-link",
    "amc_plab": "https://chat.whatsapp.com/amc-plab-group-link",
    "mph": "https://chat.whatsapp.com/mph-group-link",
    "express_entry": "https://chat.whatsapp.com/express-entry-group-link",
    "non_clinical": "https://chat.whatsapp.com/non-clinical-group-link",
    "mdcn_exam": "https://chat.whatsapp.com/mdcn-exam-group-link",
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
        if self.mentorship_programs:
            self.total_amount = sum(
                MENTORSHIP_PRICES.get(program, 0) 
                for program in self.mentorship_programs
            )
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


class MentorshipApplication(models.Model):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone_number = models.CharField(validators=[phone_regex], max_length=17)
    mentorship_programs = models.JSONField(
        default=list,
        help_text="List of selected mentorship programs"
    )
    total_amount = models.PositiveIntegerField(editable=False, default=0)
    is_paid = models.BooleanField(default=False)
    payment_reference = models.CharField(
        max_length=100, blank=True, null=True
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    payment_confirmed_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-applied_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_paid']),
        ]

    def save(self, *args, **kwargs):
        # Calculate total amount based on selected programs
        if self.mentorship_programs:
            self.total_amount = sum(
                MENTORSHIP_PRICES.get(program, 0) 
                for program in self.mentorship_programs
            )
        super().save(*args, **kwargs)

    def __str__(self):
        programs = ', '.join([
            dict(MENTORSHIP_CHOICES).get(prog, prog) 
            for prog in self.mentorship_programs
        ])
        return f"{self.full_name} - {programs}"
    
    def get_program_names(self):
        """Return human-readable program names"""
        return [
            dict(MENTORSHIP_CHOICES).get(prog, prog) 
            for prog in self.mentorship_programs
        ]
    
    def get_whatsapp_links(self):
        """Return WhatsApp links for selected programs"""
        return [
            {
                'program': dict(MENTORSHIP_CHOICES).get(prog, prog),
                'link': MENTORSHIP_WHATSAPP_LINKS.get(prog, '#')
            }
            for prog in self.mentorship_programs
        ]
    

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