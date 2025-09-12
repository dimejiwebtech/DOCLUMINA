# forms.py
from django import forms
from .models import MentorApplication, MentorshipApplication, NewsletterSubscription
from django.core.exceptions import ValidationError
from .mixins import RecaptchaV3Mixin

class ContactForm(RecaptchaV3Mixin, forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors duration-200',
            'placeholder': 'Enter your full name'
        })
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors duration-200',
            'placeholder': 'your.email@example.com'
        })
    )
    
    SUBJECT_CHOICES = [
        ('', 'Select a subject'),
        ('house_job', 'House Job Opportunities'),
        ('mentorship', 'Mentorship Program'),
        ('hospital_review', 'Hospital Reviews'),
        ('technical_support', 'Technical Support'),
        ('general_inquiry', 'General Inquiry'),
        ('other', 'Other'),
    ]
    
    subject = forms.ChoiceField(
        choices=SUBJECT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white transition-colors duration-200'
        })
    )
    
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-500 dark:placeholder-gray-400 transition-colors duration-200 resize-none',
            'rows': 5,
            'placeholder': 'Tell us how we can help you...'
        })
    )

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 2:
            raise forms.ValidationError("Name must be at least 2 characters long.")
        return name

    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message) < 10:
            raise forms.ValidationError("Message must be at least 10 characters long.")
        return message
    

class MentorApplicationForm(RecaptchaV3Mixin, forms.ModelForm):
    class Meta:
        model = MentorApplication
        fields = [
            "full_name", "email", "phone_number", "job_title", "professional_picture",
            "linkedin_link", "facebook_link", "area_of_expertise",
            "years_of_experience", "bio", "cv", "certificate"
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={
                'placeholder': 'Your Full Name',
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 transition-colors duration-200'
            }),
            "email": forms.EmailInput(attrs={
                'placeholder': 'Your Email Address',
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 transition-colors duration-200'
            }),
            "phone_number": forms.TextInput(attrs={
                'placeholder': 'Your Phone Number',
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 transition-colors duration-200'
            }),
            "job_title": forms.TextInput(attrs={
                'placeholder': 'Current Job Title (e.g., Senior Developer, Consultant)',
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 transition-colors duration-200'
            }),
            "linkedin_link": forms.URLInput(attrs={
                'placeholder': 'LinkedIn Profile URL',
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 transition-colors duration-200'
            }),
            "facebook_link": forms.URLInput(attrs={
                'placeholder': 'Facebook Profile URL (optional)',
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 transition-colors duration-200'
            }),
            "professional_picture": forms.FileInput(attrs={
                'class': 'cursor-pointer w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 dark:file:bg-gray-600 dark:file:text-gray-200 dark:hover:file:bg-gray-500 transition-colors duration-200',
                'accept': '.jpg,.jpeg,.png'
            }),
            "area_of_expertise": forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 transition-colors duration-200'
            }),
            "years_of_experience": forms.NumberInput(attrs={
                'placeholder': 'Years of Experience',
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 transition-colors duration-200',
                'min': '0'
            }),
            "bio": forms.Textarea(attrs={
                'placeholder': 'Tell us about your professional background, achievements, and what makes you a great mentor...',
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 placeholder-gray-500 dark:placeholder-gray-400 transition-colors duration-200 resize-none',
                'rows': '4'
            }),
            "cv": forms.FileInput(attrs={
                'class': 'cursor-pointer w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 dark:file:bg-gray-600 dark:file:text-gray-200 dark:hover:file:bg-gray-500 transition-colors duration-200',
                'accept': '.pdf,.doc,.docx'
            }),
            "certificate": forms.FileInput(attrs={
                'class': 'cursor-pointer w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-gray-100 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 dark:file:bg-gray-600 dark:file:text-gray-200 dark:hover:file:bg-gray-500 transition-colors duration-200',
                'accept': '.pdf,.jpg,.jpeg,.png'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Labels and help texts for new fields
        self.fields['job_title'].label = 'Current Job Title'
        self.fields['professional_picture'].label = 'Professional Picture'
        self.fields['linkedin_link'].label = 'LinkedIn Profile URL'
        self.fields['facebook_link'].label = 'Facebook Profile URL'

        self.fields['professional_picture'].help_text = 'Upload a clear professional photo (JPG, PNG).'
        self.fields['linkedin_link'].help_text = 'Link to your LinkedIn profile.'
        self.fields['facebook_link'].help_text = 'Optional: Link to your Facebook profile.'

        # Existing labels and help texts preserved
        self.fields['full_name'].label = 'Full Name'
        self.fields['email'].label = 'Email Address'
        self.fields['phone_number'].label = 'Phone Number'
        self.fields['area_of_expertise'].label = 'Area of Expertise'
        self.fields['years_of_experience'].label = 'Years of Experience'
        self.fields['bio'].label = 'Professional Bio'
        self.fields['cv'].label = 'CV/Resume'
        self.fields['certificate'].label = 'Professional Certificate'
        self.fields['cv'].help_text = 'Upload your CV/Resume (PDF, DOC, DOCX)'
        self.fields['certificate'].help_text = 'Upload your professional certificate (PDF, JPG, PNG)'
        self.fields['bio'].help_text = 'Minimum 100 characters. Tell us about your professional journey and what makes you a great mentor.'

    def clean_bio(self):
        """Validate bio length"""
        bio = self.cleaned_data.get('bio')
        if bio and len(bio.strip()) < 100:
            raise ValidationError("Professional bio must be at least 100 characters long.")
        return bio


    def clean(self):
        """Additional form-level validation"""
        cleaned_data = super().clean()
        
        # Check if someone is trying to submit exact same combination
        full_name = cleaned_data.get('full_name')
        email = cleaned_data.get('email')
        phone_number = cleaned_data.get('phone_number')
        
        if full_name and email and phone_number:
            # Check for exact combination match
            if MentorApplication.objects.filter(
                full_name__iexact=full_name.strip(),
                email__iexact=email.strip(),
                phone_number=phone_number.strip()
            ).exists():
                raise ValidationError("This exact application has already been submitted.")
        
        return cleaned_data

class MentorshipApplicationForm(RecaptchaV3Mixin, forms.ModelForm):
    class Meta:
        model = MentorshipApplication
        fields = [
            "full_name",
            "email",
            "phone_number",
            "mentorship_choice",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={
                'placeholder': 'Your Full Name',
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            "email": forms.EmailInput(attrs={
                'placeholder': 'Your Email',
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            "phone_number": forms.TextInput(attrs={
                'placeholder': 'Your Phone Number',
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            "mentorship_choice": forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
        }

class NewsletterForm(RecaptchaV3Mixin, forms.ModelForm):
    class Meta:
        model = NewsletterSubscription
        fields = ['full_name', 'email', 'university', 'current_role', 'whatsapp_line']
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'Your Full Name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'your.email@example.com'
            }),
            'university': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'University Name'
            }),
            'current_role': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': 'e.g., Medical Student, Doctor, Nurse'
            }),
            'whatsapp_line': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
                'placeholder': '+234xxxxxxxxxx'
            }),
        }