"""Adds config flow for APRS integration."""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ACCESS_TOKEN

from .const import DOMAIN

DATA_SCHEMA = vol.Schema({vol.Required(CONF_ACCESS_TOKEN): str})


class APRSConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for APRS integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle the initial step."""

        self._async_abort_entries_match()

        if user_input is not None:
            access_token = user_input[CONF_ACCESS_TOKEN]

            return self.async_create_entry(
                title="APRS",
                data={CONF_ACCESS_TOKEN: access_token},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors={},
        )
