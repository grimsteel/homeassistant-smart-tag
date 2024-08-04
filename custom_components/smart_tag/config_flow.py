"""Adds config flow for SMART Tag."""

from __future__ import annotations

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
from .const import CONF_STUDENT, DOMAIN, LOGGER


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
            self._api_client = SmartTagApiClient(
                async_create_clientsession(self.hass)
            )

        _errors = {}
        if user_input is not None:
            try:
                await self._api_client.login(
                    user_input[CONF_EMAIL],
                    user_input[CONF_PASSWORD]
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
                        default=user_input.get(CONF_EMAIL, vol.UNDEFINED) if user_input else vol.UNDEFINED,
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

    async def async_step_choose_student(
            self,
            user_input: dict | None = None
    ):
        """Prompt the user to select one of their students."""
        if self._api_client is None:
            raise InvalidStateError("invalid state")

        _errors = {}
        if user_input is not None:
            pass

        # load a list of students
        students = await self._api_client.get_students()

        return self.async_show_form(
            step_id="choose_student",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_STUDENT): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            mode = selector.SelectSelectorMode.LIST,
                            options = [
                                selector.SelectOptionDict(
                                    value = str(student.id),
                                    label =
                                     f"{student.full_name} ({student.grade}) #{student.external_id}"
                                )
                                for student in students
                            ]
                        )
                    )
                }
            ),
            errors=_errors
        )
