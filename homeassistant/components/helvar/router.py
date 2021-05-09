import logging

import aiohelvar

from homeassistant.exceptions import ConfigEntryNotReady

_LOGGER = logging.getLogger(__name__)


class HelvarRouter:
    """Manages a Helvar Router."""

    def __init__(self, hass, config_entry):
        """Initialize the system."""
        self.config_entry = config_entry
        self.hass = hass
        self.available = True

    @property
    def host(self):
        """Return the host of this bridge."""
        return self.config_entry.data["host"]

    async def async_setup(self, tries=0):
        """Set up a helval router based on host parameter."""
        host = self.host
        hass = self.hass

        router = aiohelvar.Router(host, 50000)

        try:
            await router.connect()
            await router.initialize()

        except ConnectionError as err:
            _LOGGER.error("Error connecting to the Hue bridge at %s", host)
            raise ConfigEntryNotReady from err

        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unknown error connecting with Hue bridge at %s", host)
            return False

        self.api = router
        # self.sensor_manager = SensorManager(self)

        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(self.config_entry, "light")
        )

        return True
