from django_recaptcha.fields import ReCaptchaField
from django_recaptcha.widgets import ReCaptchaV3

class RecaptchaV3Mixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['captcha'] = ReCaptchaField(
            widget=ReCaptchaV3(
                action='submit'
            )
        )