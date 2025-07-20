# XCC Tepelné Čerpadlo - Home Assistant Integrace

Home Assistant integrace pro řadiče tepelných čerpadel XCC s podporou fotovoltaické integrace. Monitorujte a ovládejte váš systém tepelného čerpadla přímo z Home Assistant s automatickým objevováním entit a dvojjazyčnou podporou.

## 🏠 Funkce Home Assistant Integrace

- 🔧 **470+ nastavitelných polí** automaticky objevených napříč 6 konfiguračními stránkami
- 📊 **Živé monitorování dat** s hodnotami senzorů v reálném čase
- 🌐 **Dvojjazyčná podpora** (angličtina/čeština s automatickou detekcí)
- 📋 **Organizováno podle zařízení** (vytápění, FV, teplá voda, pomocný zdroj, atd.)

## 📦 Instalace

### 🚀 HACS Instalace (Doporučeno)

1. **Přidání vlastního repozitáře**:
   - Otevřete HACS v Home Assistant
   - Klikněte na 3 tečky (⋮) → "Custom repositories"
   - Přidejte repozitář: `https://github.com/pvyleta/xcc-integration`
   - Kategorie: `Integration`

2. **Instalace integrace**:
   - Jděte do HACS > Integrations
   - Vyhledejte "XCC Heat Pump Controller"
   - Klikněte na "Download" a restartujte Home Assistant

3. **Konfigurace integrace**:
   - Nastavení > Zařízení a služby > "Přidat integraci"
   - Vyhledejte "XCC Heat Pump Controller"
   - Zadejte údaje vašeho XCC řadiče

## 🔧 Vývoj a Testování

### Vývojové prostředí

1. **Klonování repozitáře:**
   ```bash
   git clone https://github.com/pvyleta/xcc-integration
   cd xcc-integration
   ```

2. **Vytvoření virtuálního prostředí:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Na Windows: venv\Scripts\activate
   ```

3. **Instalace závislostí:**
   ```bash
   pip install -r requirements.txt
   ```

### Spuštění testů

Integrace obsahuje komplexní testy pro zajištění spolehlivosti:

```bash
# Spuštění všech testů
python -m pytest tests/ -v
```



## 📚 Konfigurační stránky

Integrace automaticky objevuje entity z těchto XCC stránek:

| Stránka | Popis | Typické entity |
|---------|-------|----------------|
| **Topné okruhy** | Řízení teploty, časové programy | Teplotní senzory, ovládání nastavení |
| **Fotovoltaika** | Správa baterie, exportní limity | Výkonové senzory, ovládání baterie |
| **Teplá voda** | Sanitace, cirkulace | Teplota vody, ovládání ohřevu |
| **Pomocný zdroj** | Záložní topný systém | Stavové senzory, ovládání provozu |
| **Spotové ceny** | Optimalizace dynamických cen | Cenové senzory, optimalizační přepínače |
| **Stav systému** | Celkové informace o systému | Stavové senzory, diagnostická data |
