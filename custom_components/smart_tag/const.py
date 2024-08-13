"""Constants for smart_tag."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "smart_tag"
ATTRIBUTION = "Data provided by https://smart-tag.net/"

CONF_STUDENT = "student"
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_ROUTES = "routes"
