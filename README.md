# SMART Tag Home Assistant Integratin

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]

_Integration to integrate with [SMART Tag parent portal][https://parent.smart-tag.net]._

**This integration will set up the following platforms for each student:**

Platform | Description
-- | --
On Bus (`binary_sensor`) | Whether the student is current on a bus.
Last Bus (`sensor`) | The last bus number the student was on (includes bus route/driver)
Enable Polling (`switch`) | Whether to enable polling for updates for this student (can be turned off if they stop riding the bus)

## Installation

1. Download the `custom_components/smart_tag/` directory into your HA `custom_components` dire
1. Restart Home Assistant
1. In the HA UI go to "Configuration" -> "Integrations" click "+" and search for "SMART Tag"

**Configuration is done in the UI**

<!---->

## Contributions are welcome!


***

[commits-shield]: https://img.shields.io/github/commit-activity/y/grimsteel/homeassistant-smart-tag.svg?style=for-the-badge
[commits]: https://github.com/grimsteel/homeassistant-smart-tag/commits/main

[releases-shield]: https://img.shields.io/github/release/grimsteel/homeassistant-smart-tag.svg?style=for-the-badge
[releases]: https://github.com/grimsteel/homeassistant-smart-tag/releases
