import logging
from datetime import timedelta
import async_timeout
import aiohttp

from homeassistant.components.sensor import SensorEntity, SensorStateClass
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import EntityCategory

# Používáme relativní import, aby přejmenování složky nezpůsobilo chybu
from .const import DOMAIN, SENSOR_TYPES, SOLAX_MODES, SOLAX_STATES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Nastavení senzorů na základě konfigurace v UI."""
    ip = entry.data["ip"]
    pwd = entry.data["password"]
    scan_interval = entry.data.get("scan_interval", 6)

    coordinator = SolaxUpdateCoordinator(hass, ip, pwd, scan_interval)
    await coordinator.async_config_entry_first_refresh()

    entities = [SolaxSensor(coordinator, key, info, entry) for key, info in SENSOR_TYPES.items()]
    async_add_entities(entities)

class SolaxUpdateCoordinator(DataUpdateCoordinator):
    """Třída pro hromadné stahování dat ze střídače."""
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
                    res = await response.json(content_type=None)
                    if not res.get("Data"):
                        raise UpdateFailed("Invertor vrátil prázdná data.")
                    return res
        except Exception as err:
            raise UpdateFailed(f"Chyba komunikace: {err}")

class SolaxSensor(SensorEntity):
    """Senzor Solax s podporou statistik a dynamickými ikonami."""

    def __init__(self, coordinator, sensor_key, info, entry):
        self.coordinator = coordinator
        self._key = sensor_key
        self._info = info
        
        # Interní ID entity v Home Assistantu
        self.entity_id = f"sensor.solax_api_{sensor_key}"
        self._attr_name = info[0]
        # Unikátní ID pro možnost editace v UI
        self._attr_unique_id = f"solax_local_api_{sensor_key}_{entry.entry_id}"
        self._attr_native_unit_of_measurement = info[1]
        self._attr_device_class = info[2]

        # PODPORA PRO ENERGY DASHBOARD
        if info[1] == "kWh":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        elif info[1] in ["W", "V", "A", "%", "°C"]:
            self._attr_state_class = SensorStateClass.MEASUREMENT

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="SolaX Inverter",
            manufacturer="SolaX Power",
            model="X3-Hybrid G4",
            sw_version="Local API",
            configuration_url=f"http://{coordinator.ip}",
        )

        if sensor_key in ["inverter_sn", "type", "nominal_power", "battery_bms"]:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def icon(self):
        """Dynamické ikony podle hodnoty."""
        val = self.native_value
        if "pv_power" in self._key or "pv1" in self._key or "pv2" in self._key:
            return "mdi:solar-power" if (isinstance(val, (int, float)) and val > 0) else "mdi:solar-power-variant-outline"
        
        if self._key == "battery_soc":
            if val is None: return "mdi:battery-unknown"
            if val > 90: return "mdi:battery"
            if val > 20: return "mdi:battery-medium"
            return "mdi:battery-low"
            
        if self._key == "grid_power":
            if val is None or val == 0: return "mdi:transmission-tower"
            return "mdi:transmission-tower-export" if val > 0 else "mdi:transmission-tower-import"

        return super().icon

    @property
    def available(self):
        return self.coordinator.last_update_success

    @property
    def should_poll(self):
        return False

    async def async_added_to_hass(self):
        self.async_on_remove(self.coordinator.async_add_listener(self.async_write_ha_state))

    @property
    def native_value(self):
        if not self.coordinator.data: return None
        res = self.coordinator.data
        data, info_field = res.get("Data", []), res.get("Information", [])
        idx, factor, dtype = self._info[3], self._info[4], self._info[5]

        try:
            val = None
            if dtype == 0: 
                val = data[idx]
            elif dtype == 1:
                val = data[idx]
                if val > 32767: val -= 65536
            elif dtype == 2: 
                val = (data[idx[0]] * 65536) + data[idx[1]]
            elif dtype == 3:
                raw = data[idx]
                if self._key == "mode": return SOLAX_MODES.get(raw, f"Neznámý ({raw})")
                return SOLAX_STATES.get(raw, f"Neznámý ({raw})")
            elif dtype == 4: 
                val = data[idx[0]] + data[idx[1]]
            elif dtype == 5: 
                return "OK" if data[idx] == 1 else "Chyba"
            elif dtype == 6: 
                return "X3-Hybrid G4" if res.get("type") == 14 else f"Jiný ({res.get('type')})"
            elif dtype == 7: 
                return info_field[idx]
            
            if val is not None:
                return round(val * factor, 2)
            return None
        except Exception as e:
            _LOGGER.error("Chyba při parsování dat pro %s: %s", self._key, e)
            return None