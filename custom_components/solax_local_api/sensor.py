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
    """Senzor Solax s podporou firmware, diagnostiky a hezkých ikon."""

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
        if sensor_key in ["firmware", "inverter_sn", "type", "nominal_power"]:
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

        # Typ 8 - čte verzi firmware přímo z kořene JSON ('ver')
        if dtype == 8:
            return res.get("ver")

        # Pro ostatní senzory čteme z polí Data nebo Information
        data = res.get("Data", [])
        info_field = res.get("Information", [])

        try:
            val = None
            if dtype == 0: # Unsigned
                val = data[idx] if idx < len(data) else None
            elif dtype == 1: # Signed
                val = data[idx] if idx < len(data) else None
                if val is not None and val > 32767: val -= 65536
            elif dtype == 2: # Long
                val = (data[idx[0]] * 65536) + data[idx[1]]
            elif dtype == 3: # Textové režimy
                raw = data[idx]
                if self._key == "mode":
                    return SOLAX_MODES.get(raw, f"Neznámý ({raw})")
                return SOLAX_STATES.get(raw, f"Neznámý ({raw})")
            elif dtype == 4: # PV sum
                val = data[idx[0]] + data[idx[1]]
            elif dtype == 5: # BMS Status
                return "OK" if data[idx] == 1 else "Chyba"
            elif dtype == 7: # Info field (SN)
                return info_field[idx] if idx < len(info_field) else None

            if val is not None:
                return round(val * factor, 2)
        except Exception:
            return None
        return None

    @property
    def icon(self):
        """Dynamické ikony s prioritou pro firmware a klíčové hodnoty."""
        key = self._key.lower()
        
        # Ikona pro firmware (čip)
        if "firmware" in key:
            return "mdi:chip"
        
        # Ikony pro solární panely
        if "pv" in key:
            return "mdi:solar-power-variant"
            
        # Ikony pro baterii (dynamická podle SoC pokud je to možné)
        if "battery_soc" in key:
            return "mdi:battery-high"
        if "battery" in key:
            return "mdi:battery-charging"
            
        # Ikony pro síť a spotřebu
        if "grid" in key:
            return "mdi:transmission-tower"
        if "consumption" in key:
            return "mdi:home-lightning-bolt"
            
        # Ikony pro střídač a diagnostiku
        if "inverter_sn" in key or "sn" in key:
            return "mdi:barcode-scan"
        if "temperature" in key:
            return "mdi:thermometer"
        if "mode" in key or "state" in key:
            return "mdi:cog-box"

        return super().icon

    @property
    def available(self):
        return self.coordinator.last_update_success

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    @property
    def should_poll(self):
        return False
