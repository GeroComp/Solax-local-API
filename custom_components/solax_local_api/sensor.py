import logging
from datetime import timedelta
import async_timeout3

from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.components.sensor import (
    SensorEntity, 
    SensorStateClass, 
    SensorDeviceClass
)
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator, 
    UpdateFailed,
    CoordinatorEntity
)
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import EntityCategory

# Importování mapovacích tabulek z const.py
from .const import DOMAIN, SENSOR_TYPES, SOLAX_MODES, SOLAX_STATES, SOLAX_INVERTER_TYPES

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
    """Třída pro stahování dat ze střídače."""

    def __init__(self, hass, ip, pwd, scan_interval):
        super().__init__(
            hass, _LOGGER, name="Solax Data",
            update_interval=timedelta(seconds=scan_interval),
        )
        self.ip = ip
        self.pwd = pwd
        self.session = async_get_clientsession(hass)

    async def _async_update_data(self):
        url = f"http://{self.ip}/"
        payload = f"optType=ReadRealTimeData&pwd={self.pwd}"
        
        try:
            async with async_timeout.timeout(5):
                async with self.session.post(url, data=payload) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Chyba střídače: {response.status}")
                    
                    data = await response.json(content_type=None)
                    if not data:
                        raise UpdateFailed("Prázdná data ze střídače")
                    return data
        except Exception as err:
            raise UpdateFailed(f"Chyba komunikace: {err}")

class SolaxSensor(CoordinatorEntity, SensorEntity):
    """Senzor Solax bez odkazu na webové rozhraní."""

    def __init__(self, coordinator, sensor_key, info, entry):
        """Inicializace senzoru."""
        super().__init__(coordinator)
        self._key = sensor_key
        self._info = info
        self._entry = entry
        
        self.entity_id = f"sensor.solax_{sensor_key}"
        self._attr_name = info[0]
        self._attr_unique_id = f"solax_{sensor_key}_{entry.entry_id}"
        self._attr_native_unit_of_measurement = info[1]
        
        # Automatické nastavení DeviceClass a StateClass
        unit = info[1]
        if unit == "kWh":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            self._attr_device_class = SensorDeviceClass.ENERGY
        elif unit == "W":
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_device_class = SensorDeviceClass.POWER
        elif unit == "V":
            self._attr_device_class = SensorDeviceClass.VOLTAGE
        elif unit == "A":
            self._attr_device_class = SensorDeviceClass.CURRENT
        elif unit == "°C":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
        
        # Diagnostické senzory
        diagnostic_keys = {
            "type", "inverter_sn", "nominal_power", "firmware",
            "inverter_temperature_inner", "inverter_temperature",
            "battery_temperature", "battery_bms", "mode", "state"
        }
        if sensor_key in diagnostic_keys:
            self._attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def device_info(self) -> DeviceInfo:
        """Informace o zařízení (zde je odstraněn configuration_url)."""
        fw_version = "Načítání..."
        model_type = "Hybrid Inverter"
        sn_value = None

        if self.coordinator.data:
            fw_version = self.coordinator.data.get("ver", "Neznámý")
            info_field = self.coordinator.data.get("Information", [])
            if len(info_field) > 2:
                sn_value = info_field[2]
                raw_model_code = info_field[1]
                model_type = SOLAX_INVERTER_TYPES.get(raw_model_code, f"Model {raw_model_code}")

        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name=f"SolaX {model_type}",
            manufacturer="SolaX Power",
            model=model_type,
            sw_version=fw_version,
            serial_number=sn_value,
            # Parametr configuration_url je odstraněn pro skrytí tlačítka v UI
        )

    @property
    def native_value(self):
        """Zpracování a výpočet hodnoty ze syrových dat."""
        if not self.coordinator.data:
            return None
            
        res = self.coordinator.data
        idx, factor, dtype = self._info[3], self._info[4], self._info[5]
        data = res.get("Data", [])
        info_field = res.get("Information", [])

        try:
            val = None
            if dtype == 8: return res.get("ver")
            
            if dtype == 0: val = data[idx]
            elif dtype == 1:
                val = data[idx]
                if val > 32767: val -= 65536
            elif dtype == 2: val = (data[idx[0]] * 65536) + data[idx[1]]
            elif dtype == 3:
                raw = data[idx]
                return SOLAX_MODES.get(raw, f"Neznámý ({raw})") if self._key == "mode" else SOLAX_STATES.get(raw, f"Neznámý ({raw})")
            elif dtype == 4: val = data[idx[0]] + data[idx[1]]
            elif dtype == 5: return "OK" if data[idx] == 1 else "Chyba"
            elif dtype == 7: return info_field[idx]
            elif dtype == 9:
                raw = info_field[idx]
                return SOLAX_INVERTER_TYPES.get(raw, f"Model {raw}")
                
            return round(val * factor, 2) if val is not None else None
        except (IndexError, TypeError, KeyError):
            return None

    @property
    def icon(self):
        """Přiřazení ikon podle klíče senzoru."""
        key = self._key.lower()
        if "pv" in key: return "mdi:solar-power-variant"
        if "battery_soc" in key: return "mdi:battery-high"
        if "battery" in key: return "mdi:battery-charging"
        if "grid" in key: return "mdi:transmission-tower"
        if "consumption" in key: return "mdi:home-lightning-bolt"
        if "temperature" in key: return "mdi:thermometer"
        return super().icon

