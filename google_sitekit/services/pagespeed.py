from __future__ import annotations

from typing import Dict, Optional
import requests
from django.conf import settings


PSI_ENDPOINT = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"


class PageSpeedService:
    """
    PageSpeed Insights v5 (public, key-based). OAuth not required.
    Docs: pagespeedapi.runpagespeed
    """

    def __init__(self, api_key: Optional[str] = None):
        # Prefer explicit key, else settings var if present
        self.api_key = api_key or getattr(settings, "GOOGLE_PAGESPEED_API_KEY", None)

    def analyze_url(self, url: str, strategy: str = "mobile") -> Dict:
        """
        Returns key Lighthouse category scores and Core Web Vitals.
        strategy: 'mobile' | 'desktop'
        """
        params = {"url": url, "strategy": strategy, "category": ["performance", "accessibility", "seo", "best-practices"]}
        if self.api_key:
            params["key"] = self.api_key

        resp = requests.get(PSI_ENDPOINT, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        lighthouse = data.get("lighthouseResult", {})
        categories = lighthouse.get("categories", {}) or {}
        audits = lighthouse.get("audits", {}) or {}

        def pct(score):
            return round((score or 0) * 100)

        result = {
            "performance_score": pct(categories.get("performance", {}).get("score")),
            "accessibility_score": pct(categories.get("accessibility", {}).get("score")),
            "seo_score": pct(categories.get("seo", {}).get("score")),
            "best_practices_score": pct(categories.get("best-practices", {}).get("score")),
            "first_contentful_paint": audits.get("first-contentful-paint", {}).get("numericValue"),
            "largest_contentful_paint": audits.get("largest-contentful-paint", {}).get("numericValue"),
            "first_input_delay": audits.get("max-potential-fid", {}).get("numericValue"),
            "cumulative_layout_shift": audits.get("cumulative-layout-shift", {}).get("numericValue"),
        }
        return result

    def get_core_web_vitals(self, url: str, strategy: str = "mobile") -> Dict:
        """
        Convenience wrapper to return just CWV.
        """
        data = self.analyze_url(url, strategy=strategy)
        return {
            "lcp": data.get("largest_contentful_paint"),
            "fid": data.get("first_input_delay"),
            "cls": data.get("cumulative_layout_shift"),
        }
