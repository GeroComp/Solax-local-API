import logging
from homeassistant.components.sensor import (
    SensorEntity, 
    SensorStateClass, 
    SensorDeviceClass
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.const import EntityCategory

# Importování mapovacích tabulek z const.py
from .const import DOMAIN, SENSOR_TYPES, SOLAX_MODES, SOLAX_STATES, SOLAX_INVERTER_TYPES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass, entry, async_add_entities):
    """Nastavení senzorů na základě konfigurace v UI."""
    
    # Získání již běžícího koordinátora
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # 1. Standardní senzory
    entities = [SolaxSensor(coordinator, key, info, entry) for key, info in SENSOR_TYPES.items()]
    
    # 2. Diagnostický senzor intervalu
    entities.append(SolaxIntervalDiagnostic(coordinator, entry))

    async_add_entities(entities)


class SolaxIntervalDiagnostic(CoordinatorEntity, SensorEntity):
    """Diagnostický senzor zobrazující aktuální interval aktualizace."""

    _attr_has_entity_name = True
    _attr_name = "Aktuální interval skenování"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = "s"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"solax_interval_diagnostic_{entry.entry_id}"
        self.entity_id = f"sensor.solax_interval_diagnostic"
        
        # DEFINICE IKONY PŘÍMO V INITU (Upraveno na timer-check-outline)
        self._attr_icon = "mdi:timer-check-outline"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)}
        )

    @property
    def native_value(self):
        """Vrátí aktuální nastavený interval v sekundách."""
        if self.coordinator.update_interval:
            return int(self.coordinator.update_interval.total_seconds())
        return None


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
        unit = self._attr_native_unit_of_measurement

        # --- 1. DYNAMICKÁ BATERIE (SOC %) ---
        if "battery" in key and "soc" in key:
            if val is None: return "mdi:battery-unknown"
            try:
                soc = int(val)
                if soc >= 95: return "mdi:battery"
                if soc <= 5: return "mdi:battery-outline"
                
                rounded = round(soc / 10) * 10
                return f"mdi:battery-{rounded}"
            except (ValueError, TypeError):
                return "mdi:battery-50"

        # --- 2. BATERIE - Napětí / Proud / Výkon ---
        if "battery_power" in key or "battery_current" in key:
            if val is None: return "mdi:battery-unknown"
            
            is_idle = False
            try:
                state_def = SENSOR_TYPES.get("state") 
                if state_def and self.coordinator.data:
                    state_idx = state_def[3] 
                    data_list = self.coordinator.data.get("Data", [])
                    if len(data_list) > state_idx:
                        raw_state_val = data_list[state_idx]
                        if raw_state_val in [0, 1, 3, 9, 10]:
                            is_idle = True
            except Exception:
                pass 

            if is_idle: return "mdi:battery-off-outline"
            if val == 0: return "mdi:battery-outline"
            if val < 0: return "mdi:battery-arrow-down"
            elif val > 0: return "mdi:battery-arrow-up-outline"
        
        # Baterie - Napětí
        if "battery" in key and "voltage" in key:
            return "mdi:battery-charging"

        # --- 3. BATERIE - Ostatní ---
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

        # --- 6. SÍŤ (GRID) ---
        if "feed" in key or "feed" in name:
            if val is None: return "mdi:transmission-tower-off"
            if val < 0: return "mdi:transmission-tower-export"
            if val > 0: return "mdi:transmission-tower-import"
            return "mdi:transmission-tower"

        if "grid" in key and "in" in key:
            return "mdi:transmission-tower-export"
        if "grid" in key and "out" in key:
            return "mdi:transmission-tower-import"

        # --- 7. DYNAMICKÉ TEPLOTY ---
        if "temperature" in key:
            if val is None: return "mdi:thermometer-off"
            
            is_idle = False
            if "inverter" in key:
                try:
                    state_def = SENSOR_TYPES.get("state")
                    if state_def and self.coordinator.data:
                        state_idx = state_def[3]
                        data_list = self.coordinator.data.get("Data", [])
                        if len(data_list) > state_idx:
                            raw_state_val = data_list[state_idx]
                            if raw_state_val in [0, 1, 3, 9, 10]:
                                is_idle = True
                except Exception:
                    pass

            if is_idle:
                return "mdi:thermometer-off"

            try:
                temp = float(val)
                if temp < 0: return "mdi:thermometer-minus"
                if temp < 30: return "mdi:thermometer-low"
                if temp < 40: return "mdi:thermometer"
                if temp < 60: return "mdi:thermometer-high"
                return "mdi:thermometer-alert"
            except (ValueError, TypeError):
                return "mdi:thermometer"

        # --- 8. DIAGNOSTIKA ---
        if "sn" in key: return "mdi:barcode"
        if "firmware" in key: return "mdi:chip"
        if "type" in key: return "mdi:solar-power"
        if "bms" in key: return "mdi:battery-heart-variant"
        if "mode" in key or "state" in key: return "mdi:state-machine"
        if "nominal" in key: return "mdi:lightning-bolt-circle"

        # --- SPECIÁLNÍ: Solar energy total ---
        if "solar" in name and "total" in name:
            return "mdi:solar-power"

        # --- FVE (PV) - KOMPLETNÍ LOGIKA S NOČNÍM REŽIMEM ---
        if "pv" in key:
            
            is_night = False
            try:
                if val is not None and float(val) == 0 and "power" in key:
                    is_night = True
            except (ValueError, TypeError):
                pass

            if "pv1" in key:
                if "current" in key: return "mdi:current-dc"        
                if "power" in key and is_night: return "mdi:solar-panel-large"
                return "mdi:solar-power-variant-outline"

            if "pv2" in key:
                if "current" in key: return "mdi:current-dc"        
                if "power" in key and is_night: return "mdi:solar-panel"
                return "mdi:solar-power-variant"
            
            if "power" in key:
                if is_night: return "mdi:solar-power-variant"
                return "mdi:solar-power-variant-outline"

            return "mdi:solar-panel" 

        # --- 9. SPECIFICKÉ IKONY PRO AC VELIČINY ---
        if "ac_power" in key:
             return "mdi:lightning-bolt-circle"

        if "frequency" in key or unit == "Hz":
            return "mdi:waveform"
        if "current" in key or unit == "A":
            return "mdi:current-ac"
        if "voltage" in key or unit == "V":
            return "mdi:sine-wave"
        if "power" in key or unit == "W":
             return "mdi:flash"

        # --- 10. OBECNÉ IKONY (FALLBACK) ---
        if "pv" in key: return "mdi:solar-power-variant"
        if "battery_soc" in key: return "mdi:battery-50"
        if "battery" in key: return "mdi:battery-charging"
        if "grid" in key: return "mdi:transmission-tower"
        
        return super().icon