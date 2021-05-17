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
    VALID_OFF_GROUP_SCENES,
)


async def asynnc_setup_platform(hass, config, add_entities, discovery_info=None):
    """"""
    pass


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up Helvar lights from a config entry."""

    router = hass.data[HELVAR_DOMAIN][config_entry.entry_id]

    # Add devices
    async_add_entities(
        # Add groups
        HelvarLight(group, None, router)
        for group in router.api.groups.groups.values()
    )

    devices = [
        HelvarLight(None, device, router)
        for device in router.api.devices.get_light_devices()
    ]

    _LOGGER.critical(f"Adding {len(devices)} devices. ")

    async_add_entities(devices)


class HelvarLight(LightEntity):
    """Representation of a Helvar Light."""

    def __init__(
        self, group: aiohelvar.groups.Group, device: aiohelvar.devices.Device, router
    ):
        """Initialize an HelvarLight."""
        self._router = router
        self._group = group
        self._device = device
        self.group_id = None
        self.device_address = None

        if group is None:
            if device is None:
                raise Exception("device or group must be set")
            self.is_group = False
            self.device_address = self._device.address
        else:
            self.is_group = True
            if device is not None:
                raise Exception("device and group connot both be set")

        self.register_subscription()

    def register_subscription(self):
        async def async_router_callback_group(group_id):
            self.async_write_ha_state()

        async def async_router_callback_device(device_id):
            self.async_write_ha_state()

        if self.is_group:
            self._router.api.groups.register_subscription(
                self.group_id, async_router_callback_group
            )
        else:
            self._router.api.devices.register_subscription(
                self.device_address, async_router_callback_group
            )

    @property
    def name(self):
        """Return the display name of this light."""
        if self.is_group:
            return f"Group: {self._group.name}"
        else:
            return self._device.name

    @property
    def brightness(self):
        """Return the brightness of the light.
        This method is optional. Removing it indicates to Home Assistant
        that brightness is not supported for this light.
        """
        if self.is_group:
            return None

        return self._device.brightness

    @property
    def is_on(self):
        """Return true if light is on."""

        if self.is_group:
            last_scene = self._group.last_scene
            if last_scene is None:
                return False
            if last_scene in [
                aiohelvar.parser.address.SceneAddress(
                    self._group.group_id, DEFAULT_OFF_GROUP_BLOCK, s
                )
                for s in VALID_OFF_GROUP_SCENES
            ]:
                return False
            return True

            # for device_address in self._group.devices:
            #     device = self._router.api.devices.devices.get(device_address)
            #     if device is not None:
            #         if device.load_level > 0:
            #             return True

        # Device

        if self.brightness > 0:
            return True
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
        else:
            # For now, set the device level directly. But we may want to set the device scene as we do with
            # groups.
            await self._router.api.devices.set_device_brightness(
                self.device_address, 255
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
        else:
            # For now, set the device level directly. But we may want to set the device scene as we do with
            # groups.
            await self._router.api.devices.set_device_brightness(self.device_address, 0)

    async def async_update(self):
        """Fetch new state data for this light.
        This is the only method that should fetch new data for Home Assistant.
        """
        # the underlying objects are automatically updated, and all properties read directly from
        # those objects.
        return True
