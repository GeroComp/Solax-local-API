<p align="center">
  <img src="custom_components/solax_local_api/images/logo.png" alt="SolaX Logo" width="200"/>
</p>

# <img src="custom_components/solax_local_api/images/icon.png" alt="SolaX Logo" width="30"/> SolaX Inverter Local API

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![version](https://img.shields.io/github/v/release/GeroComp/Solax-local-API?style=for-the-badge)](https://github.com/GeroComp/Solax-local-API/releases)
![License](https://img.shields.io/github/license/GeroComp/Solax-local-API?style=for-the-badge)


Tato integrace umožňuje lokální monitorování střídače **SolaX Hybrid G4** v Home Assistant.  
Komunikace probíhá přímo přes lokální síť (LAN/WiFi), bez závislosti na cloudu a s bleskovou odezvou.

---

## ✨ Vlastnosti
- **Rychlá odezva**: Aktualizace dat každých 6–10 sekund (nastavitelné).
- **Lokální soukromí**: Data neopouštějí vaši síť.
- **Efektivní sběr**: Využívá `DataUpdateCoordinator` pro hromadný odběr 45+ senzorů jedním dotazem.
- **Dynamické ikony**: Ikony se mění podle stavu baterie, výroby panelů a směru toku energie.
- **Nativní podpora**: Plně kompatibilní s Home Assistant Energy Dashboardem.

---

## ⚡ Nastavení Energy Dashboardu
Pro správné zobrazení statistik v Energy panelu použijte tyto entity:

| Sekce v Energy Dashboardu | Entita v Home Assistant |
| :--- | :--- |
| **Výroba panelů (Solar production)** | `sensor.solax_api_solar_total` |
| **Odběr ze sítě (Grid consumption)** | `sensor.solax_api_grid_in_total` |
| **Návrat do sítě (Return to grid)** | `sensor.solax_api_grid_out_total` |
| **Nabíjení baterie (Battery storage - In)** | `sensor.solax_api_battery_in_total` |
| **Vybíjení baterie (Battery storage - Out)** | `sensor.solax_api_battery_out_total` |

> [!TIP]
> Po prvním nastavení může trvat až 2 hodiny, než Home Assistant začne v Energy Dashboardu zobrazovat první grafy.

---

## ⚙️ Instalace

### Manuální instalace
1. Stáhněte si repozitář a zkopírujte složku `solax_local_api` do adresáře `custom_components` ve vaší instalaci Home Assistant.
2. Restartujte Home Assistant.
3. V menu **Nastavení -> Zařízení a služby** klikněte na **Přidat integraci**.
4. Vyhledejte **SolaX Inverter Local API**.

---

## 📝 Konfigurace
Během nastavování budete vyzváni k zadání:
- **IP adresa**: Lokální IP adresa střídače v rámci vaší sítě.
- **Heslo / PIN**: PIN kód (obvykle natištěný na WiFi dongle) nebo sériové číslo dongle (dle verze firmware).
- **Interval aktualizace**: Doporučeno 6–10 sekund (příliš nízký interval může přetěžovat API dongle).

---

## 📊 Hlavní sledované entity
- **Výkon**: Celkový AC výkon, výkon z panelů (PV1+PV2), okamžitý výkon baterie (včetně směru toku).
- **Baterie**: SoC (%), napětí, proud, teplota, BMS status (OK/Chyba).
- **Energie**: Celková výroba, dnešní zisky, přetoky do sítě (vše s podporou statistik).
- **Stavy**: Provozní režim střídače (Self-use, Feed-in priority, atd.) a systémový status (Normal, Fault, Wait).
- **Diagnostika**: Sériové číslo střídače, verze firmware a nominální výkon.

---

## 📂 Struktura projektu
- `__init__.py`: Inicializace asynchronních platforem.
- `sensor.py`: Hlavní logika, dynamické ikony a zpracování 32-bitových registrů.
- `const.py`: Definice mapování indexů a typů dat (Signed, Long, PV sum).
- `config_flow.py`: Uživatelské rozhraní pro nastavení s validací spojení.
- `manifest.json`: Metadata a definice závislostí.
- `translations/cs.json`: Kompletní česká lokalizace.

---

## 🚀 Roadmap
- [ ] Podpora pro více střídačů v jedné síti.
- [ ] Implementace ovládacích prvků (Switch pro změnu pracovního módu).
- [ ] Rozšířená diagnostika pro třífázové systémy (napětí na jednotlivých fázích).

---
**Disclaimer**: Tato integrace není oficiálním produktem společnosti SolaX Power. Použití je na vlastní riziko.
