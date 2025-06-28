# XCC Tepelné Čerpadlo CLI

Komplexní nástroj příkazové řádky pro správu řadičů tepelných čerpadel XCC s podporou fotovoltaické integrace. Tento nástroj umožňuje číst, monitorovat a konfigurovat váš systém tepelného čerpadla prostřednictvím strukturovaného rozhraní organizovaného podle stránek.

## Funkce

- 🔧 **470+ Nastavitelných Polí** napříč 6 konfiguračními stránkami
- 📊 **Živé Načítání Dat** s aktuálními hodnotami v reálném čase
- 🌐 **Dvojjazyčná Podpora** (anglické/české popisy)
- 📋 **Strukturované Rozhraní** organizované podle konfiguračních stránek
- 🔍 **Pokročilé Vyhledávání** napříč všemi poli a stránkami
- 🔄 **Obnovení Databáze** pro synchronizaci s aktualizacemi firmwaru
- 📈 **Bohaté Zobrazení** s omezeními, možnostmi a aktuálními hodnotami
- 🖥️ **Profesionální CLI** postavené na Click frameworku
- 🛠️ **Shell Integrace** s pohodlným wrapper skriptem

## Instalace

1. **Klonování repozitáře:**
   ```bash
   git clone <repository-url>
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

4. **Generování databáze polí:**
   ```bash
   python analyze_known_pages.py
   ```

5. **Nastavení shell skriptu (volitelné):**
   ```bash
   # Učinit shell skript spustitelným
   chmod +x xcc

   # Přidat do PATH nebo vytvořit symbolický odkaz
   sudo ln -s $(pwd)/xcc /usr/local/bin/xcc
   ```

**Poznámka:** Databáze polí se automaticky vygeneruje při prvním spuštění, pokud chybí.

## Rychlý Start

### Seznam Dostupných Stránek
```bash
# Použití Python skriptu přímo
python xcc_cli.py pages

# Použití shell wrapperu (pokud je nainstalován)
xcc pages
```

### Zobrazení Konfiguračních Polí
```bash
# Seznam všech nastavitelných polí na stránce spotových cen
xcc spot --list

# Seznam všech polí (včetně pouze pro čtení) na FVE stránce
xcc fve --list-all

# Zobrazení detailních informací o konkrétním poli
xcc fve --show FVE-USEMODE

# Získání aktuální hodnoty pole
xcc tuv1 --get TUVPOZADOVANA
```

### Vyhledávání a Filtrování
```bash
# Vyhledání polí souvisejících s baterií na FVE stránce
xcc fve --search battery

# Vyhledávání napříč všemi stránkami
xcc search temperature
```

## Konfigurační Stránky

| Příkaz | Stránka | Popis | Pole |
|--------|---------|-------|------|
| `okruh` | Topné Okruhy | Řízení teploty, časové programy, vliv počasí | 114 |
| `fve` | Fotovoltaika | Správa baterie, limity exportu, spotové ceny | 220 |
| `tuv1` | Teplá Voda | Sanitace, cirkulace, externí ohřev | 82 |
| `biv` | Bivalentní Topení | Konfigurace záložního topného systému | 47 |
| `spot` | Spotové Ceny | Optimalizace dynamických cen | 7 |

## Rozhraní Příkazové Řádky

### Shell Skript vs Python Skript

**Shell Skript (Doporučeno):**
```bash
xcc --lang cz spot --list
```

**Python Skript (Přímo):**
```bash
python xcc_cli.py --lang cz spot --list
```

### Globální Možnosti

**Důležité**: Globální možnosti musí být **před** podpříkazem.

- `--ip IP` - IP adresa řadiče (výchozí: 192.168.0.50)
- `--username USER` - Uživatelské jméno (výchozí: xcc)
- `--password PASS` - Heslo (výchozí: xcc)
- `--lang {en,cz}` - Jazyk pro popisy (výchozí: en)
- `-v, --verbose` - Povolit podrobný ladicí výstup
- `--show-entities` - Zobrazit výstup entit během načítání dat

### Příkazy Stránek
Každá stránka podporuje tyto podpříkazy:
- `--list` - Seznam všech nastavitelných polí s aktuálními hodnotami
- `--list-all` - Seznam všech polí (nastavitelná + pouze pro čtení)
- `--show POLE` - Zobrazení detailních informací o poli
- `--get POLE` - Získání aktuální hodnoty pole
- `--search DOTAZ` - Vyhledávání polí na této stránce

### Speciální Příkazy
- `pages` - Seznam všech dostupných konfiguračních stránek
- `search DOTAZ` - Vyhledávání napříč všemi stránkami
- `refresh-db` - Aktualizace databáze polí z řadiče
- `refresh-db --force` - Vynucení obnovení i když je databáze čerstvá

## Příklady

### Základní Použití
```bash
# Zobrazení všech nastavení spotových cen
xcc spot --list

# Kontrola aktuálního režimu baterie
xcc fve --get FVE-USEMODE

# Vyhledání nastavení souvisejících s teplotou
xcc okruh --search temperature
```

### Pokročilé Použití
```bash
# Použití českých popisů (globální možnosti první)
xcc --lang cz spot --list

# Vlastní přihlašovací údaje s podrobným výstupem
xcc --username admin --password secret123 -v pages

# Zobrazení výstupu entit během načítání dat
xcc --show-entities fve --list
```

### Správa Databáze
```bash
# Kontrola, zda databáze potřebuje obnovení
xcc refresh-db

# Vynucení obnovení databáze po aktualizaci firmwaru
xcc refresh-db --force
```



## Typy Polí a Zobrazení

### Sloupce Tabulky
- **Field** - Název/identifikátor pole
- **Type** - Datový typ (numeric, boolean, enum, time, action)
- **Current Value** - Živá hodnota z řadiče
- **Description** - Lidsky čitelný popis
- **Constraints** - Min/max hodnoty, jednotky, dostupné možnosti
- **Access** - 🔧 (nastavitelné) nebo 👁️ (pouze pro čtení)

### Formátování Hodnot
- **Boolean**: ✓ (povoleno) / ✗ (zakázáno)
- **Enum**: Aktuální hodnota s popisem (např. "3 (Ekonomický)")
- **Numeric**: Hodnota s jednotkou (např. "21.0 °C")
- **Time**: Formátované časové hodnoty

## Správa Databáze

CLI používá hybridní přístup:
- **Statická data** (definice polí, omezení) z JSON databáze
- **Dynamická data** (aktuální hodnoty) načítaná živě z řadiče

### Kdy Obnovit Databázi
- Po aktualizacích firmwaru řadiče
- Když jsou přidána nová pole
- Pokud se změní definice polí
- Pro řešení problémů se synchronizací

### Proces Obnovení
```bash
# Příkaz refresh automaticky spustí analyze_known_pages.py
xcc refresh-db
```

## Řešení Problémů

### Problémy s Připojením
```bash
# Test s podrobným výstupem
xcc -v pages

# Kontrola s vlastní IP
xcc --ip 192.168.1.100 pages
```

### Problémy s Databází
```bash
# Vynucení obnovení databáze
xcc refresh-db --force

# Ruční generování databáze
python analyze_known_pages.py
```

### Problémy s Autentizací
```bash
# Použití vlastních přihlašovacích údajů
xcc --username mojeuživatel --password mojeheslo pages
```



## Architektura

### Tok Dat
1. **Statická Databáze**: Definice polí načtené z `field_database.json`
2. **Živé Připojení**: Aktuální hodnoty načtené z XML endpointů řadiče
3. **Hybridní Zobrazení**: Kombinace statických metadat s živými hodnotami

### Struktura Souborů
- `xcc_cli.py` - Hlavní CLI aplikace (založená na Click)
- `xcc` - Shell wrapper skript s aktivací virtuálního prostředí
- `xcc_client.py` - Znovupoužitelná XCC klientská knihovna
- `scripts/analyze_known_pages.py` - Generátor databáze
- `field_database.json` - Databáze polí (automaticky generovaná)
- `requirements.txt` - Python závislosti (včetně Click)

## Přispívání

1. Forkněte repozitář
2. Vytvořte feature branch
3. Proveďte změny
4. Otestujte s vaším řadičem
5. Odešlete pull request

## Licence

[Přidejte informace o licenci zde]

## Podpora

Pro problémy a otázky:
1. Zkontrolujte sekci řešení problémů
2. Spusťte s `-v` flagou pro detailní logy
3. Ověřte konektivitu řadiče
4. Zkontrolujte čerstvost databáze pomocí `refresh-db`
