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
    list_display = ("full_name", "email", "mentorship_choice", "amount_paid", "is_paid", "applied_at")
    list_filter = ("is_paid", "mentorship_choice")


@admin.register(Testimonial)
class Testimonial(admin.ModelAdmin):
    list_display = ("name", "current_job")

@admin.register(GmailToken)
class GmailTokenAdmin(admin.ModelAdmin):
    list_display = ['id', 'token_expiry', 'created_at']
    readonly_fields = ['access_token', 'refresh_token']