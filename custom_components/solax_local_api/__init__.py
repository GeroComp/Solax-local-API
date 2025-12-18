from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Nastavení integrace z konfiguračního záznamu v UI."""
    
    # Inicializujeme úložiště dat pro novou doménu solax_local_api
    # To zabrání konfliktům, pokud by v systému zůstaly zbytky staré integrace
    hass.data.setdefault(DOMAIN, {})
    
    # Předání nastavení (IP, heslo) do platformy 'sensor'
    # Používáme modernější metodu async_forward_entry_setups (množné číslo)
    await hass.config_entries.async_forward_entry_setups(entry, ["sensor"])
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Odstranění integrace z Home Assistanta."""
    
    # Korektní ukončení platformy sensor
    unload_ok = await hass.config_entries.async_forward_entry_unload(entry, "sensor")
    
    # Po úspěšném odstranění vyčistíme data z paměti
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    
    return unload_ok