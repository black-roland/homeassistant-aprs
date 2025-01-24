"""The APRS component."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import aprslib
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN, LOGGER

PLATFORMS: list[Platform] = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    server_filter = "r/59.950000/30.31667/400 -t/oimqstun"
    ais = aprslib.IS("N0CALL", passwd="-1", host="spb.lan", port=14581)

    hass.data[DOMAIN] = ais

    ais.set_filter(server_filter)
    ais.connect()

    LOGGER.debug("Connected to APRS-IS")

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

    # # address = entry.unique_id
    # # data = DataParser()
    # coordinator = hass.data.setdefault(DOMAIN, {})[entry.entry_id] = (
    #     APRSDataUpdateCoordinator(hass)
    # )
    # await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    # entry.async_on_unload(
    #     # only start after all platforms have had a chance to subscribe
    #     coordinator.async_start()
    # )
    # return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(
        config_entry, PLATFORMS
    )
    # if unload_ok:
    #     tibber_connection = hass.data[DOMAIN]
    #     await tibber_connection.rt_disconnect()
    return unload_ok
