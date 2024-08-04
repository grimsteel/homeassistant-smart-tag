"""Custom types for integration_blueprint."""

from __future__ import annotations

from dataclasses import dataclass
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
    @classmethod
    def from_dict(cls, value: dict):
        return cls(
            campus = value["campus"],
            externalId = value["externalId"],
            fullName = value["fullName"],
            id = value["id"],
            grade = value["grade"]
        )
    
    campus: str
    externalId: str
    fullName: str
    id: int
    grade: str
