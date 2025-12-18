import aiohttp
import async_timeout
import voluptuous as vol
from homeassistant import config_entries
from .const import DOMAIN

class SolaxConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for SolaX Local API."""
    VERSION = 1

    async def _test_connection(self, ip, password):
        """Ověří, zda se lze ke střídači připojit a zda je heslo správné."""
        url = f"http://{ip}/"
        payload = f"optType=ReadRealTimeData&pwd={password}"
        try:
            async with aiohttp.ClientSession() as session:
                with async_timeout.timeout(5):
                    async with session.post(url, data=payload) as response:
                        if response.status != 200:
                            return "cannot_connect"
                        res = await response.json(content_type=None)
                        if not res.get("Data"):
                            return "invalid_auth"
                        return None
        except Exception:
            return "cannot_connect"

    async def async_step_user(self, user_input=None):
        """Krok pro manuální zadání údajů uživatelem."""
        errors = {}
        
        DATA_SCHEMA = vol.Schema({
            vol.Required("ip", default="192.168.1.10"): str,
            vol.Required("password"): str,
            vol.Optional("scan_interval", default=10): vol.All(vol.Coerce(int), vol.Range(min=5, max=60)),
        })

        if user_input is not None:
            # Validace spojení před vytvořením entity
            error = await self._test_connection(user_input["ip"], user_input["password"])
            if not error:
                return self.async_create_entry(
                    title=f"SolaX Inverter ({user_input['ip']})", 
                    data=user_input
                )
            else:
                errors["base"] = error

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )
