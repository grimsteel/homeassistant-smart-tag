"""Sample API Client."""

from __future__ import annotations

import socket

import aiohttp
import async_timeout
from yarl import URL

from custom_components.smart_tag.data import Student

API_ORIGIN = URL("https://api-parentapp-prod.azurewebsites.net/")

class SmartTagApiError(Exception):
    """Exception to indicate a general API error."""


class SmartTagApiNetworkError(SmartTagApiError):
    """Exception to indicate a network error"""


class SmartTagApiAuthError(SmartTagApiError):
    """Exception to indicate an authentication error."""


def _raise_response_error(response: aiohttp.ClientResponse) -> None:
    """Raise an error based on the response code."""
    if response.status in (401, 403):
        raise SmartTagApiAuthError("invalid or expired credentials")
    # handle 400/404 manually
    if response.status not in (400, 404):
        response.raise_for_status()

class SmartTagApiClient:
    """API client for the new SMART tag backend."""

    _access_token = None
    _refresh_token = None

    def __init__(
        self,
        session: aiohttp.ClientSession,
        refresh_token: str | None = None,
        api_origin: URL = API_ORIGIN
    ) -> None:
        """Initialize the API client"""
        self._api_origin = api_origin
        self._refresh_token = refresh_token
        self._session = session

    async def login(self, email: str, password: str):
        """Login to the API and get a token"""
        self._refresh_token = None
        self._access_token = None

        response = await self._api_wrapper(
            "POST",
            "user/login",
            {
                "username": email,
                "password": password
            }
        )
        if response.status == 400:
            # invalid auth credentials
            raise SmartTagApiAuthError("invalid email or password")
        json = await response.json()

        # refresh token in cookie
        refresh_token = response.cookies.get("refreshToken")
        if refresh_token:
            self._refresh_token = refresh_token.value

        self._access_token = json["token"]

    async def get_students(self):
        """Get a list of the user's students."""
        if self._access_token is None:
            raise SmartTagApiAuthError("not authenticated")

        response = await self._api_wrapper(
            "GET",
            "parent/all-students"
        )

        students = [Student.from_dict(d) for d in await response.json()]
        print(students)

        return students

    async def _api_wrapper(
        self,
        method: str,
        path: str,
        data: dict | None = None,
    ):
        """SMART Tag API wrapper with error handling."""
        # add bearer token
        headers = {
            "Authorization": f"Bearer {self._access_token}"
        } if self._access_token is not None else None

        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=self._api_origin / path,
                    headers=headers,
                    json=data,
                )
                _raise_response_error(response)
                return response

        except TimeoutError as exception:
            err = f"Timeout error fetching information - {exception}"
            raise SmartTagApiNetworkError(
                err
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            err = f"Error fetching information - {exception}"
            raise SmartTagApiNetworkError(
                err
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            err = f"Something really wrong happened! - {exception}"
            raise SmartTagApiError(
                err
            ) from exception
