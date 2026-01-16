<p align="center">
  <img src="https://brands.home-assistant.io/_/solax_local_api/logo.png" alt="SolaX Logo" width="200"/>
</p>

# <img src="https://brands.home-assistant.io/_/solax_local_api/icon.png" alt="SolaX Icon" width="30"/> SolaX Inverter Local API

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![version](https://img.shields.io/github/v/release/GeroComp/Solax-local-API?style=for-the-badge)](https://github.com/GeroComp/Solax-local-API/releases)
![Discovery](https://img.shields.io/badge/discovery-DHCP-orange?style=for-the-badge)
![License](https://img.shields.io/github/license/GeroComp/Solax-local-API?style=for-the-badge)

Tato integrace umožňuje **lokální monitorování** střídačů **SolaX Hybrid G4** v Home Assistant.
Komunikace probíhá přímo přes lokální síť (LAN/WiFi) pomocí HTTP requestů na Pocket Wi-Fi dongle, bez závislosti na cloudu.

---

## ✨ Vlastnosti
- **Zero-Config Discovery**: Automatická detekce střídače v síti na základě DHCP (vyhledává zařízení Espressif s Pocket Wi-Fi).
- **Dynamický interval**: Možnost změnit rychlost aktualizace dat (6s až 5 min) okamžitě přes entitu v Dashboardu.
- **Robustní připojení**: Optimistický start – integrace se načte i v noci, když střídač spí (entity jsou nedostupné, ale systém nehlásí chybu).
- **Efektivní sběr**: Využívá `DataUpdateCoordinator` pro stažení všech dat jedním dotazem.
- **Chytré ikony**: Ikony se dynamicky mění podle SoC baterie, toku energie (import/export) a denní doby.
- **Energy Dashboard**: Plná kompatibilita s nativním energetickým panelem HA.

---

## 🔍 Automatické vyhledávání (Discovery)
Integrace podporuje funkci **Auto-Discovery**. Jakmile se střídač s Pocket Wi-Fi donglem připojí k síti, Home Assistant jej rozpozná.

V sekci **Zařízení a služby** uvidíte nové oznámení:
> **Zjištěno: SolaX Local API** > *SolaX Power*

Klikněte na tlačítko **Přidat** (Configure). Integrace automaticky předvyplní zjištěnou IP adresu, vy pouze zadáte přístupové heslo k API (tzv. registrační číslo donglu).

---

## ⚡ Nastavení Energy Dashboardu
Pro správné zobrazení statistik v Energy panelu použijte tyto entity (pozor, názvy se liší od starších verzí):

| Sekce v Energy Dashboardu | Entita v Home Assistant |
| :--- | :--- |
| **Výroba panelů (Solar production)** | `sensor.solax_solar_total` |
| **Odběr ze sítě (Grid consumption)** | `sensor.solax_grid_in_total` |
| **Návrat do sítě (Return to grid)** | `sensor.solax_grid_out_total` |
| **Nabíjení baterie (Battery storage - In)** | `sensor.solax_battery_in_total` |
| **Vybíjení baterie (Battery storage - Out)** | `sensor.solax_battery_out_total` |

> [!TIP]
> Senzory `_total` jsou typu `TOTAL_INCREASING`, což je vyžadováno pro správné dlouhodobé statistiky.

---

## ⚙️ Instalace a Konfigurace

### Manuální instalace
1. Stáhněte si repozitář a zkopírujte složku `solax_local_api` do adresáře `custom_components`.
2. **Restartujte Home Assistant.**
3. Integrace by měla být automaticky objevena. Pokud ne, přidejte ji přes **Nastavení -> Zařízení a služby -> Přidat integraci -> SolaX Local API**.

### Konfigurace
- **IP adresa**: Lokální IP adresa Pocket Wi-Fi donglu.
- **Heslo**: Heslo k API (často shodné se sériovým číslem donglu nebo registračním kódem).
- **Interval**: Výchozí interval je 10 sekund.

---

## 📊 Entity a Ovládání

### Hlavní senzory
Integrace vytváří cca 50 senzorů, včetně:
- **PV**: Napětí, proud a výkon pro oba stringy (PV1, PV2).
- **Baterie**: SoC, napětí, proud, teplota, BMS status a zbývající energie.
- **Síť (Grid)**: Import/Export (aktuální W i celkové kWh).
- **Inverter**: Teploty, frekvence, účiník, sériové číslo.

### Ovládací prvky (Novinka)
Integrace nyní obsahuje entitu typu `Select`:
- **Scan Interval** (`select.solax_scan_interval`): Umožňuje přepínat rychlost vyčítání dat za chodu.
  - *Možnosti:* 6s (Agresivní), 10s, ..., až 5 minut.
  - Změna se projeví okamžitě a uloží se do konfigurace.

### Diagnostika
- **Aktuální interval skenování** (`sensor.solax_interval_diagnostic`): Zobrazuje reálný čas v sekundách mezi posledními aktualizacemi dat.

---

## 📂 Struktura projektu
- `__init__.py`: Inicializace integrace a načtení platforem.
- `coordinator.py`: Správa stahování dat z API a session handling.
- `sensor.py`: Definice senzorů, parsování dat a logika ikon.
- `select.py`: Implementace přepínače pro změnu intervalu aktualizace.
- `const.py`: Tabulky registrů, konstanty a mapování modelů.
- `config_flow.py`: Průvodce nastavením a DHCP discovery.
- `manifest.json`: Definice verze a závislostí.

---

**Disclaimer**: Tato integrace není oficiálním produktem společnosti SolaX Power. Použití je na vlastní riziko.
