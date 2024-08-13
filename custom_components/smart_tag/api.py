"""Sample API Client."""

from __future__ import annotations

import socket
from urllib.parse import unquote

import aiohttp
import async_timeout
from yarl import URL

from custom_components.smart_tag.data import Ride, Student

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

    access_token = None
    refresh_token = None

    def __init__(
        self,
        session: aiohttp.ClientSession,
        access_token: str | None = None,
        refresh_token: str | None = None,
        api_origin: URL = API_ORIGIN,
    ) -> None:
        """Initialize the API client"""
        self._api_origin = api_origin
        self.refresh_token = refresh_token
        self.access_token = access_token
        self._session = session

    async def login(self, email: str, password: str):
        """Login to the API and get a token"""
        self.refresh_token = None
        self.access_token = None

        response = await self._api_wrapper(
            "POST", "user/login", {"username": email, "password": password}
        )
        if response.status == 400:
            # invalid auth credentials
            raise SmartTagApiAuthError("invalid email or password")
        json = await response.json()

        # refresh token in cookie
        refresh_token = response.cookies.get("refreshToken")
        if refresh_token:
            self.refresh_token = unquote(refresh_token.value)

        self.access_token = json["token"]

    async def refresh_access_token(self):
        """Refresh the access token"""
        if self.access_token is None or self.refresh_token is None:
            raise SmartTagApiAuthError("not authenticated")

        data = {"token": self.access_token, "refreshToken": self.refresh_token}
        response = await self._api_wrapper("POST", "user/refresh", data=data)

        if not response.ok:
            raise SmartTagApiAuthError("need reauthentication")

        json = await response.json()

        # refresh token in cookie
        refresh_token = response.cookies.get("refreshToken")
        if refresh_token:
            self.refresh_token = unquote(refresh_token.value)

        self.access_token = json["token"]

    async def get_students(self):
        """Get a list of the user's students."""
        if self.access_token is None:
            raise SmartTagApiAuthError("not authenticated")

        response = await self._authed_api_wrapper("GET", "parent/all-students")

        return [Student.from_dict(d) for d in await response.json()]

    async def get_rides(self, student_id: str, limit: int):
        """Get the {limit} most recent rides for this student"""
        if self.access_token is None:
            raise SmartTagApiAuthError("not authenticated")

        query = {"studentid": student_id, "pageIndex": 0, "pageSize": limit}
        response = await self._authed_api_wrapper(
            "GET", "student/riding-activity", query=query
        )
        json = await response.json()

        return [Ride.from_dict(d) for d in json["data"]]

    async def _api_wrapper(
        self,
        method: str,
        path: str,
        data: dict | None = None,
        query: dict | None = None,
        headers: dict | None = None,
    ):
        """Make a call to the SMART Tag API with error handling."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=self._api_origin / path % query,
                    headers=headers,
                    json=data,
                )
                _raise_response_error(response)
                return response

        except TimeoutError as exception:
            err = f"Timeout error fetching information - {exception}"
            raise SmartTagApiNetworkError(err) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            err = f"Error fetching information - {exception}"
            raise SmartTagApiNetworkError(err) from exception
        except Exception as exception:  # pylint: disable=broad-except
            err = f"Something really wrong happened! - {exception}"
            raise SmartTagApiError(err) from exception

    async def _authed_api_wrapper(
        self,
        method: str,
        path: str,
        data: dict | None = None,
        query: dict | None = None,
    ):
        """Make an authenticated call to the SMART Tag API with error handling"""
        # add bearer token
        headers = (
            {"Authorization": f"Bearer {self.access_token}"}
            if self.access_token is not None
            else None
        )

        try:
            return await self._api_wrapper(method, path, data, query, headers)
        except SmartTagApiAuthError:
            # try to reauthenticate
            await self.refresh_access_token()

            # new bearer token
            headers = (
                {"Authorization": f"Bearer {self.access_token}"}
                if self.access_token is not None
                else None
            )

            return await self._api_wrapper(method, path, data, query, headers)
