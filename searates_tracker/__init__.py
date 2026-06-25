"""
SeaRates Tracker — تتبع الحاويات والشحنات عبر SeaRates API
============================================================

مكتبة بايثون شاملة لتتبع جميع أنواع الشحنات عبر SeaRates API.
تدعم: الحاويات البحرية، الشحن الجوي، الطرود البريدية، السكك الحديدية، النقل البري.

Author: Mohammed Benchaa
License: MIT
"""

from .client import SeaRatesClient
from .exceptions import (
    SeaRatesException,
    SeaRatesAuthError,
    SeaRatesRateLimitError,
    SeaRatesNotFoundError,
    SeaRatesServerError,
)
from .models import (
    TrackingResult,
    SeaTrackingResult,
    AirTrackingResult,
    ParcelTrackingResult,
    RailTrackingResult,
    RoadTrackingResult,
    Carrier,
)

__version__ = "1.0.0"
__all__ = [
    # Client
    "SeaRatesClient",
    # Exceptions
    "SeaRatesException",
    "SeaRatesAuthError",
    "SeaRatesRateLimitError",
    "SeaRatesNotFoundError",
    "SeaRatesServerError",
    # Models
    "TrackingResult",
    "SeaTrackingResult",
    "AirTrackingResult",
    "ParcelTrackingResult",
    "RailTrackingResult",
    "RoadTrackingResult",
    "Carrier",
]
