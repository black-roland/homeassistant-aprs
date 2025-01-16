import logging
import threading
from typing import Any, final

import aprslib
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import UnitOfTemperature, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

_LOGGER = logging.getLogger(__name__)


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the sensor platform."""

    mon = APRSWeatherSensor()
    add_entities([APRSWeatherTemp("APRS temperature", mon)])
    mon.start()


class APRSWeatherSensor(threading.Thread, SensorEntity):

    # _attr_name = "APRS temperature"
    # _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    # _attr_device_class = SensorDeviceClass.TEMPERATURE
    # _attr_state_class = SensorStateClass.MEASUREMENT
    # _attr_should_poll: bool = False

    def __init__(self) -> None:
        """Initialize the sensor."""

        threading.Thread.__init__(self)
        self.daemon = False
        self.keep_going = True
        self.data = {"weather": None, "latitude": None, "longitude": None}
        self.event = threading.Event()

        _LOGGER.debug("Starting APRS-IS thread.")

        self.server_filter = "r/59.950000/30.31667/250 -t/oimqstun"

        self.ais = aprslib.IS("N0CALL", passwd="-1", host="spb.lan", port=14581)

    def run(self) -> None:
        """Run the thread."""
        try:
            self.ais.set_filter(self.server_filter)
            self.ais.connect()
            _LOGGER.debug("Connected to the APRS-IS server.")
            self.ais.consumer(callback=self.rx_msg, immortal=True)
        except (aprslib.ConnectionError, aprslib.LoginError) as err:
            _LOGGER.exception(err)
        except OSError:
            _LOGGER.debug(
                "Closing connection to %s with callsign %s",
            )

    def rx_msg(self, msg: dict[str, Any]):
        _LOGGER.debug("APRS message received: %s", str(msg))
        # weather packets only
        if "weather" not in msg:
            return
        self.data = msg

    @property
    @final
    def state(self) -> str | None:
        """Return the state."""
        return 22

    def terminate(self):
        """Signal runner to stop and join thread."""
        self.keep_going = False
        self.event.set()
        self.join()


class APRSWeatherTemp(SensorEntity):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, name, mon):
        """Initialize a sensor."""
        self.mon = mon
        self._name = name

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def native_value(self):
        """Return the state of the device."""
        if self.mon.data["weather"] is None:
            return None
        _LOGGER.debug("Weather data: %s", self.mon.data)
        return self.mon.data["weather"]["temperature"]

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            "latitude": self.mon.data["latitude"],
            "longitude": self.mon.data["longitude"],
        }
