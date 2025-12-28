"""Module representing a Rako Bridge."""
from __future__ import annotations

import logging

from python_rako.bridge import Bridge

from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .model import RakoDomainEntryData

_LOGGER = logging.getLogger(__name__)


class RakoBridge(Bridge):
    """Represents a Rako Bridge."""

    def __init__(
        self,
        host: str,
        port: int,
        name: str,
        mac: str,
        entry_id: str,
        hass: HomeAssistant,
    ) -> None:
        """Init subclass of python_rako Bridge."""
        super().__init__(host, port, name, mac)
        self.entry_id = entry_id
        self.hass = hass
