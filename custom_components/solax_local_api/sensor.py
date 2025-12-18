import logging
from datetime import timedelta
import async_timeout
import aiohttp

from homeassistant.components.sensor import (
    SensorEntity, 
    SensorStateClass, 
    SensorDeviceClass
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import EntityCategory

from .const import DOMAIN, SENSOR_TYPES, SOLAX_MODES, SOLAX_STATES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Nastavení senzorů na základě konfigurace v UI."""
    ip = entry.data["ip"]
    pwd = entry.data["password"]
    scan_interval = entry.data.get("scan_interval", 10)

    coordinator = SolaxUpdateCoordinator(hass, ip, pwd, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    entities = [SolaxSensor(coordinator, key, info, entry) for key, info in SENSOR_TYPES.items()]
    async_add_entities(entities)

class SolaxUpdateCoordinator(DataUpdateCoordinator):
    """Třída pro stahování dat."""
    def __init__(self, hass, ip, pwd, scan_interval):
        super().__init__(
            hass, _LOGGER, name="Solax Data",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.ip = ip
        self.pwd = pwd

    async def _async_update_data(self):
        url = f"http://{self.ip}/"
        payload = f"optType=ReadRealTimeData&pwd={self.pwd}"
        try:
            async with aiohttp.ClientSession() as session, async_timeout.timeout(5):
                async with session.post(url, data=payload) as response:
                    return await response.json(content_type=None)
        except Exception as err:
            raise UpdateFailed(f"Chyba komunikace: {err}")

class SolaxSensor(SensorEntity):
    """Senzor Solax s podporou firmware a diagnostiky."""

    def __init__(self, coordinator, sensor_key, info, entry):
        self.coordinator = coordinator
        self._key = sensor_key
        self._info = info
        
        self.entity_id = f"sensor.solax_{sensor_key}"
        self._attr_name = info[0]
        self._attr_unique_id = f"solax_{sensor_key}_{entry.entry_id}"
        self._attr_native_unit_of_measurement = info[1]
        
        # --- Nastavení Device Class a State Class ---
        unit = info[1]
        self._attr_device_class = info[2]
        
        if unit == "kWh":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            self._attr_device_class = SensorDeviceClass.ENERGY
        elif unit == "W":
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_device_class = SensorDeviceClass.POWER
        
        # Kategorie pro servisní informace
        if sensor_key in ["firmware", "inverter_sn", "type"]:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="SolaX Inverter",
            manufacturer="SolaX Power",
            model="X3-Hybrid G4",
        )

    @property
    def native_value(self):
        if not self.coordinator.data:
            return None
        
        res = self.coordinator.data
        idx, factor, dtype = self._info[3], self._info[4], self._info[5]

        # Speciální případ pro Firmware (dtype 8) - čte z res['ver']
        if dtype == 8:
            return res.get("ver")

        # Pro ostatní senzory čteme z polí Data nebo Information
        data = res.get("Data", [])
        info_field = res.get("Information", [])

        try:
            val = None
            if dtype == 0: val = data[idx] # Unsigned
            elif dtype == 1: # Signed
                val = data[idx]
                if val > 32767: val -= 65536
            elif dtype == 2: # Long (32-bit)
                val = (data[idx[0]] * 65536) + data[idx[1]]
            elif dtype == 3: # Textové režimy
                raw = data[idx]
                return SOLAX_MODES.get(raw, f"Neznámý ({raw})") if self._key == "mode" else SOLAX_STATES.get(raw, f"Neznámý ({raw})")
            elif dtype == 4: # PV1 + PV2
                val = data[idx[0]] + data[idx[1]]
            elif dtype == 5: # BMS Status
                return "OK" if data[idx] == 1 else "Chyba"
            elif dtype == 7: # Informační pole (Sériová čísla)
                return info_field[idx]

            if val is
