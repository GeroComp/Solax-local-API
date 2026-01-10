<p align="center">
  <img src="https://brands.home-assistant.io/_/solax_local_api/logo.png" alt="SolaX Logo" width="200"/>
</p>

# <img src="https://brands.home-assistant.io/_/solax_local_api/icon.png" alt="SolaX Icon" width="30"/> SolaX Inverter Local API

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![version](https://img.shields.io/github/v/release/GeroComp/Solax-local-API?style=for-the-badge)](https://github.com/GeroComp/Solax-local-API/releases)
![Discovery](https://img.shields.io/badge/discovery-DHCP-orange?style=for-the-badge)
![License](https://img.shields.io/github/license/GeroComp/Solax-local-API?style=for-the-badge)

Tato integrace umožňuje lokální monitorování střídače **SolaX Hybrid G4** v Home Assistant.
Komunikace probíhá přímo přes lokální síť (LAN/WiFi), bez závislosti na cloudu a s bleskovou odezvou.

---

## ✨ Vlastnosti
- **Zero-Config Discovery**: Automatická detekce střídače v síti (není třeba hledat IP adresu).
- **Rychlá odezva**: Aktualizace dat každých 6–10 sekund (nastavitelné).
- **Lokální soukromí**: Data neopouštějí vaši síť.
- **Efektivní sběr**: Využívá `DataUpdateCoordinator` pro hromadný odběr 45+ senzorů jedním dotazem.
- **Dynamické ikony**: Ikony se mění podle stavu baterie, výroby panelů a směru toku energie.
- **Nativní podpora**: Plně kompatibilní s Home Assistant Energy Dashboardem.

---

## 🔍 Automatické vyhledávání (Discovery)
Integrace podporuje funkci **Auto-Discovery**. Jakmile do své sítě připojíte střídač SolaX s Pocket Wi-Fi donglem, Home Assistant jej sám rozpozná.

V sekci **Zařízení a služby** uvidíte nové oznámení:
> **Zjištěno: SolaX** > *SolaX Power*

Klikněte na tlačítko **Přidat** (Configure). Integrace automaticky předvyplní zjištěnou IP adresu, vy pouze zadáte přístupové heslo.

> [!NOTE]
> **Detekce střídače v síti může trvat 1 až 2 minuty.**
> Pokud se zařízení ani po této době nezobrazí, přidejte integraci ručně a zadejte IP adresu Vašeho střídače přímo.

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
2. **Restartujte Home Assistant.**
3. Počkejte několik sekund – střídač by měl být automaticky detekován (vyskočí upozornění).
4. Pokud se tak nestane, jděte do **Nastavení -> Zařízení a služby -> Přidat integraci** a vyhledejte **SolaX Inverter Local API**.

---

## 📝 Konfigurace
Během nastavování budete vyzváni k zadání:
- **IP adresa**: Předvyplněno automaticky při detekci, jinak zadejte ručně.
- **Heslo / PIN**: Heslo pro přihlášení k Pocket Wi-Fi (obvykle natištěné na donglu).
- **Interval aktualizace**: Doporučeno 6–10 sekund.

---

## 📊 Hlavní sledované entity
- **Výkon**: Celkový AC výkon, výkon z panelů (PV1+PV2), okamžitý výkon baterie.
- **Baterie**: SoC (%), napětí, proud, teplota, BMS status.
- **Energie**: Celková výroba, dnešní zisky, přetoky do sítě.
- **Stavy**: Provozní režim střídače a systémový status (Normal, Fault, Wait).
- **Diagnostika**: Sériové číslo střídače, verze firmware a nominální výkon.

---

## 📂 Struktura projektu
- `__init__.py`: Inicializace a správa instance zařízení.
- `sensor.py`: Logika senzorů a zpracování 32-bitových registrů.
- `const.py`: Definice registrů, koeficientů a mapování stavů.
- `config_flow.py`: UI pro nastavení a DHCP discovery logika.
- `manifest.json`: Metadata a definice pro automatické vyhledávání.
- `translations/`: Kompletní česká a anglická lokalizace.

---

**Disclaimer**: Tato integrace není oficiálním produktem společnosti SolaX Power. Použití je na vlastní riziko.
