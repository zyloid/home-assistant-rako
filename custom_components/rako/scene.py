"""Platform for scene integration."""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

import python_rako
from python_rako.exceptions import RakoBridgeError

from homeassistant.components.scene import Scene
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .util import create_unique_id

if TYPE_CHECKING:
    from .bridge import RakoBridge
    from .model import RakoDomainEntryData

_LOGGER = logging.getLogger(__name__)

# Rako scene definitions
# Scene 0 = Off (handled by lights)
# Scene 1 = 100% brightness
# Scene 2 = 75% brightness
# Scene 3 = 50% brightness
# Scene 4 = 25% brightness
RAKO_SCENES = {
    1: {"name": "Scene 1", "description": "100% brightness"},
    2: {"name": "Scene 2", "description": "75% brightness"},
    3: {"name": "Scene 3", "description": "50% brightness"},
    4: {"name": "Scene 4", "description": "25% brightness"},
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the config entry."""
    rako_domain_entry_data: RakoDomainEntryData = hass.data[DOMAIN][entry.unique_id]
    bridge = rako_domain_entry_data["rako_bridge_client"]

    hass_scenes: list[Scene] = []
    session = async_get_clientsession(hass)

    # Discover rooms from the bridge
    async for light in bridge.discover_lights(session):
        # Only create scene entities for RoomLight, not individual ChannelLight
        if isinstance(light, python_rako.RoomLight):
            room_id = light.room_id
            room_title = light.room_title

            # Create a scene entity for each Rako scene (1-4)
            for scene_number, scene_info in RAKO_SCENES.items():
                hass_scene = RakoScene(
                    bridge, room_id, room_title, scene_number, scene_info
                )
                hass_scenes.append(hass_scene)

    async_add_entities(hass_scenes, True)


class RakoScene(Scene):
    """Representation of a Rako Scene."""

    def __init__(
        self,
        bridge: RakoBridge,
        room_id: int,
        room_title: str,
        scene_number: int,
        scene_info: dict[str, str],
    ) -> None:
        """Initialize a RakoScene."""
        self.bridge = bridge
        self._room_id = room_id
        self._room_title = room_title
        self._scene_number = scene_number
        self._scene_info = scene_info
        self._available = True

    @property
    def name(self) -> str:
        """Return the display name of this scene."""
        return f"{self._room_title} - {self._scene_info['name']}"

    @property
    def unique_id(self) -> str:
        """Scene's unique ID."""
        return create_unique_id(self.bridge.mac, self._room_id, self._scene_number)

    @property
    def available(self) -> bool:
        """Return True if entity is available."""
        return self._available

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information about this Rako Scene."""
        return {
            "identifiers": {(DOMAIN, f"{self.bridge.mac}_{self._room_id}")},
            "name": self._room_title,
            "manufacturer": "Rako",
            "via_device": (DOMAIN, self.bridge.mac),
        }

    async def async_activate(self, **kwargs: Any) -> None:
        """Activate the scene."""
        _LOGGER.debug(
            "Activating scene %s for room %s (scene number %s)",
            self.name,
            self._room_id,
            self._scene_number,
        )

        try:
            await asyncio.wait_for(
                self.bridge.set_room_scene(self._room_id, self._scene_number),
                timeout=3.0,
            )
            _LOGGER.debug("Scene activation successful for %s", self.name)
            self._available = True

        except (RakoBridgeError, asyncio.TimeoutError) as ex:
            _LOGGER.error(
                "Error activating scene %s: %s",
                self.name,
                ex,
            )
            if self._available:
                _LOGGER.error("An error occurred while activating the Rako Scene")
            self._available = False
