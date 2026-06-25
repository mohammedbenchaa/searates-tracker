"""
Data models for SeaRates Tracker responses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class TrackingEvent:
    """Single tracking event/update."""
    date: str | None = None
    actual: bool | None = None
    event: str | None = None
    location: str | None = None
    vessel: str | None = None
    voyage: str | None = None
    mode: str | None = None
    transport_type: str | None = None
    order_id: str | None = None
    event_code: str | None = None
    _raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict) -> TrackingEvent:
        return cls(
            date=data.get("date"),
            actual=data.get("actual"),
            event=data.get("event") or data.get("movement"),
            location=_extract_location(data.get("location")),
            vessel=data.get("vessel"),
            voyage=data.get("voyage"),
            mode=data.get("mode"),
            transport_type=data.get("transport_mode"),
            order_id=data.get("order_id"),
            event_code=data.get("event_code"),
            _raw=data,
        )


@dataclass
class RoutePoint:
    """Route segment between two points."""
    from_name: str | None = None
    from_country: str | None = None
    from_locode: str | None = None
    to_name: str | None = None
    to_country: str | None = None
    to_locode: str | None = None
    path: list[list[float]] | None = None
    atd: str | None = None  # Actual Time of Departure
    etd: str | None = None  # Estimated Time of Departure
    ata: str | None = None  # Actual Time of Arrival
    eta: str | None = None  # Estimated Time of Arrival
    _raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict) -> RoutePoint:
        frm = data.get("from") or {}
        to = data.get("to") or {}
        return cls(
            from_name=frm.get("name"),
            from_country=frm.get("country"),
            from_locode=frm.get("locode"),
            to_name=to.get("name"),
            to_country=to.get("country"),
            to_locode=to.get("locode"),
            path=data.get("path"),
            atd=data.get("atd"),
            etd=data.get("etd"),
            ata=data.get("ata"),
            eta=data.get("eta"),
            _raw=data,
        )


@dataclass
class Container:
    """Container info from sea tracking."""
    number: str | None = None
    size_type: str | None = None
    status: str | None = None
    _raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict) -> Container:
        return cls(
            number=data.get("number"),
            size_type=data.get("size_type"),
            status=data.get("status"),
            _raw=data,
        )


@dataclass
class Vessel:
    """Vessel info."""
    name: str | None = None
    imo: str | None = None
    _raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api(cls, data: dict) -> Vessel:
        return cls(
            name=data.get("name"),
            imo=data.get("imo"),
            _raw=data,
        )


@dataclass
class TrackingResult:
    """Base tracking result."""
    is_success: bool = False
    tracking_number: str | None = None
    status: str | None = None
    status_message: str | None = None
    error_message: str | None = None
    updated_at: str | None = None
    _raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @classmethod
    def from_api_response(cls, response: dict) -> TrackingResult:
        api_status = response.get("status", "error")
        data = response.get("data", {})
        metadata = data.get("metadata", {})

        return cls(
            is_success=(api_status == "success"),
            tracking_number=metadata.get("number"),
            status=metadata.get("status"),
            status_message=response.get("message"),
            error_message=response.get("message") if api_status == "error" else None,
            updated_at=metadata.get("updated_at"),
            _raw=response,
        )


@dataclass
class SeaTrackingResult(TrackingResult):
    """Full sea/container tracking result."""
    direction_from: str | None = None
    direction_to: str | None = None
    sealine: str | None = None
    sealine_name: str | None = None
    from_cache: bool = False
    atd: str | None = None
    etd: str | None = None
    ata: str | None = None
    eta: str | None = None
    progress: int | None = None
    containers: list[Container] = field(default_factory=list)
    events: list[TrackingEvent] = field(default_factory=list)
    routes: list[RoutePoint] = field(default_factory=list)
    vessels: list[Vessel] = field(default_factory=list)

    @classmethod
    def from_api_response(cls, response: dict) -> SeaTrackingResult:
        base = TrackingResult.from_api_response(response)
        data = response.get("data", {})
        metadata = data.get("metadata", {})

        # Locations lookup
        locations = {loc["id"]: loc for loc in data.get("locations", [])}
        facilities = {f["id"]: f for f in data.get("facilities", [])}

        # Extract vessels
        raw_vessels = data.get("vessels", [])
        vessels_list = [
            Vessel(name=v.get("name"), imo=str(v.get("imo", "")))
            for v in raw_vessels
        ]

        # Extract events from containers
        containers = data.get("containers", [])
        events_list = []
        for cont in containers:
            for evt in cont.get("events", []):
                loc = locations.get(evt.get("location"))
                fac = facilities.get(evt.get("facility"))
                vessel = None
                vessel_id = evt.get("vessel")
                if vessel_id and raw_vessels:
                    for v in raw_vessels:
                        if v.get("id") == vessel_id:
                            vessel = v.get("name")
                            break

                location_str = None
                if loc:
                    parts = [loc.get("name", "")]
                    if loc.get("country"):
                        parts.append(loc.get("country"))
                    location_str = ", ".join(parts)
                elif fac:
                    location_str = fac.get("name")

                events_list.append(TrackingEvent(
                    date=evt.get("date"),
                    actual=evt.get("actual"),
                    event=evt.get("description"),
                    location=location_str,
                    vessel=vessel,
                    voyage=evt.get("voyage"),
                    mode=evt.get("type"),
                    transport_type=evt.get("transport_type"),
                    order_id=evt.get("order_id"),
                    event_code=evt.get("event_code"),
                    _raw=evt,
                ))

        # Extract routes
        route_data = data.get("route_data", {})
        raw_routes = route_data.get("route", [])
        routes_list = []
        for r in raw_routes:
            fr = r.get("from", {})
            to = r.get("to", {})
            routes_list.append(RoutePoint(
                from_name=fr.get("name"),
                from_country=fr.get("country"),
                from_locode=fr.get("locode"),
                to_name=to.get("name"),
                to_country=to.get("country"),
                to_locode=to.get("locode"),
                path=r.get("path"),
                _raw=r,
            ))

        # Direction
        if routes_list:
            direction_from = f"{routes_list[0].from_name}, {routes_list[0].from_country}"
            direction_to = f"{routes_list[-1].to_name}, {routes_list[-1].to_country}"
        else:
            direction_from = None
            direction_to = None

        # Route timing from route object
        route_obj = data.get("route", {})
        pol = route_obj.get("pol", {})
        pod = route_obj.get("pod", {})

        return cls(
            **base.__dict__,
            direction_from=direction_from,
            direction_to=direction_to,
            sealine=metadata.get("sealine"),
            sealine_name=metadata.get("sealine_name"),
            from_cache=metadata.get("from_cache", False),
            atd=pol.get("date") if pol.get("actual") else None,
            etd=pol.get("date"),
            ata=pod.get("date") if pod.get("actual") else None,
            eta=pod.get("date"),
            progress=None,  # Not in raw API; will be computed
            containers=[Container.from_api(c) for c in containers],
            events=events_list,
            routes=routes_list,
            vessels=vessels_list,
        )


@dataclass
class AirTrackingResult(TrackingResult):
    """Air cargo tracking result."""
    airline_name: str | None = None
    iata_code: str | None = None
    from_location: str | None = None
    to_location: str | None = None
    pieces: int | None = None
    weight: str | None = None
    atd: str | None = None
    eta: str | None = None
    events: list[TrackingEvent] = field(default_factory=list)

    @classmethod
    def from_api_response(cls, response: dict) -> AirTrackingResult:
        base = TrackingResult.from_api_response(response)
        data = response.get("data", {})
        metadata = data.get("metadata", {})

        return cls(
            **base.__dict__,
            airline_name=metadata.get("airline_name"),
            iata_code=metadata.get("iata_code"),
            from_location=data.get("from_location"),
            to_location=data.get("to_location"),
            pieces=data.get("pieces"),
            weight=data.get("weight"),
            atd=data.get("atd"),
            eta=data.get("eta"),
            events=[TrackingEvent.from_api(e) for e in data.get("events", [])],
        )


@dataclass
class ParcelTrackingResult(TrackingResult):
    """Parcel tracking result."""
    carrier_name: str | None = None
    carrier_code: str | None = None
    carrier_url: str | None = None
    from_location: str | None = None
    to_location: str | None = None
    events: list[TrackingEvent] = field(default_factory=list)
    routes: list[RoutePoint] = field(default_factory=list)

    @classmethod
    def from_api_response(cls, response: dict) -> ParcelTrackingResult:
        metadata = response.get("metadata", {})
        parcel_company = metadata.get("parcel_company", {})
        data = response.get("data", {})

        is_success = response.get("success", False) or response.get("status") == "success"

        return cls(
            is_success=is_success,
            tracking_number=metadata.get("request_parameters", {}).get("number"),
            status_message=response.get("status_code"),
            carrier_name=parcel_company.get("name"),
            carrier_code=parcel_company.get("carrier_code"),
            carrier_url=parcel_company.get("url"),
            from_location=data.get("from_location"),
            to_location=data.get("to_location"),
            events=[TrackingEvent.from_api(e) for e in data.get("events", [])],
            routes=[RoutePoint.from_api(r) for r in data.get("routes", [])],
            updated_at=metadata.get("updated_at"),
            _raw=response,
        )


@dataclass
class RailTrackingResult(TrackingResult):
    """Rail tracking result."""
    railway_company: str | None = None
    events: list[TrackingEvent] = field(default_factory=list)

    @classmethod
    def from_api_response(cls, response: dict) -> RailTrackingResult:
        base = TrackingResult.from_api_response(response)
        data = response.get("data", {})

        return cls(
            **base.__dict__,
            railway_company=data.get("railway_company"),
            events=[TrackingEvent.from_api(e) for e in data.get("events", [])],
        )


@dataclass
class RoadTrackingResult(TrackingResult):
    """Road tracking result."""
    events: list[TrackingEvent] = field(default_factory=list)

    @classmethod
    def from_api_response(cls, response: dict) -> RoadTrackingResult:
        base = TrackingResult.from_api_response(response)
        data = response.get("data", {})

        return cls(
            **base.__dict__,
            events=[TrackingEvent.from_api(e) for e in data.get("events", [])],
        )


@dataclass
class Carrier:
    """Shipping line / carrier information."""
    name: str
    scac_codes: list[str] = field(default_factory=list)
    prefixes: list[str] = field(default_factory=list)
    active: bool = True
    maintenance: bool = False
    cache_interval: int = 86400
    active_types: dict[str, bool] = field(default_factory=dict)
    _raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def supports_containers(self) -> bool:
        return self.active_types.get("ct", False)

    @property
    def supports_bl(self) -> bool:
        return self.active_types.get("bl", False)

    @property
    def supports_booking(self) -> bool:
        return self.active_types.get("bk", False)

    @classmethod
    def from_api(cls, data: dict) -> Carrier:
        return cls(
            name=data.get("carrier_name", ""),
            scac_codes=data.get("scac_codes", []),
            prefixes=data.get("prefixes", []),
            active=data.get("active", True),
            maintenance=data.get("maintenance", False),
            cache_interval=data.get("cache_interval", 86400),
            active_types=data.get("active_types", {}),
            _raw=data,
        )


# --- Helpers ---

def _extract_location(loc: Any) -> str | None:
    """Extract location string from various API formats."""
    if loc is None:
        return None
    if isinstance(loc, str):
        return loc
    if isinstance(loc, dict):
        parts = []
        name = loc.get("name")
        country = loc.get("country") or loc.get("country_code")
        state = loc.get("state")
        if name:
            parts.append(name)
        if state:
            parts.append(state)
        if country:
            parts.append(country)
        return ", ".join(parts) if parts else None
    return str(loc)
