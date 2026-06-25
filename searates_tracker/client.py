"""
Core SeaRates API client.
"""

from __future__ import annotations

import logging
from typing import Any

import requests

from .exceptions import (
    SeaRatesAuthError,
    SeaRatesException,
    SeaRatesNotFoundError,
    SeaRatesRateLimitError,
    SeaRatesServerError,
)
from .models import (
    AirTrackingResult,
    Carrier,
    ParcelTrackingResult,
    RailTrackingResult,
    RoadTrackingResult,
    SeaTrackingResult,
    TrackingResult,
)

logger = logging.getLogger(__name__)

# Base URLs
BASE_WWW = "https://www.searates.com/tracking-system"
BASE_TRACKING = "https://tracking.searates.com"

# Error messages that map to specific exceptions
RATE_LIMIT_MSGS = {"API_KEY_LIMIT_REACHED", "API_KEY_RATE_LIMIT"}
AUTH_ERROR_MSGS = {"API_KEY_WRONG", "API_KEY_ACCESS_DENIED", "API_KEY_EXPIRED", "UNAUTHORIZED"}
NOT_FOUND_MSGS = {"WRONG_NUMBER", "WRONG_SEALINE", "WRONG_RAILWAY_COMPANY"}


class SeaRatesClient:
    """
    عميل SeaRates لتتبع جميع أنواع الشحنات.

    Args:
        api_key: مفتاح API اختياري (يزيد حدود الطلبات).
        timeout: المهلة الزمنية للطلبات بالثواني.
        language: لغة النتائج (en, ar, ru, zh, es, de...).

    Usage:
        >>> client = SeaRatesClient()
        >>> result = client.track_sea("MEDU3288655", sealine="MSCU")
        >>> print(f"Status: {result.status}")
        >>> print(f"Events: {len(result.events)}")

        >>> carriers = client.get_carriers()
        >>> maersk = [c for c in carriers if "Maersk" in c.name]
    """

    def __init__(
        self,
        api_key: str | None = None,
        timeout: int = 30,
        language: str = "en",
    ):
        self.api_key = api_key
        self.timeout = timeout
        self.language = language
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": (
                "SeaRatesTracker/1.0 (Python; +https://github.com/benchaa/searates-tracker)"
            ),
            "Accept": "application/json",
            "Accept-Language": language,
            "Origin": "https://www.searates.com",
            "Referer": "https://www.searates.com/container/tracking",
            "X-Referer": "https://www.searates.com/",
        })
        if api_key:
            self._session.headers["Authorization"] = f"Bearer {api_key}"

    # ------------------------------------------------------------------
    # 🚢 Sea / Container Tracking
    # ------------------------------------------------------------------

    def track_sea(
        self,
        number: str,
        sealine: str | None = None,
        tracking_type: str | None = None,
        route: bool = True,
    ) -> SeaTrackingResult:
        """
        تتبع حاوية بحرية أو بوليصة شحن.

        Args:
            number: رقم الحاوية أو بوليصة الشحن.
            sealine: كود SCAC لشركة الشحن (مثلاً ``MAEU``, ``MSCU``, ``HLCU``).
            tracking_type: نوع التتبع: ``ct`` حاوية، ``bl`` بوليصة، ``bk`` حجز.
            route: تفعيل تتبع المسار الكامل.

        Returns:
            SeaTrackingResult: نتيجة التتبع مع كل التفاصيل.

        Raises:
            SeaRatesRateLimitError: تجاوزت حد الطلبات.
            SeaRatesNotFoundError: رقم الحاوية غير موجود.
        """
        params: dict[str, Any] = {
            "number": number,
            "route": str(route).lower(),
            "last_successful": "false",
        }
        if sealine:
            params["sealine"] = sealine
        if tracking_type:
            params["type"] = tracking_type

        response = self._get(f"{BASE_WWW}/reverse/tracking", params=params)
        self._raise_for_error(response)
        return SeaTrackingResult.from_api_response(response)

    # ------------------------------------------------------------------
    # ✈️ Air Cargo Tracking
    # ------------------------------------------------------------------

    def track_air(
        self,
        number: str,
    ) -> AirTrackingResult:
        """
        تتبع شحنة جوية.

        Args:
            number: رقم الشحنة الجوية (AWB).

        Returns:
            AirTrackingResult: نتيجة التتبع.
        """
        params = {
            "number": number,
            "last_successful": "false",
        }
        response = self._get(f"{BASE_WWW}/air", params=params)
        self._raise_for_error(response)
        return AirTrackingResult.from_api_response(response)

    # ------------------------------------------------------------------
    # 📦 Parcel Tracking
    # ------------------------------------------------------------------

    def track_parcel(
        self,
        number: str,
    ) -> ParcelTrackingResult:
        """
        تتبع طرد بريدي (يدعم UPS, FedEx, DHL, USPS...).

        لا يحتاج API key — يعمل بدون مصادقة.

        Args:
            number: رقم التتبع البريدي.

        Returns:
            ParcelTrackingResult: نتيجة التتبع مع اسم شركة البريد تلقائياً.
        """
        params = {
            "api_key": "1",
            "path": "true",
            "number": number,
        }
        response = self._get(f"{BASE_TRACKING}/parcel", params=params)
        return ParcelTrackingResult.from_api_response(response)

    # ------------------------------------------------------------------
    # 🚂 Rail Tracking
    # ------------------------------------------------------------------

    def track_rail(
        self,
        number: str,
    ) -> RailTrackingResult:
        """
        تتبع شحنة سكة حديدية.

        لا يحتاج API key.

        Args:
            number: رقم الشحنة.

        Returns:
            RailTrackingResult: نتيجة التتبع.
        """
        params = {
            "api_key": "1",
            "number": number,
        }
        response = self._get(f"{BASE_TRACKING}/rail", params=params)
        self._raise_for_error(response)
        return RailTrackingResult.from_api_response(response)

    # ------------------------------------------------------------------
    # 🚛 Road Tracking
    # ------------------------------------------------------------------

    def track_road(
        self,
        number: str,
    ) -> RoadTrackingResult:
        """
        تتبع شحنة نقل بري.

        لا يحتاج API key.

        Args:
            number: رقم الشحنة.

        Returns:
            RoadTrackingResult: نتيجة التتبع.
        """
        params = {
            "api_key": "1",
            "path": "true",
            "number": number,
        }
        response = self._get(f"{BASE_TRACKING}/road", params=params)
        self._raise_for_error(response)
        return RoadTrackingResult.from_api_response(response)

    # ------------------------------------------------------------------
    # 🏷️ Carriers / Sealines
    # ------------------------------------------------------------------

    def get_carriers(self) -> list[Carrier]:
        """
        جلب قائمة جميع شركات الشحن البحري المدعومة.

        لا يحتاج API key — يعمل بدون مصادقة.

        Returns:
            list[Carrier]: قائمة شركات الشحن (240+ شركة).
        """
        response = self._get(f"{BASE_TRACKING}/v5/carriers")
        data = response.get("data", [])
        return [Carrier.from_api(c) for c in data]

    def find_carrier(self, query: str) -> list[Carrier]:
        """
        البحث عن شركة شحن بالاسم أو كود SCAC.

        Args:
            query: جزء من اسم الشركة أو كود SCAC.

        Returns:
            list[Carrier]: الشركات المطابقة.
        """
        carriers = self.get_carriers()
        q = query.lower()
        results = []
        for c in carriers:
            if (
                q in c.name.lower()
                or any(q in scac.lower() for scac in c.scac_codes)
                or any(q in prefix.lower() for prefix in c.prefixes)
            ):
                results.append(c)
        return results

    def find_carrier_by_prefix(self, container_number: str) -> Carrier | None:
        """
        محاولة تحديد شركة الشحن من بادئة رقم الحاوية.

        Args:
            container_number: رقم الحاوية (مثلاً ``MAEU9168137``).

        Returns:
            Carrier | None: شركة الشحن المطابقة أو None.
        """
        # Extract prefix (first 3-4 uppercase letters)
        prefix_3 = container_number[:3].upper()
        prefix_4 = container_number[:4].upper()

        carriers = self.get_carriers()
        for c in carriers:
            for p in c.prefixes:
                p_upper = p.upper()
                if p_upper == prefix_3 or p_upper == prefix_4:
                    return c
        return None

    # ------------------------------------------------------------------
    # 📊 Analytics
    # ------------------------------------------------------------------

    def get_analytics(self) -> dict:
        """
        جلب تحليلات التتبع (للحسابات المسجلة).

        Returns:
            dict: بيانات التحليلات.
        """
        return self._get(f"{BASE_WWW}/analytics")

    # ------------------------------------------------------------------
    # 🔔 Notifications
    # ------------------------------------------------------------------

    def get_notifications(self) -> dict:
        """
        جلب الإشعارات (للحسابات المسجلة).

        Returns:
            dict: بيانات الإشعارات.
        """
        return self._post(f"{BASE_WWW}/notifications")

    # ------------------------------------------------------------------
    # 🌐 Public URL builder
    # ------------------------------------------------------------------

    @staticmethod
    def get_public_tracking_url(number: str, tracking_type: str = "ct") -> str:
        """
        بناء رابط التتبع العام في موقع SeaRates.

        Args:
            number: رقم الحاوية.
            tracking_type: ``ct`` حاوية، ``bl`` بوليصة.

        Returns:
            str: رابط التتبع المباشر.
        """
        return f"https://www.searates.com/container/tracking/?number={number}&type={tracking_type}"

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(self, url: str, params: dict | None = None) -> dict:
        """Make a GET request and return JSON."""
        logger.debug("GET %s params=%s", url, params)
        resp = self._session.get(url, params=params, timeout=self.timeout)
        return self._handle_response(resp)

    def _post(self, url: str, json_data: dict | None = None) -> dict:
        """Make a POST request and return JSON."""
        logger.debug("POST %s data=%s", url, json_data)
        resp = self._session.post(url, json=json_data, timeout=self.timeout)
        return self._handle_response(resp)

    def _handle_response(self, resp: requests.Response) -> dict:
        """Parse response and handle HTTP errors."""
        if resp.status_code >= 500:
            raise SeaRatesServerError(
                message=f"Server error: HTTP {resp.status_code}",
                raw_response={"http_status": resp.status_code},
            )

        try:
            data = resp.json()
        except ValueError:
            data = {"status": "error", "message": resp.text[:200]}

        # Some endpoints use 'success' instead of 'status'
        api_status = data.get("status") or ("success" if data.get("success") else "error")

        if api_status == "error":
            msg = data.get("message") or data.get("status_code", "Unknown error")
            self._raise_for_error(data)

        return data

    @staticmethod
    def _raise_for_error(response: dict) -> None:
        """Raise appropriate exception based on API error message."""
        msg = response.get("message") or response.get("status_code", "")
        msg_upper = msg.upper()

        if any(m in msg_upper for m in RATE_LIMIT_MSGS):
            raise SeaRatesRateLimitError(message=msg, raw_response=response)
        if any(m in msg_upper for m in AUTH_ERROR_MSGS):
            raise SeaRatesAuthError(message=msg, raw_response=response)
        if any(m in msg_upper for m in NOT_FOUND_MSGS):
            raise SeaRatesNotFoundError(message=msg, raw_response=response)
        if msg_upper and msg_upper != "OK":
            raise SeaRatesException(message=msg, raw_response=response)

    def __repr__(self) -> str:
        auth = "with API key" if self.api_key else "public"
        return f"SeaRatesClient(auth={auth})"
