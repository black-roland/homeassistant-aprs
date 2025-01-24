# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from typing import Any, Callable

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from .const import DOMAIN, LOGGER

RT_SENSORS: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the sensor platform."""

    ais = hass.data[DOMAIN]

    entity_registry = er.async_get(hass)

    # coordinator = APRSDataCoordinator(hass, ais)

    LOGGER.debug("Setting up sensor platform")

    async_add_entities([], True)

    LOGGER.debug("Added entries")

    entity_creator = APRSRtEntityCreator(async_add_entities, entity_registry)

    LOGGER.debug("Created entity creator")

    ais.consumer(
        callback=APRSRtDataCoordinator(
            entity_creator.add_sensors, hass
        ).async_set_updated_data,
        immortal=True,
        blocking=False,
    )

    LOGGER.debug("Registered consumer")

    return True

    # coordinator: APRSDataUpdateCoordinator = hass.data[DOMAIN][
    #     entry.entry_id
    # ]
    # processor = PassiveBluetoothDataProcessor(sensor_update_to_bluetooth_data_update)
    # entry.async_on_unload(
    #     processor.async_add_entities_listener(
    #         ExampleBluetoothSensorEntity, async_add_entities
    #     )
    # )
    # entry.async_on_unload(coordinator.async_register_processor(processor))

    # @callback
    # def async_add_entities_platform(msg):
    #     LOGGER.debug("Adding sensor %s", msg["from"])
    #     sensor = APRSWeatherTemp(msg["from"], msg)
    #     async_add_entities([sensor])

    # mon = APRSWeatherMonitor(async_add_entities_platform)
    # mon.start()

    # return True


class APRSRtDataCoordinator(DataUpdateCoordinator):

    def __init__(
        self,
        add_sensor_callback: Callable[[Any, Any], None],
        hass: HomeAssistant,
    ) -> None:
        """Initialize the data handler."""
        self._add_sensor_callback = add_sensor_callback
        super().__init__(
            hass,
            LOGGER,
            name="APRS",
        )

    @callback
    def _data_updated(self) -> None:
        """Triggered when data is updated."""
        if packet := self.get_packet():
            self._add_sensor_callback(self, packet)

    def get_packet(self) -> Any:
        return self.data.get("data", {}).get("packet")


class APRSSensor(SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, callsign, packet):
        """Initialize a sensor."""
        self._packet = packet
        self._name = callsign

    @property
    def name(self):
        """Return the name of the sensor."""
        return "APRS " + self._name

    @property
    def native_value(self):
        """Return the state of the device."""
        if self._packet["weather"] is None:
            return None
        LOGGER.debug("Weather data: %s", self._packet)
        return self._packet["weather"]["temperature"]

    @property
    def extra_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            "latitude": self._packet["latitude"],
            "longitude": self._packet["longitude"],
        }


class APRSSensorRT(APRSSensor, CoordinatorEntity["APRSRtDataCoordinator"]):
    """Representation of a APRS sensor for real time data."""

    def __init__(
        self,
        callsign: str,
        packet,
        description: SensorEntityDescription,
        coordinator: APRSRtDataCoordinator,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator=coordinator, callsign=callsign, packet=packet)
        self.entity_description = description

        self._attr_native_value = 0
        self._attr_unique_id = f"{DOMAIN}{callsign}_rt_{description.key}"

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return True

    @callback
    def _handle_coordinator_update(self) -> None:
        if not (packet := self.coordinator.get_packet()):
            return
        state = packet["weather"].get(self.entity_description.key)
        if state is None:
            return

        self._attr_native_value = state
        self.async_write_ha_state()


class APRSRtEntityCreator:
    """Create realtime APRS entities."""

    def __init__(
        self,
        async_add_entities: AddEntitiesCallback,
        entity_registry: er.EntityRegistry,
    ) -> None:
        """Initialize the data handler."""
        self._async_add_entities = async_add_entities
        self._added_sensors: set[str] = set()
        self._entity_registry = entity_registry

    @callback
    def add_sensors(self, coordinator: APRSRtDataCoordinator, packet: Any) -> None:
        """Add sensor."""
        new_entities = []
        for sensor_description in RT_SENSORS:
            if sensor_description.key in self._added_sensors:
                continue
            callsign = packet["from"]
            state = packet["weather"].get(sensor_description.key)
            if state is None:
                continue

            entity = APRSSensorRT(
                callsign,
                packet,
                sensor_description,
                state,
                coordinator,
            )
            new_entities.append(entity)
            self._added_sensors.add(sensor_description.key)
        if new_entities:
            self._async_add_entities(new_entities)


# class APRSWeatherMonitor(threading.Thread, SensorEntity):

#     # _attr_name = "APRS temperature"
#     # _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
#     # _attr_device_class = SensorDeviceClass.TEMPERATURE
#     # _attr_state_class = SensorStateClass.MEASUREMENT
#     # _attr_should_poll: bool = False

#     def __init__(self, async_add_entities_platform) -> None:
#         """Initialize the sensor."""

#         threading.Thread.__init__(self)
#         self.daemon = False
#         self.keep_going = True
#         self.data = {"weather": None, "latitude": None, "longitude": None}
#         self.event = threading.Event()
#         self.async_add_entities_platform = async_add_entities_platform

#         LOGGER.debug("Starting APRS-IS thread.")

#         self.server_filter = "r/59.950000/30.31667/400 -t/oimqstun"

#         self.ais = aprslib.IS("N0CALL", passwd="-1", host="spb.lan", port=14581)

#     def run(self) -> None:
#         """Run the thread."""
#         try:
#             self.ais.set_filter(self.server_filter)
#             self.ais.connect()
#             LOGGER.debug("Connected to the APRS-IS server.")
#             self.ais.consumer(callback=self.rx_msg, immortal=True)
#         except (aprslib.ConnectionError, aprslib.LoginError) as err:
#             LOGGER.exception(err)
#         except OSError:
#             LOGGER.debug(
#                 "Closing connection to %s with callsign %s",
#             )

#     def rx_msg(self, msg: dict[str, Any]):
#         LOGGER.debug("APRS message received: %s", str(msg))
#         # weather packets only
#         if "weather" not in msg:
#             return

#         self.async_add_entities_platform(msg)
#         # self.data = msg

#     @property
#     @final
#     def state(self) -> str | None:
#         """Return the state."""
#         return 22

#     def terminate(self):
#         """Signal runner to stop and join thread."""
#         self.keep_going = False
#         self.event.set()
#         self.join()
