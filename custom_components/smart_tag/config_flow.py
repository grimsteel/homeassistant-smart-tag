"""Adds config flow for SMART Tag."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time, timedelta
from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.exceptions import InvalidStateError
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    SmartTagApiAuthError,
    SmartTagApiClient,
    SmartTagApiError,
    SmartTagApiNetworkError,
)
from .const import CONF_ROUTES, CONF_STUDENT, DOMAIN, LOGGER

if TYPE_CHECKING:
    from custom_components.smart_tag.data import Ride


@dataclass
class Route:
    """Route polling data"""

    # start embark polling
    embark_start: time

    # stop polling if they haven't embarked by this time
    embark_end: time

    # start debark polling this many minutes after embarkation time
    length: float

    # give up debark polling by this time
    debark_end: time

    id: int
    name: str

    DISPLAY_TIME_FORMAT = "%I:%M %p"

    def display(self):
        """Return a human-readable string representing this route."""
        return f"**{self.name}** (Embark start: {self.embark_start.strftime(self.DISPLAY_TIME_FORMAT)} • Embark end: {self.embark_end.strftime(self.DISPLAY_TIME_FORMAT)} • Ride length: {self.length:.2f} min • Debark end: {self.debark_end.strftime(self.DISPLAY_TIME_FORMAT)})"


def average_route_polling_data(data: list[Ride]):
    """Average a list of rides into a Route polling data"""
    embark_start_min = time(23, 59, 59)
    embark_end_max = time(0, 0)
    debark_end_max = time(0, 0)
    length_secs = 0

    # Knuth 1998 - average
    for i, ride in enumerate(data):
        embark_start_min = min(embark_start_min, ride.start.time.time())
        embark_end_max = max(
            embark_end_max, (ride.start.time + timedelta(minutes=5)).time()
        )
        debark_end_max = max(
            debark_end_max, (ride.end.time + timedelta(minutes=10)).time()
        )
        length_secs += ((ride.end.time - ride.start.time).seconds - length_secs) / (
            i + 1
        )

    return Route(
        embark_start=embark_start_min,
        embark_end=embark_end_max,
        length=length_secs / 60.0,
        debark_end=debark_end_max,
        id=data[0].route_id,
        name=data[0].route_name,
    )


class SmartTagConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for SMART Tag."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the class"""
        super().__init__()

        self._api_client = None

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> data_entry_flow.FlowResult:
        """Handle a flow initialized by the user."""
        if self._api_client is None:
            self._api_client = SmartTagApiClient(async_create_clientsession(self.hass))

        _errors = {}
        if user_input is not None:
            try:
                await self._api_client.login(
                    user_input[CONF_EMAIL], user_input[CONF_PASSWORD]
                )
            except SmartTagApiAuthError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except SmartTagApiNetworkError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except SmartTagApiError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                return await self.async_step_choose_student()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_EMAIL,
                        # prefill with the email they entered
                        default=user_input.get(CONF_EMAIL, vol.UNDEFINED)
                        if user_input
                        else vol.UNDEFINED,
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.EMAIL,
                        ),
                    ),
                    vol.Required(CONF_PASSWORD): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def async_step_choose_student(self, user_input: dict | None = None):
        """Prompt the user to select one of their students."""
        if self._api_client is None:
            raise InvalidStateError("invalid state")

        _errors = {}
        if user_input is not None:
            self._student_id = str(user_input[CONF_STUDENT])
            return await self.async_step_choose_times()

        students = []

        # load a list of students
        try:
            students = await self._api_client.get_students()
        except SmartTagApiAuthError as exception:
            LOGGER.warning(exception)
            _errors["base"] = "auth"
        except SmartTagApiNetworkError as exception:
            LOGGER.error(exception)
            _errors["base"] = "connection"
        except SmartTagApiError as exception:
            LOGGER.exception(exception)
            _errors["base"] = "unknown"

        return self.async_show_form(
            step_id="choose_student",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STUDENT): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            # radio buttons
                            mode=selector.SelectSelectorMode.LIST,
                            options=[
                                # one option for each student
                                selector.SelectOptionDict(
                                    value=str(student.id),
                                    label=f"{student.full_name} ({student.grade}) #{student.external_id}",
                                )
                                for student in students
                            ],
                        )
                    )
                }
            ),
            errors=_errors,
        )

    async def async_step_choose_times(self, user_input: dict | None = None):
        """Ask the user to select the polling times"""
        if self._api_client is None or self._student_id is None:
            raise InvalidStateError("invalid state")

        _errors = {}

        if user_input is not None:
            pass

        # get the 50 most recent rides
        rides = []
        try:
            rides = await self._api_client.get_rides(self._student_id, 50)
        except SmartTagApiAuthError as exception:
            LOGGER.warning(exception)
            _errors["base"] = "auth"
        except SmartTagApiNetworkError as exception:
            LOGGER.error(exception)
            _errors["base"] = "connection"
        except SmartTagApiError as exception:
            LOGGER.exception(exception)
            _errors["base"] = "unknown"

        routes: dict[int, list[Ride]] = {}
        for ride in rides:
            if ride.route_id in routes:
                routes[ride.route_id].append(ride)
            else:
                routes[ride.route_id] = [ride]

        # average all items together
        avg_routes = [average_route_polling_data(rides) for rides in routes.values()]

        return self.async_show_form(
            step_id="choose_times",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_ROUTES): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            # radio buttons
                            mode=selector.SelectSelectorMode.LIST,
                            multiple=True,
                            options=[
                                # one option for each student
                                selector.SelectOptionDict(
                                    value=str(route.id),
                                    label=route.display(),
                                )
                                for route in avg_routes
                            ],
                        )
                    )
                }
            ),
            errors=_errors,
        )
