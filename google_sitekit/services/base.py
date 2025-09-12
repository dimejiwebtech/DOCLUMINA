from __future__ import annotations

import requests
from typing import Any, Dict, Optional

from django.conf import settings
from ..models import SiteKitSettings
from .auth import GoogleAuthService


class BaseGoogleService:
    """
    Minimal helper for authenticated Google API requests.
    Ensures a fresh access token (via Phase 2) and provides request helpers.
    """

    def __init__(self, settings_obj: SiteKitSettings):
        self.settings_obj = settings_obj
        self._auth = GoogleAuthService()
        self._access_token = self._auth.ensure_fresh_access_token(settings_obj)

    @property
    def headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._access_token}"}

    def _get(self, url: str, params: Optional[Dict[str, Any]] = None, timeout: int = 20) -> Dict[str, Any]:
        resp = requests.get(url, headers=self.headers, params=params or {}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()

    def _post(self, url: str, json: Optional[Dict[str, Any]] = None, timeout: int = 25) -> Dict[str, Any]:
        resp = requests.post(url, headers=self.headers, json=json or {}, timeout=timeout)
        resp.raise_for_status()
        return resp.json()
