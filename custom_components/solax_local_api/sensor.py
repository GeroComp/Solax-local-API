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
from homeassistant.const import EntityCategory, UnitOfPower, UnitOfEnergy, PERCENTAGE, UnitOfTemperature, UnitOfElectricPotential, UnitOfElectricCurrent

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
        
        self.entity_id = f"sensor.solax_api_{sensor_key}"
        self._attr_name = info[0]
        self._attr_unique_id = f"solax_local_api_{sensor_key}_{entry.entry_id}"
        self._attr_native_unit_of_measurement = info[1]
        
        # Automatické nastavení Device Class a State Class pro Energy Dashboard
        self._setup_energy_attributes(info[1], info[2])

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

    def _setup_energy_attributes(self, unit, d_class):
        """Konfigurace atributů pro správné zobrazení v Energy Dashboardu."""
        self._attr_device_class = d_class
        
        if unit == "kWh":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            self._attr_device_class = SensorDeviceClass.ENERGY
        elif unit in ["W", "kW"]:
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_device_class = SensorDeviceClass.POWER
        elif unit in ["V", "A", "%", "°C"]:
            self._attr_state_class = SensorStateClass.MEASUREMENT
            if unit == "V": self._attr_device_class = SensorDeviceClass.VOLTAGE
            if unit == "A": self._attr_device_class = SensorDeviceClass.CURRENT
            if unit == "%": self._attr_device_class = SensorDeviceClass.BATTERY if "soc" in self._key else None
            if unit == "°C": self._attr_device_class = SensorDeviceClass.TEMPERATURE

    @property
    def icon(self):
        """Dynamické ikony podle aktuálního stavu."""
        val = self.native_value
        if val is None: return "mdi:help-circle-outline"

        # FVE Panely
        if any(x in self._key for x in ["pv_power", "pv1", "pv2"]):
            return "mdi:solar-power" if (isinstance(val, (int, float)) and val > 0) else "mdi:solar-power-variant-outline"
        
        # Baterie (SOC)
        if "battery_soc" in self._key:
            if val > 90: return "mdi:battery"
            if val > 60: return "mdi:battery-70"
            if val > 40: return "mdi:battery-50"
            if val > 15: return "mdi:battery-20"
            return "mdi:battery-alert"

        # Baterie (Nabíjení/Vybíjení)
        if "battery_power" in self._key:
            if val > 0: return "mdi:battery-arrow-up" # Nabíjení
            if val < 0: return "mdi:battery-arrow-down" # Vybíjení
            return "mdi:battery-lock"

        # Síť (Grid)
        if "grid_power" in self._key:
            if val > 0: return "mdi:transmission-tower-export" # Přetok do sítě
            if val < 0: return "mdi:transmission-tower-import" # Odběr ze sítě
            return "mdi:transmission-tower"

        # Stav střídače
        if self._key == "status":
            if val == "Normal": return "mdi:check-circle-outline"
            if val == "Fault": return "mdi:alert-circle-outline"
            return "mdi:pause-circle-outline"

        return self._info[6] if len(self._info) > 6 else super().icon

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
        data = res.get("Data", [])
        info_field = res.get("Information", [])
        
        # Index, Faktor, Typ dat
        idx, factor, dtype = self._info[3], self._info[4], self._info[5]

        try:
            val = None
            if dtype == 0: # Standardní Unsigned Int
                val = data[idx]
            elif dtype == 1: # Signed Int (pro záporné hodnoty jako Grid Power)
                val = data[idx]
                if val > 32767: val -= 65536
            elif dtype == 2: # Double Word (32-bit)
                val = (data[idx[0]] * 65536) + data[idx[1]]
            elif dtype == 3: # Textové stavy (Mode/Status)
                raw = data[idx]
                if self._key == "mode": return SOLAX_MODES.get(raw, f"Neznámý ({raw})")
                return SOLAX_STATES.get(raw, f"Neznámý ({raw})")
            elif dtype == 7: # Informační pole (Sériová čísla)
                return info_field[idx]
            
            if val is not None:
                return round(val * factor, 2)
        except Exception as e:
            _LOGGER.error("Chyba při parsování dat pro %s: %s", self._key, e)
        return None
