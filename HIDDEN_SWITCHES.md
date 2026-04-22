# Hidden Switches in XCC Controller

## Summary

The XCC controller contains **217 hidden switches** - boolean fields that are writable (`_BOOL_i` suffix in their `NAME` attribute) but have no corresponding UI control (`<switch>` or `<choice>` element) in the descriptor XML files.

These are typically:
- Service technician settings
- Installation-time configuration
- Hardware capability flags (e.g., cooling mode support)
- Feature flags not exposed to end users

## Discovery

Run `python find_hidden_switches.py` to scan all data pages and generate a report of hidden switches.

```bash
python find_hidden_switches.py
# Output: hidden_switches_report.txt
```

## Statistics

- **Total boolean fields in data**: 278
- **With UI controls**: 98 (35%)
- **Hidden (no UI)**: 217 (78%)

Most hidden switches appear in every page as global flags:
- `SZAPNUTO` - System power on/off
- `SCOMPACT` - Compact mode flag
- `FVE-CONFIG-ENABLED` - Photovoltaics enabled
- `CELKOVEPRAZDNINY` - Global vacation mode

## Exposed Hidden Switches

The integration exposes selected hidden switches that are safe and useful for advanced users. See `custom_components/xcc/const.py` → `HIDDEN_SWITCHES` dictionary.

### Currently Exposed

#### TO-CONFIG-CHLAZENI
**Location**: `OKRUH10.XML` (Heating Circuit 0)  
**Internal Name**: `__R44907.7_BOOL_i`  
**Description**: Enables cooling mode for the heating circuit  
**Entity**: `switch.heating_circuit_cooling_mode_configuration`

This switch allows heat pumps with reversible operation capability to switch between heating and cooling modes. When enabled, the heating circuit can operate in cooling mode during summer.

**Requirements**:
- Heat pump must support reversible operation (cooling)
- Proper hydraulic configuration for cooling
- Cooling-compatible floor/wall heating (lower water temperatures)

**Status Indicators**:
- `binary_sensor.schlazeni` (from STATUS.XML) shows if cooling is currently active
- `TO-CONFIG-CHLAZENI` (this switch) shows if the circuit is configured to support cooling

## Notable Hidden Switches (Not Yet Exposed)

### Heating Circuit Configuration
- `TO-CONFIG-UTLUM` - Attenuation mode available
- `TO-CONFIG-SENZOR` - Room sensor mode available
- `TO-CONFIG-MICHACKA-POVOLENI` - Mixing valve enabled
- `TO-CONFIG-EXTERNIUTLUM` - External attenuation control enabled
- `TO-CONFIG-NATOPPOVOLEN` - Slow heating-up mode enabled

### Hot Water (TUV) Configuration
- `TUVCONFIG-CIRKULACE` - Circulation pump enabled
- `TUVCONFIG-SANITACE` - Anti-legionella sanitization enabled
- `TUVCONFIG-VOLBAOHREVU` - Heating mode selection
- `TUVCONFIG-BOOST` - Boost mode available
- `TUVCONFIG-ALTERNATIVNIREZIM` - Alternative heating mode available
- `TUVEXTERNIOHREV` - External heater enabled
- `TUVDRUHECIDLO` - Second temperature sensor enabled
- `TUVINTELIGENTNICIDLO` - Smart sensor enabled

### Bivalent Source
- `BIVALENCE` - Bivalent heating source active
- `ALTERNATIVNIREZIMAKTIVNI` - Alternative mode active
- `VARIANTAHDOPROBIV` - HDO (ripple control) for bivalent source

### Photovoltaics (FVE)
- `FVE-CONFIG-ENABLED` - PV system enabled
- `FVE-SSR-ENABLED` - SSR (solid state relay) control enabled
- `FVE-CONFIG-SCHOVATPRETAPENI` - Hide overheating options
- Various battery and feed limit controls

### Pool/Basin
- `FILTRACE` - Filtration pump control
- `VARIANTAUTLUMBAZENU` - Pool attenuation mode available
- `BAZENINTELIGENTNICIDLO` - Smart pool sensor

## Adding New Hidden Switches

1. Find the switch in `hidden_switches_report.txt`
2. Verify it's safe to expose (won't damage equipment if toggled incorrectly)
3. Add entry to `HIDDEN_SWITCHES` in `custom_components/xcc/const.py`:

```python
"PROP-NAME": {
    "friendly_name": "Czech label",
    "friendly_name_en": "English label",
    "unit": "",
    "entity_type": "switch",
    "writable": True,
    "device_class": None,  # or "switch" for generic
    "note": "Description of what this switch does",
},
```

4. Restart Home Assistant to load the new switch

## Safety Notes

⚠️ **WARNING**: Hidden switches are hidden for a reason. Changing them without understanding their purpose can:
- Damage equipment
- Void warranty
- Create unsafe operating conditions
- Require service technician to reset

Only expose switches you understand and have verified are safe to toggle.

## Further Information

For the complete list of all 217 hidden switches, see `hidden_switches_report.txt`.
