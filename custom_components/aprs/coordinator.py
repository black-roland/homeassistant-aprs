"""Coordinator for APRS sensors."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import LOGGER


class APRSDataCoordinator(DataUpdateCoordinator[None]):
    """Handle APRS data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, ais: Any) -> None:
        """Initialize the data handler."""
        super().__init__(
            hass,
            LOGGER,
            name="APRS",
        )
        self.ais = ais

    # async def _async_update_data(self) -> None:
    #   pass
