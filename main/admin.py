from django import forms
from django.contrib import admin, messages
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from .models import GmailToken, MentorApplication, MentorshipApplication, Testimonial



class RejectionReasonForm(forms.Form):
    _selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
    reason = forms.CharField(
        label="Rejection Reason",
        widget=forms.Textarea(attrs={"rows": 4, "style": "width: 100%;"}),
        help_text="This reason will be included in the rejection email to applicants.",
    )


@admin.register(MentorApplication)
class MentorApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "full_name", "email", "area_of_expertise",
        "approved", "pending", "rejected", "submitted_at"
    )
    list_filter = ("approved", "pending", "rejected", "area_of_expertise")
    actions = ["approve_applications", "reject_applications"]

    def approve_applications(self, request, queryset):
        for application in queryset:
            if not application.approved:
                application.approved = True
                application.pending = False
                application.rejected = False
                application.save()

                # Send approval email
                send_mail(
                    subject="Doclumina Mentorship Application Approved",
                    message=(
                        f"Dear {application.full_name},\n\n"
                        "Your mentor application has been approved! "
                        "Please join our mentorship group using this link: [WhatsApp/Telegram link here]\n\n"
                        "Welcome onboard!\n\n- Doclumina Team"
                    ),
                    from_email="msgdoclumina@gmail.com",
                    recipient_list=[application.email],
                    fail_silently=False
                )

        self.message_user(request, "Selected applications have been approved.")

    approve_applications.short_description = "Approve selected mentor applications"

    def reject_applications(self, request, queryset):
        if "apply" in request.POST:
            form = RejectionReasonForm(request.POST)
            if form.is_valid():
                reason = form.cleaned_data["reason"]
                selected_ids = request.POST.getlist("_selected_action")
                applications = MentorApplication.objects.filter(pk__in=selected_ids)

                for application in applications:
                    application.approved = False
                    application.pending = False
                    application.rejected = True
                    application.save()

                    # Send rejection email
                    send_mail(
                        subject="Doclumina Mentorship Application Declined",
                        message=(
                            f"Dear {application.full_name},\n\n"
                            "We regret to inform you that your mentor application has been declined.\n\n"
                            f"Reason: {reason}\n\n"
                            "Thank you for your interest.\n\n- Doclumina Team"
                        ),
                        from_email="msgdoclumina@gmail.com",
                        recipient_list=[application.email],
                        fail_silently=False
                    )

                self.message_user(request, "Selected applications have been rejected.")
                return redirect(request.get_full_path())
        else:
            form = RejectionReasonForm(initial={"_selected_action": queryset.values_list("pk", flat=True)})

        return render(
            request,
            "main/mentors/reject_confirmation.html",
            {
                "applications": queryset,
                "form": form,
                "title": "Provide Rejection Reason"
            }
        )

    reject_applications.short_description = "Reject selected mentor applications"


@admin.register(MentorshipApplication)
class MentorshipApplicationAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 
        'email', 
        'phone_number', 
        'display_programs', 
        'total_amount', 
        'payment_status', 
        'applied_at'
    ]
    list_filter = ['is_paid', 'applied_at']
    search_fields = ['full_name', 'email', 'phone_number']
    readonly_fields = ['total_amount', 'applied_at', 'payment_confirmed_at']
    ordering = ['-applied_at']
    
    fieldsets = (
        ('Applicant Information', {
            'fields': ('full_name', 'email', 'phone_number')
        }),
        ('Mentorship Details', {
            'fields': ('mentorship_programs', 'total_amount')
        }),
        ('Payment Information', {
            'fields': ('is_paid', 'payment_reference', 'payment_confirmed_at')
        }),
        ('Timestamps', {
            'fields': ('applied_at',),
            'classes': ('collapse',)
        }),
    )
    
    def display_programs(self, obj):
        """Display selected programs in admin"""
        programs = obj.get_program_names()
        return ', '.join(programs) if programs else 'None'
    display_programs.short_description = 'Selected Programs'
    
    def payment_status(self, obj):
        """Display payment status with colored indicator"""
        if obj.is_paid:
            return format_html(
                '<span style="color: #10b981; font-weight: bold;">✓ Paid</span>'
            )
        return format_html(
            '<span style="color: #ef4444; font-weight: bold;">✗ Pending</span>'
        )
    payment_status.short_description = 'Status'
    
    def get_queryset(self, request):
        """Optimize queries"""
        return super().get_queryset(request).select_related()

@admin.register(Testimonial)
class Testimonial(admin.ModelAdmin):
    list_display = ("name", "current_job")

@admin.register(GmailToken)
class GmailTokenAdmin(admin.ModelAdmin):
    list_display = ['id', 'token_expiry', 'created_at']
    readonly_fields = ['access_token', 'refresh_token']