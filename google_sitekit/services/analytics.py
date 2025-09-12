from __future__ import annotations

from datetime import date
from typing import Dict, List

from django.utils.dateparse import parse_date

from .base import BaseGoogleService

ANALYTICS_BASE = "https://analyticsdata.googleapis.com/v1"


class AnalyticsService(BaseGoogleService):
    """
    GA4 Reporting (v1). Uses runReport and runRealtimeReport with a minimal, safe subset of
    dimensions/metrics suitable for dashboards.
    Docs: https://developers.google.com/analytics/devguides/reporting/data/v1
    """

    def __init__(self, settings_obj):
        super().__init__(settings_obj)
        if not settings_obj.analytics_property_id:
            raise ValueError("GA4 Property ID is not configured.")
        self.property = f"properties/{settings_obj.analytics_property_id}"

    # ---------- Realtime ----------

    def get_realtime_data(self) -> Dict:
        """
        Returns active users (last 30–60 minutes, per GA limits).
        """
        url = f"{ANALYTICS_BASE}/{self.property}:runRealtimeReport"
        body = {
            "metrics": [{"name": "activeUsers"}],
            # keep it light; you can add dimensions later (e.g., deviceCategory)
            "limit": 1,
        }
        data = self._post(url, json=body)
        value = 0
        if data.get("rows"):
            value = int(float(data["rows"][0]["metricValues"][0]["value"]))
        return {"active_users": value}

    # ---------- Overview (date range) ----------

    def get_overview_data(self, start_date, end_date) -> Dict:
        """
        Sessions, users, views, average session duration, bounce rate.
        """
        url = f"{ANALYTICS_BASE}/{self.property}:runReport"
        body = {
            "dateRanges": [{"startDate": self._d(start_date), "endDate": self._d(end_date)}],
            "metrics": [
                {"name": "sessions"},
                {"name": "totalUsers"},
                {"name": "screenPageViews"},
                {"name": "averageSessionDuration"},
                {"name": "bounceRate"},
            ],
            "limit": 1,
        }
        data = self._post(url, json=body)
        metrics = {"sessions": 0, "users": 0, "pageviews": 0, "avg_session_duration": 0.0, "bounce_rate": 0.0}
        if data.get("rows"):
            mv = data["rows"][0]["metricValues"]
            metrics.update(
                sessions=int(float(mv[0]["value"] or 0)),
                users=int(float(mv[1]["value"] or 0)),
                pageviews=int(float(mv[2]["value"] or 0)),
                avg_session_duration=float(mv[3]["value"] or 0.0),
                bounce_rate=float(mv[4]["value"] or 0.0),
            )
        return metrics

    def get_top_pages(self, start_date, end_date, limit: int = 10) -> List[Dict]:
        """
        Most viewed pages by path with pageviews.
        """
        url = f"{ANALYTICS_BASE}/{self.property}:runReport"
        body = {
            "dateRanges": [{"startDate": self._d(start_date), "endDate": self._d(end_date)}],
            "dimensions": [{"name": "pagePath"}],
            "metrics": [{"name": "screenPageViews"}],
            "orderBys": [{"metric": {"metricName": "screenPageViews"}, "desc": True}],
            "limit": limit,
        }
        data = self._post(url, json=body)
        rows = []
        for r in data.get("rows", []):
            rows.append({"path": r["dimensionValues"][0]["value"], "pageviews": int(float(r["metricValues"][0]["value"]))})
        return rows

    def get_traffic_sources(self, start_date, end_date, limit: int = 10) -> List[Dict]:
        """
        Acquisition by default channel group.
        """
        url = f"{ANALYTICS_BASE}/{self.property}:runReport"
        body = {
            "dateRanges": [{"startDate": self._d(start_date), "endDate": self._d(end_date)}],
            "dimensions": [{"name": "sessionDefaultChannelGroup"}],
            "metrics": [{"name": "sessions"}],
            "orderBys": [{"metric": {"metricName": "sessions"}, "desc": True}],
            "limit": limit,
        }
        data = self._post(url, json=body)
        rows = []
        for r in data.get("rows", []):
            rows.append({"channel": r["dimensionValues"][0]["value"], "sessions": int(float(r["metricValues"][0]["value"]))})
        return rows
    
    def get_time_series(self, start_date, end_date, metric: str = "sessions", limit: int = 100):
        """Return daily time-series for a single metric between start_date and end_date.
        Result: {'labels': ['2025-07-01', ...], 'values': [123, ...]}
        """
        url = f"{ANALYTICS_BASE}/{self.property}:runReport"
        body = {
            "dateRanges": [{"startDate": self._d(start_date), "endDate": self._d(end_date)}],
            "dimensions": [{"name": "date"}],
            "metrics": [{"name": metric}],
            "limit": limit,
            "orderBys": [{"dimension": {"dimensionName": "date"}, "desc": False}],
        }
        data = self._post(url, json=body)
        labels = []
        values = []
        for row in data.get("rows", []):
            # date is returned in dimensionValues[0].value as YYYYMMDD or YYYY-MM-DD depending on API
            raw_date = row["dimensionValues"][0]["value"]
            # normalize common formats
            if len(raw_date) == 8 and raw_date.isdigit():  # YYYYMMDD
                label = f"{raw_date[0:4]}-{raw_date[4:6]}-{raw_date[6:8]}"
            else:
                label = raw_date
            labels.append(label)
            mv = row.get("metricValues", [{}])
            val = mv[0].get("value", 0) if mv else 0
            # ensure numeric type
            try:
                v = int(float(val))
            except Exception:
                try:
                    v = float(val)
                except Exception:
                    v = 0
            values.append(v)
        return {"labels": labels, "values": values}


    # ---------- utils ----------
    @staticmethod
    def _d(value) -> str:
        if isinstance(value, str):
            # accept 'YYYY-MM-DD' strings from callers
            return value
        if isinstance(value, date):
            return value.isoformat()
        # django timezone.now() etc.
        parsed = parse_date(str(value).split(" ")[0])
        return parsed.isoformat() if parsed else str(value)
