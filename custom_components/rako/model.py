"""Rako shared models."""
from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from .bridge import RakoBridge


class RakoDomainEntryData(TypedDict):
    """A single Rako config entry's data."""

    rako_bridge_client: RakoBridge
