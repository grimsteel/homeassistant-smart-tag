"""Custom types for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from homeassistant.config_entries import ConfigEntry
    from homeassistant.loader import Integration

    from .api import SmartTagApiClient
    from .coordinator import SmartTagCoordinator


type SmartTagEntry = ConfigEntry[SmartTagData]


@dataclass
class SmartTagData:
    """Data for the Blueprint integration."""

    client: SmartTagApiClient
    coordinator: SmartTagCoordinator
    integration: Integration


@dataclass
class Student:
    """A student from the SMART Tag portal"""

    @classmethod
    def from_dict(cls, value: dict) -> Student:
        """Convert a dict to a Student."""
        return cls(
            campus=value["campus"],
            external_id=value["externalId"],
            full_name=value["fullName"],
            id=value["id"],
            grade=value["grade"],
        )

    campus: str
    external_id: str
    full_name: str
    id: int
    grade: str


@dataclass
class RideEndpoint:
    """Either the start or the end of a ride"""

    time: datetime
    lat: float
    long: float


@dataclass
class Ride:
    """A single bus ride"""

    DATE_FORMAT = "%m/%d/%Y %H:%M:%S"

    @classmethod
    def from_dict(cls, value: dict) -> Ride:
        """Convert a dict from the API to a Ride."""
        embarkation = RideEndpoint(
            time=datetime.strptime(
                value["embarkationDate"], cls.DATE_FORMAT
            ).astimezone(),
            lat=value["embarkationLatitude"],
            long=value["embarkationLongtitude"],
        )
        disembarkation = RideEndpoint(
            time=datetime.strptime(
                value["disembarkationDate"], cls.DATE_FORMAT
            ).astimezone(),
            lat=value["disembarkationLatitude"],
            long=value["disembarkationLongtitude"],
        )
        return cls(
            id=value["activityId"],
            bus_id=value["busName"],
            start=embarkation,
            end=disembarkation,
            driver=value["driverName"],
            route_name=value["friendlyRouteDisplay"],
            shift=value["shift"],
            route_id=value["routeId"],
        )

    id: int
    bus_id: str
    start: RideEndpoint
    end: RideEndpoint
    driver: str
    shift: str
    route_id: int
    route_name: str
