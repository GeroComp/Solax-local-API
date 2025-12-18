<p align="center">
  <img src="custom_components/solax_local_api/images/logo.png" alt="SolaX Logo" width="200"/>
</p>

# <img src="custom_components/solax_local_api/images/icon.png" alt="SolaX Logo" width="30"/> SolaX Inverter Local API

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![version](https://img.shields.io/github/v/release/GeroComp/Solax-local-API?style=for-the-badge)](https://github.com/GeroComp/Solax-local-API/releases)
[![License](https://img.shields.io/github/license/GeroComp/Solax-local-API?style=for-the-badge)](LICENSE)


---

## 🚀 First Public Release

- Core features:
  - Local API integration for SolaX inverters
  - Basic sensor support (status, power, energy)
  - Compatible with Home Assistant via custom component
- Ready for testing and community feedback




Tato integrace umožňuje lokální monitorování střídače **SolaX Hybrid G4** v Home Assistant.  
Komunikace probíhá přímo přes lokální síť (LAN/WiFi), bez závislosti na Cloudu.

---

## ✨ Vlastnosti
- **Rychlá odezva**: Aktualizace dat každých 6 sekund.  
- **Efektivní sběr**: Využívá `DataUpdateCoordinator` pro hromadný odběr 45+ senzorů jedním dotazem.  
- **Přehledné UI**: Automatické seskupení pod jedno zařízení s rozdělením na senzory a diagnostiku.  
- **Nativní podpora**: Plně kompatibilní s Home Assistant Energy Dashboardem.  

---

## 📂 Struktura integrace
- `__init__.py`: Inicializace a načtení integrace.  
- `sensor.py`: Hlavní logika, výpočty a definice zařízení (Device Registry).  
- `const.py`: Kompletní tabulka indexů a registrů pro senzory.  
- `config_flow.py`: Uživatelské rozhraní pro zadání IP adresy a hesla.  
- `manifest.json`: Metadata integrace.  
- `translations/cs.json`: Česká lokalizace pro nastavení.  
- `images/solax_logo.png`: Oficiální logo pro README a dokumentaci.  

---

## ⚙️ Instalace
1. Zkopírujte složku `solax_local` do adresáře `custom_components`.  
2. Restartujte Home Assistant.  
3. V menu **Nastavení -> Zařízení a služby** klikněte na **Přidat integraci**.  
4. Vyhledejte **SolaX Inverter Local**.  

---

## 📝 Konfigurace
Během nastavování budete vyzváni k zadání:  
- **IP adresa**: Lokální IP adresa střídače (např. `192.168.1.130`).  
- **Heslo**: PIN kód natištěný na vašem WiFi dongle.  

---

## 📊 Hlavní sledované entity
- **Výkon**: Celkový AC výkon, výkon z panelů (PV1+PV2), výkon baterie.  
- **Baterie**: SoC (%), napětí, proud, teplota, BMS status.  
- **Energie**: Celková výroba, dnešní zisky, přetoky do sítě.  
- **Stavy**: Provozní režim střídače a mód baterie.  

