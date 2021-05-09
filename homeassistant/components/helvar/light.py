import logging

import aiohelvar
import voluptuous as vol

# Import the device class from the component that you want to support
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    PLATFORM_SCHEMA,
    Light,
    LightEntity,
)

_LOGGER = logging.getLogger(__name__)

from .const import (
    DEFAULT_OFF_GROUP_BLOCK,
    DEFAULT_OFF_GROUP_SCENE,
    DEFAULT_ON_GROUP_BLOCK,
    DEFAULT_ON_GROUP_SCENE,
    DOMAIN as HELVAR_DOMAIN,
)


async def asynnc_setup_platform(hass, config, add_entities, discovery_info=None):
    """"""
    pass


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Helvar lights from a config entry."""

    router = hass.data[HELVAR_DOMAIN][config_entry.entry_id]

    # Add devices
    async_add_entities(
        HelvarLight(group, router) for group in router.api.groups.groups.values()
    )


class HelvarLight(LightEntity):
    """Representation of a Helvar Light."""

    def __init__(self, group: aiohelvar.groups.Group, router):
        """Initialize an HelvarLight."""
        self._router = router
        self._group = group
        self.group_id = group.group_id
        self.is_group = True

    @property
    def name(self):
        """Return the display name of this light."""
        return self._group.name

    @property
    def brightness(self):
        """Return the brightness of the light.
        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        if self.is_group:
            return None

    @property
    def is_on(self):
        """Return true if light is on."""

        if self.is_group:
            last_scene = self._group.last_scene
            if last_scene is None:
                return False
            if last_scene == aiohelvar.parser.address.SceneAddress(
                self._group.group_id,
                DEFAULT_OFF_GROUP_BLOCK,
                DEFAULT_OFF_GROUP_SCENE,
            ):
                return False
            return True

            # for device_address in self._group.devices:
            #     device = self._router.api.devices.devices.get(device_address)
            #     if device is not None:
            #         if device.load_level > 0:
            #             return True
        return False

    async def async_turn_on(self, **kwargs):
        """
        We'll just select scene 1 for a group, for now.
        """

        if self.is_group:
            await self._router.api.groups.set_scene(
                aiohelvar.parser.address.SceneAddress(
                    self._group.group_id, DEFAULT_ON_GROUP_BLOCK, DEFAULT_ON_GROUP_SCENE
                )
            )

    async def async_turn_off(self, **kwargs):
        """Instruct the light to turn off."""

        if self.is_group:
            await self._router.api.groups.set_scene(
                aiohelvar.parser.address.SceneAddress(
                    self._group.group_id,
                    DEFAULT_OFF_GROUP_BLOCK,
                    DEFAULT_OFF_GROUP_SCENE,
                )
            )

    async def async_update(self):
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """
        # the underlying objects are automatically updated, and all properties read directly from
        # those objects.
        return True
