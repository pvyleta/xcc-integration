# XCC Tepelné Čerpadlo - Home Assistant Integrace

Home Assistant integrace pro řadiče tepelných čerpadel XCC s podporou fotovoltaické integrace. Monitorujte a ovládejte váš systém tepelného čerpadla přímo z Home Assistant s automatickým objevováním entit a dvojjazyčnou podporou.

## 🏠 Funkce Home Assistant Integrace

- 🔧 **470+ nastavitelných polí** automaticky objevených napříč 6 konfiguračními stránkami
- 📊 **Živé monitorování dat** s hodnotami senzorů v reálném čase
- 🌐 **Dvojjazyčná podpora** (angličtina/čeština s automatickou detekcí)
- 🎛️ **Nativní HA entity**: Senzory, přepínače, čísla, výběry, binární senzory
- 📋 **Organizováno podle zařízení** (vytápění, FV, teplá voda, pomocný zdroj, atd.)
- 🔄 **Automatické aktualizace** s konfigurovatelným intervalem skenování
- 📈 **Profesionální UI** s nativním konfiguračním tokem Home Assistant
- 🏷️ **Konzistentní pojmenování** s prefixem `xcc_` pro snadnou identifikaci

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
   - Zadejte údaje vašeho XCC řadiče:
     - IP adresa: IP adresa vašeho XCC řadiče
     - Uživatelské jméno: Vaše XCC uživatelské jméno
     - Heslo: Vaše XCC heslo
     - Interval skenování: 30 sekund (doporučeno)

### 📁 Manuální instalace

1. Stáhněte nejnovější verzi
2. Zkopírujte `custom_components/xcc/` do vašeho Home Assistant `custom_components/` adresáře
3. Restartujte Home Assistant
4. Postupujte podle konfiguračních kroků výše

## ✅ Co získáte

- 🌡️ **Teplotní senzory**: Venkovní, vnitřní, teploty vody
- 🔄 **Stavové senzory**: Kompresor, čerpadlo, provozní režimy
- 🎛️ **Ovládání**: Přepínače, nastavení teploty, provozní režimy
- 📊 **Výkonnostní metriky**: Spotřeba energie, data účinnosti
- 🌐 **Vícejazyčnost**: Angličtina/čeština s automatickou detekcí
- 🏷️ **Organizované entity**: Všechny entity s prefixem `xcc_` pro snadnou identifikaci

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

# Spuštění konkrétních kategorií testů
python -m pytest tests/test_basic_validation.py -v
python -m pytest tests/test_xcc_client.py -v
```

**Pokrytí testů:**
- ✅ Validace Python syntaxe
- ✅ Validace manifest.json
- ✅ Parsování ukázkových dat
- ✅ Validace XML struktury
- ✅ Ověření konstant integrace

## 🔧 Řešení problémů

### Integrace se nezobrazuje v HACS
- Ujistěte se, že jste správně přidali repozitář do HACS vlastních repozitářů
- Obnovte HACS a vyhledejte znovu
- Zkontrolujte HACS logy pro případné chyby

### Problémy s připojením
- Ověřte, že IP adresa XCC řadiče je dostupná z Home Assistant
- Zkontrolujte správnost uživatelského jména/hesla
- Ujistěte se, že webové rozhraní XCC řadiče je přístupné
- Otestujte připojení z hostitele Home Assistant: `ping <XCC_IP>`

### Problémy s entitami
- Všechny XCC entity mají prefix `xcc_` pro snadnou identifikaci
- Pokud se entity nezobrazují, zkontrolujte logy Home Assistant pro chyby
- Restartujte Home Assistant po změnách konfigurace
- Zkontrolujte registr entit v Developer Tools

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

## 🆘 Podpora

### Získání pomoci
Pokud narazíte na problémy:

1. **Zkontrolujte logy Home Assistant**: Nastavení > Systém > Logy
2. **Hledejte XCC chyby**: Vyhledejte "xcc" nebo "custom_components" v lozích
3. **Ověřte konektivitu**: Ujistěte se, že XCC řadič je dostupný z HA
4. **Zkontrolujte registr entit**: Developer Tools > States (hledejte `xcc_`)

### Časté problémy

**Entity se neaktualizují:**
- Zkontrolujte konfiguraci intervalu skenování
- Ověřte, že XCC řadič odpovídá
- Hledejte chyby timeout v lozích

**Chyby autentizace:**
- Ověřte správnost uživatelského jména/hesla
- Zkontrolujte, zda je webové rozhraní XCC přístupné
- Ujistěte se, že v přihlašovacích údajích nejsou speciální znaky

**Chybějící entity:**
- Některé entity mohou být skryté, pokud nemají aktuální hodnotu
- Zkontrolujte, zda XCC řadič má všechny očekávané moduly/funkce
- Restartujte Home Assistant po změnách konfigurace

### Hlášení problémů

Při hlášení problémů prosím uveďte:
- Verzi Home Assistant
- Verzi XCC integrace
- Model/firmware XCC řadiče
- Relevantní záznamy z logů
- Kroky k reprodukci problému

[Otevřete issue na GitHubu](https://github.com/pvyleta/xcc-integration/issues)

## 📋 Changelog

Viz [CHANGELOG.md](CHANGELOG.md) pro detailní historii verzí a změn.

## 🤝 Přispívání

1. Forkněte repozitář
2. Vytvořte feature branch
3. Proveďte změny
4. Spusťte testy: `python -m pytest tests/ -v`
5. Odešlete pull request

## 📄 Licence

Tento projekt je licencován pod MIT licencí - viz soubor LICENSE pro detaily.

---

**Vytvořeno s ❤️ pro komunitu Home Assistant**
