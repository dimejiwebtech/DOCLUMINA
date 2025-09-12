from __future__ import annotations

from datetime import date
from typing import Dict, List

from django.utils.dateparse import parse_date

from .base import BaseGoogleService

SC_BASE = "https://www.googleapis.com/webmasters/v3"


class SearchConsoleService(BaseGoogleService):
    """
    Google Search Console - Search Analytics (v3).
    Uses the 'query' method under sites/{siteUrl}/searchAnalytics.
    Docs: POST /sites/siteUrl/searchAnalytics/query
    """

    def __init__(self, settings_obj):
        super().__init__(settings_obj)
        if not settings_obj.search_console_site_url:
            raise ValueError("Search Console site URL is not configured.")
        self.site_url = settings_obj.search_console_site_url

    def get_search_analytics(self, start_date, end_date) -> Dict:
        """
        Returns totals for clicks, impressions, ctr, position over the date range.
        """
        url = f"{SC_BASE}/sites/{self.site_url}/searchAnalytics/query"
        body = {
            "startDate": self._d(start_date),
            "endDate": self._d(end_date),
            "dimensions": ["date"],
            "rowLimit": 1_000,
        }
        data = self._post(url, json=body)
        clicks = impressions = 0
        ctr_sum = position_sum = 0.0
        n = 0
        for row in data.get("rows", []):
            c = int(row.get("clicks", 0))
            i = int(row.get("impressions", 0))
            clicks += c
            impressions += i
            ctr_sum += float(row.get("ctr", 0.0))
            position_sum += float(row.get("position", 0.0))
            n += 1

        avg_ctr = (ctr_sum / n * 100.0) if n else 0.0  # convert to %
        avg_pos = (position_sum / n) if n else 0.0
        return {"clicks": clicks, "impressions": impressions, "ctr": avg_ctr, "position": avg_pos}

    def get_top_queries(self, start_date, end_date, limit: int = 10) -> List[Dict]:
        url = f"{SC_BASE}/sites/{self.site_url}/searchAnalytics/query"
        body = {
            "startDate": self._d(start_date),
            "endDate": self._d(end_date),
            "dimensions": ["query"],
            "rowLimit": limit,
            "orderBy": [{"field": "clicks", "descending": True}],
        }
        data = self._post(url, json=body)
        rows = []
        for r in data.get("rows", []):
            rows.append({
                "query": r["keys"][0],
                "clicks": int(r.get("clicks", 0)),
                "impressions": int(r.get("impressions", 0)),
                "ctr": float(r.get("ctr", 0.0)) * 100.0,   # to %
                "position": float(r.get("position", 0.0)),
            })
        return rows

    def get_top_pages(self, start_date, end_date, limit: int = 10) -> List[Dict]:
        url = f"{SC_BASE}/sites/{self.site_url}/searchAnalytics/query"
        body = {
            "startDate": self._d(start_date),
            "endDate": self._d(end_date),
            "dimensions": ["page"],
            "rowLimit": limit,
            "orderBy": [{"field": "clicks", "descending": True}],
        }
        data = self._post(url, json=body)
        rows = []
        for r in data.get("rows", []):
            rows.append({
                "page": r["keys"][0],
                "clicks": int(r.get("clicks", 0)),
                "impressions": int(r.get("impressions", 0)),
                "ctr": float(r.get("ctr", 0.0)) * 100.0,   # to %
                "position": float(r.get("position", 0.0)),
            })
        return rows

    # ---------- utils ----------
    @staticmethod
    def _d(value) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, date):
            return value.isoformat()
        parsed = parse_date(str(value).split(" ")[0])
        return parsed.isoformat() if parsed else str(value)
