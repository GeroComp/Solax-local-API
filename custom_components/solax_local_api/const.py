"""Constants for the SolaX Local API integration."""

# Změněno z "solax_local" na "solax_local_api"
DOMAIN = "solax_local_api"

# Mapování režimů pro textové senzory
SOLAX_MODES = {
    0: "Self Use Mode", 
    1: "Force Time Use", 
    2: "Back Up Mode", 
    3: "Feed-in Priority"
}

SOLAX_STATES = {
    0: "Waiting", 1: "Checking", 2: "Normal", 3: "Off", 
    4: "Permanent Fault", 5: "Updating", 6: "EPS Check", 
    7: "EPS Mode", 8: "Self Test", 9: "Idle", 10: "Standby"
}

# Kompletní tabulka všech 35+ senzorů
# Formát: "id": ["Název", "Jednotka", "Device_Class", "Index", "Koeficient", "Typ_dat"]
# Typy dat: 0=normal, 1=signed (+/-), 2=long (součet dvou registrů), 3=text/special
SENSOR_TYPES = {
    # --- AC Podrobnosti ---
    "acu1": ["L1 Voltage", "V", "voltage", 0, 0.1, 0],
    "acu2": ["L2 Voltage", "V", "voltage", 1, 0.1, 0],
    "acu3": ["L3 Voltage", "V", "voltage", 2, 0.1, 0],
    "aci1": ["L1 Current", "A", "current", 3, 0.1, 1],
    "aci2": ["L2 Current", "A", "current", 4, 0.1, 1],
    "aci3": ["L3 Current", "A", "current", 5, 0.1, 1],
    "acp1": ["L1 Power", "W", "power", 6, 1, 1],
    "acp2": ["L2 Power", "W", "power", 7, 1, 1],
    "acp3": ["L3 Power", "W", "power", 8, 1, 1],
    "ac_power": ["Total AC Power", "W", "power", 9, 1, 1],
    "acf1": ["L1 Frequency", "Hz", "frequency", 16, 0.01, 0],
    "acf2": ["L2 Frequency", "Hz", "frequency", 17, 0.01, 0],
    "acf3": ["L3 Frequency", "Hz", "frequency", 18, 0.01, 0],

    # --- PV Podrobnosti ---
    "pv1u": ["PV1 Voltage", "V", "voltage", 10, 0.1, 0],
    "pv2u": ["PV2 Voltage", "V", "voltage", 11, 0.1, 0],
    "pv1i": ["PV1 Current", "A", "current", 12, 0.1, 0],
    "pv2i": ["PV2 Current", "A", "current", 13, 0.1, 0],
    "pv1p": ["PV1 Power", "W", "power", 14, 1, 0],
    "pv2p": ["PV2 Power", "W", "power", 15, 1, 0],
    "pv_power": ["Total PV Power", "W", "power", (14, 15), 1, 4], # Speciální typ 4: součet 14+15

    # --- Baterie ---
    "battery_voltage": ["Battery Voltage", "V", "voltage", 39, 0.01, 0],
    "battery_current": ["Battery Current", "A", "current", 40, 0.01, 1],
    "battery_power": ["Battery Power", "W", "power", 41, 1, 1],
    "battery_soc": ["Battery SoC", "%", None, 103, 1, 0],
    "battery_remain": ["Battery Remain Energy", "kWh", "energy", 106, 0.1, 0],
    "battery_temperature": ["Battery Temperature", "°C", "temperature", 105, 1, 0],
    "battery_bms": ["Battery BMS status", None, None, 45, 1, 5], # Speciální typ 5: OK/Fail

    # --- Souhrny a Statistika ---
    "grid_power": ["Feed-in Power", "W", "power", 34, 1, 1],
    "consumption": ["Consumption", "W", "power", 47, 1, 1],
    "energy_total": ["Energy total", "kWh", "energy", (69, 68), 0.1, 2],
    
    # --- Dnešní statistiky ---
    "grid_out_today": ["Grid out today", "kWh", "energy", 90, 0.01, 0],
    "grid_in_today": ["Grid in today", "kWh", "energy", 92, 0.01, 0],
    "battery_out_today": ["Battery discharge today", "kWh", "energy", 78, 0.1, 0],
    "battery_in_today": ["Battery charge today", "kWh", "energy", 79, 0.1, 0],
    "energy_today": ["Energy today", "kWh", "energy", 82, 0.1, 0],
    "energy_bat_today": ["Energy incl battery today", "kWh", "energy", 70, 0.1, 0],

    # --- Celkové hodnoty pro Energy Panel ---
    "solar_total": ["Solar energy total", "kWh", "energy", (81, 80), 0.1, 2],
    "grid_out_total": ["Grid out total", "kWh", "energy", (87, 86), 0.01, 2],
    "grid_in_total": ["Grid in total", "kWh", "energy", (89, 88), 0.01, 2],
    "consumption_total": ["Consumption total", "kWh", "energy", 88, 0.01, 0],
    "battery_out_total": ["Battery discharge total", "kWh", "energy", (75, 74), 0.1, 2],
    "battery_in_total": ["Battery charge total", "kWh", "energy", (77, 76), 0.1, 2],

    # --- Módy a Informace o střídači ---
    "mode": ["Battery Operation Mode", None, None, 168, 1, 3],
    "state": ["Inverter Operation Mode", None, None, 19, 1, 3],
    "type": ["Inverter Type", None, None, "type", 1, 6], # Speciální typ 6: Attr střídače
    "inverter_sn": ["Inverter SN", None, None, 2, 1, 7], # Speciální typ 7: Information[2]
    "nominal_power": ["Inverter Nominal Power", "kW", None, 0, 1, 7], # Information[0]

    # --- Testovací parametry ---
    "inverter_temperature_inner": ["Inverter Temperature inner", "°C", "temperature", 46, 1, 0],
    "inverter_temperature": ["Inverter Temperature", "°C", "temperature", 54, 1, 0],
}