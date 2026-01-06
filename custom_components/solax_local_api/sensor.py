import logging
from datetime import timedelta
import async_timeout
import asyncio

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
from homeassistant.const import EntityCategory, CONF_HOST, CONF_PASSWORD

# Importování mapovacích tabulek z const.py
from .const import DOMAIN, SENSOR_TYPES, SOLAX_MODES, SOLAX_STATES, SOLAX_INVERTER_TYPES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Nastavení senzorů na základě konfigurace v UI."""
    ip = entry.data[CONF_HOST]        
    pwd = entry.data[CONF_PASSWORD]   
    
    scan_interval = entry.data.get("scan_interval", 10)

    coordinator = SolaxUpdateCoordinator(hass, ip, pwd, scan_interval)
    
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        _LOGGER.warning("Nepodařilo se navázat prvotní spojení se střídačem: %s", ex)

    entities = [SolaxSensor(coordinator, key, info, entry) for key, info in SENSOR_TYPES.items()]
    async_add_entities(entities)

class SolaxUpdateCoordinator(DataUpdateCoordinator):
    """Třída pro stahování dat ze střídače přes lokální API."""

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
            async with async_timeout.timeout(10):
                async with self.session.post(url, data=payload) as response:
                    if response.status != 200:
                        raise UpdateFailed(f"Chyba střídače: {response.status}")
                    
                    data = await response.json(content_type=None)
                    if not data or "Data" not in data:
                        raise UpdateFailed("Neúplná data ze střídače")
                    return data
        except Exception as err:
            raise UpdateFailed(f"Chyba komunikace: {err}")

class SolaxSensor(CoordinatorEntity, SensorEntity):
    """Reprezentace senzoru SolaX."""

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

        # --- OPRAVA NÁZVU (Rename pojistka) ---
        if self._attr_name == "Grid in today total":
            self._attr_name = "Grid Import Total"
        elif self._attr_name == "Grid out today total": 
            self._attr_name = "Grid Export Total"
        
        # Automatické nastavení DeviceClass a StateClass
        unit = info[1]
        if unit == "kWh":
            self._attr_state_class = SensorStateClass.TOTAL_INCREASING
            self._attr_device_class = SensorDeviceClass.ENERGY
        elif unit == "W":
            self._attr_state_class = SensorStateClass.MEASUREMENT
            self._attr_device_class = SensorDeviceClass.POWER
        elif unit == "%":
            self._attr_device_class = SensorDeviceClass.BATTERY
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif unit == "V":
            self._attr_device_class = SensorDeviceClass.VOLTAGE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif unit == "A":
            self._attr_device_class = SensorDeviceClass.CURRENT
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif unit == "°C":
            self._attr_device_class = SensorDeviceClass.TEMPERATURE
            self._attr_state_class = SensorStateClass.MEASUREMENT
        elif unit == "Hz":
            self._attr_device_class = SensorDeviceClass.FREQUENCY
            self._attr_state_class = SensorStateClass.MEASUREMENT
        
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
        """Informace o zařízení včetně odkazu na webové rozhraní."""
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
            configuration_url=f"http://{self.coordinator.ip}",
        )

    @property
    def native_value(self):
        """Zpracování hodnoty ze syrových dat."""
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
        """Přiřazení ikon."""
        key = self._key.lower()
        name = (self._attr_name or "").lower()
        val = self.native_value

        # --- 1. DYNAMICKÉ IKONY (BATERIE) ---
        if "battery_power" in key or "battery_current" in key:
            if val is None: return "mdi:battery-unknown"
            if val < 0: return "mdi:battery-arrow-down"
            elif val > 0: return "mdi:battery-arrow-up-outline"
            else: return "mdi:battery-off-outline"
        
        # --- 2. BATERIE - ZBÝVAJÍCÍ ENERGIE (vs 11.5 kWh) ---
        if "remain" in key or "remain" in name:
            BATTERY_CAPACITY_KWH = 11.5 
            if val is None: return "mdi:battery-unknown"
            try:
                if float(val) > (BATTERY_CAPACITY_KWH / 2):
                    return "mdi:battery-check"
                else:
                    return "mdi:battery-check-outline"
            except (ValueError, TypeError):
                return "mdi:battery-alert"

        # --- 3. BATERIE - CHARGE / DISCHARGE ---
        if "discharge" in key or "discharge" in name:
            return "mdi:battery-arrow-down"
        if "charge" in key or "charge" in name:
            return "mdi:battery-arrow-up-outline"
            
        # --- 4. SPOTŘEBA DOMU (CONSUMPTION) ---
        is_consumption = "consumption" in key or "consumption" in name
        is_total = "total" in key or "total" in name

        if is_consumption and is_total:
            return "mdi:home-import-outline"
        if is_consumption:
            return "mdi:home-lightning-bolt"

        # --- 5. ENERGIE VČETNĚ BATERIE ---
        if "incl" in name and "battery" in name:
            return "mdi:home-battery"

        # --- 6. SÍŤ (GRID) - FEED-IN & IMPORT/EXPORT ---
        if "feed" in key or "feed" in name:
            if val is None: return "mdi:transmission-tower-off"
            if val < 0: return "mdi:transmission-tower-export"
            if val > 0: return "mdi:transmission-tower-import"
            return "mdi:transmission-tower"

        if "grid" in key and "in" in key:
            return "mdi:transmission-tower-export"

        if "grid" in key and "out" in key:
            return "mdi:transmission-tower-import"

        # --- 7. DYNAMICKÉ TEPLOTY (UPRAVENÁ LOGIKA) ---
        if "temperature" in key:
            if val is None: return "mdi:thermometer-off"
            try:
                temp = float(val)
                
                # Pokud je teplota přesně 0 a jde o střídač -> vypnuto (přeškrtnutý teploměr)
                if temp == 0 and "inverter" in key: return "mdi:thermometer-off"

                if temp < 0: return "mdi:thermometer-minus" # Pod 0
                if temp < 30: return "mdi:thermometer-low"  # 0 - 30
                if temp < 40: return "mdi:thermometer"      # 30 - 40
                if temp < 60: return "mdi:thermometer-high" # 40 - 60
                return "mdi:thermometer-alert"              # Nad 60
            except (ValueError, TypeError):
                return "mdi:thermometer"

        # --- 8. DIAGNOSTIKA A INFO ---
        if "sn" in key: return "mdi:barcode"
        
        if "firmware" in key: return "mdi:chip"
        
        if "type" in key: return "mdi:solar-power"
        if "bms" in key: return "mdi:battery-heart-variant"
        if "mode" in key or "state" in key: return "mdi:state-machine"
        if "nominal" in key: return "mdi:lightning-bolt-circle"

        # --- 9. OBECNÉ IKONY ---
        if "pv" in key: return "mdi:solar-power-variant"
        if "battery_soc" in key: return "mdi:battery-high"
        
        if "battery" in key: return "mdi:battery-charging"
        
        if "grid" in key: return "mdi:transmission-tower"
        
        if "frequency" in key or "hz" in (self._attr_native_unit_of_measurement or ""): 
            return "mdi:sine-wave"
        
        return super().icon