from __future__ import annotations

import base64
import hashlib
import os
from dataclasses import dataclass
from typing import Optional, Tuple
from urllib.parse import urlencode

import requests
from django.conf import settings
from django.utils import timezone

from dotenv import load_dotenv
load_dotenv()


AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"

# Fallback scopes if settings.GOOGLE_APIS isn't present or lacks these keys
DEFAULT_ANALYTICS_SCOPE = "https://www.googleapis.com/auth/analytics.readonly"
DEFAULT_SEARCH_CONSOLE_SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _pkce_pair() -> Tuple[str, str]:
    """Generate (code_verifier, code_challenge) per RFC 7636, S256."""
    verifier = _b64url(os.urandom(32))  # 43–128 chars post-encoding
    challenge = _b64url(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


@dataclass
class TokenResult:
    access_token: str
    refresh_token: Optional[str]
    expires_in: int
    token_type: str


class GoogleAuthService:
    """
    Encapsulates Google OAuth 2.0 (Authorization Code + PKCE) for server-side Django.
    Views must call this service instead of performing raw HTTP.
    """

    def __init__(self):
        self.client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        self.redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI

        apis = getattr(settings, "GOOGLE_APIS", {})
        self.scopes = [
            apis.get("ANALYTICS", DEFAULT_ANALYTICS_SCOPE),
            apis.get("SEARCH_CONSOLE", DEFAULT_SEARCH_CONSOLE_SCOPE),
        ]

    # ---------- Public API ----------

    def get_authorization_url(self, request) -> str:
        """
        Build the Google consent URL and stash state + PKCE verifier in session.
        """
        state = _b64url(os.urandom(24))
        code_verifier, code_challenge = _pkce_pair()

        request.session["gs_state"] = state
        request.session["gs_code_verifier"] = code_verifier
        request.session.modified = True

        params = {
            "response_type": "code",
            "client_id": self.client_id,
            "redirect_uri": self.redirect_uri,
            "scope": " ".join(self.scopes),
            "state": state,
            "access_type": "offline",      # enables refresh tokens where permitted
            "prompt": "consent",           # ensures refresh_token on re-consent
            "include_granted_scopes": "true",
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
        return f"{AUTH_ENDPOINT}?{urlencode(params)}"

    def exchange_code_for_tokens(self, code: str, code_verifier: str) -> TokenResult:
        """
        Exchange authorization code for tokens.
        """
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "code_verifier": code_verifier,
        }
        # Confidential web clients may also send client_secret (compatible with PKCE).
        if self.client_secret:
            data["client_secret"] = self.client_secret

        resp = requests.post(TOKEN_ENDPOINT, data=data, timeout=20)
        resp.raise_for_status()
        payload = resp.json()

        return TokenResult(
            access_token=payload["access_token"],
            refresh_token=payload.get("refresh_token"),
            expires_in=int(payload.get("expires_in", 3600)),
            token_type=payload.get("token_type", "Bearer"),
        )

    def refresh_access_token(self, refresh_token: str) -> TokenResult:
        """
        Refresh an expired access token.
        """
        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": self.client_id,
        }
        if self.client_secret:
            data["client_secret"] = self.client_secret

        resp = requests.post(TOKEN_ENDPOINT, data=data, timeout=20)
        resp.raise_for_status()
        payload = resp.json()

        return TokenResult(
            access_token=payload["access_token"],
            refresh_token=payload.get("refresh_token", refresh_token),
            expires_in=int(payload.get("expires_in", 3600)),
            token_type=payload.get("token_type", "Bearer"),
        )

    # ---------- Helpers for persistence ----------

    @staticmethod
    def compute_expiry_ts(expires_in: int):
        """
        Return expiry with a 60s safety skew.
        """
        return timezone.now() + timezone.timedelta(seconds=max(0, expires_in - 60))

    def ensure_fresh_access_token(self, settings_obj) -> str:
        """
        Returns a valid access token, refreshing (and persisting) if needed.
        Keeps API services lean and DRY.
        """
        if not settings_obj.google_access_token or settings_obj.is_token_expired:
            if not settings_obj.google_refresh_token:
                raise RuntimeError("No refresh token available. Reconnect Google Site Kit.")
            refreshed = self.refresh_access_token(settings_obj.google_refresh_token)
            settings_obj.google_access_token = refreshed.access_token
            if refreshed.refresh_token:
                settings_obj.google_refresh_token = refreshed.refresh_token
            settings_obj.token_expires_at = self.compute_expiry_ts(refreshed.expires_in)
            settings_obj.save(update_fields=[
                "google_access_token", "google_refresh_token", "token_expires_at", "updated_at"
            ])
        return settings_obj.google_access_token
