from homeassistant import config_entries
import voluptuous as vol
from .const import DOMAIN

class SolaxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SolaX Local API."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Krok pro manuální zadání údajů uživatelem."""
        errors = {}
        
        # Schéma formuláře definujeme bokem pro čistotu
        DATA_SCHEMA = vol.Schema({
            vol.Required("ip"): str,
            vol.Required("password"): str,
            vol.Optional("scan_interval", default=6): int,
        })

        if user_input is not None:
            # Zde by se časem dala přidat kontrola, zda je IP dostupná
            return self.async_create_entry(
                title=f"SolaX {user_input['ip']}", 
                data=user_input
            )

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )