"""Base entity for the Yamaha sound bar."""

from __future__ import annotations

from homeassistant.helpers.device_info import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import YamahaCoordinator


class YamahaEntity(CoordinatorEntity[YamahaCoordinator]):
    """Common device info + attribute wiring."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: YamahaCoordinator) -> None:
        super().__init__(coordinator)
        address = coordinator.client.address
        self._attr_device_info = DeviceInfo(
            connections={("bluetooth", address)},
            identifiers={(DOMAIN, address)},
            manufacturer="Yamaha",
            name=coordinator.config_entry.title,
        )

    @property
    def client(self):
        return self.coordinator.client

    @property
    def state_data(self):
        return self.coordinator.data

    @property
    def available(self) -> bool:
        return super().available and self.coordinator.client.connected
