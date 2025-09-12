from main.models import CookieConsent


def cookie_consent(request):
    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key
    
    try:
        consent = CookieConsent.objects.get(session_key=session_key)
        has_consent = True
    except CookieConsent.DoesNotExist:
        consent = None
        has_consent = False
    
    return {
        'cookie_consent': consent,
        'show_cookie_banner': not has_consent
    }