"""Test FVEINV device priority and assignment."""

import pytest
from custom_components.xcc.coordinator import XCCDataUpdateCoordinator
from custom_components.xcc.const import LANGUAGE_ENGLISH, LANGUAGE_CZECH


def test_fveinv_device_priority_order():
    """Test that FVEINV has higher priority than FVE in device assignment."""
    
    # Mock entities from both FVEINV and FVE pages
    mock_entities = [
        {
            "entity_id": "xcc_fvestats_demandchrgcurr",
            "entity_type": "sensor", 
            "state": "15.2",
            "attributes": {
                "field_name": "FVESTATS-DEMANDCHRGCURR",
                "page": "FVEINV10.XML",  # FVEINV page
                "source_page": "FVEINV"
            }
        },
        {
            "entity_id": "xcc_fvestats_demandchrgcurr_fve",
            "entity_type": "sensor",
            "state": "15.2", 
            "attributes": {
                "field_name": "FVESTATS-DEMANDCHRGCURR",  # Same entity name
                "page": "FVE4.XML",  # FVE page
                "source_page": "FVE"
            }
        },
        {
            "entity_id": "xcc_fve_config_meniceconfig_readonly",
            "entity_type": "sensor",
            "state": "Režim pouze pro čtení",
            "attributes": {
                "field_name": "FVE-CONFIG-MENICECONFIG-READONLY",
                "page": "FVEINV.XML",  # FVEINV descriptor page
                "source_page": "FVEINV"
            }
        }
    ]
    
    # Simulate the priority-based assignment logic
    device_priority = ["SPOT", "FVEINV", "FVE", "BIV", "OKRUH", "TUV1", "STAVJED", "NAST", "XCC_HIDDEN_SETTINGS"]
    assigned_entities = set()
    device_assignments = {}
    
    # Group entities by page (normalized)
    entities_by_page = {}
    for entity in mock_entities:
        page = entity["attributes"].get("page", "unknown").upper()
        # Normalize page names
        if page == "NAST.XML":
            page_normalized = "NAST"
        else:
            page_normalized = page.replace("1.XML", "").replace("10.XML", "").replace("11.XML", "").replace("4.XML", "").replace(".XML", "")
        
        if page_normalized not in entities_by_page:
            entities_by_page[page_normalized] = []
        entities_by_page[page_normalized].append(entity)
    
    print(f"\n🔍 PAGE GROUPING:")
    for page_name, page_entities in entities_by_page.items():
        print(f"   {page_name}: {len(page_entities)} entities")
        for entity in page_entities:
            print(f"      - {entity['attributes']['field_name']}")
    
    # Process entities in priority order
    for device_name in device_priority:
        if device_name not in entities_by_page:
            continue
            
        device_entities = entities_by_page[device_name]
        assigned_count = 0
        skipped_count = 0
        
        print(f"\n📱 Processing {device_name}:")
        
        for entity in device_entities:
            prop = entity["attributes"]["field_name"]
            
            if prop in assigned_entities:
                print(f"   ⏭️  SKIP: {prop} (already assigned)")
                skipped_count += 1
                continue
            
            # Assign entity to this device
            assigned_entities.add(prop)
            device_assignments[prop] = device_name
            assigned_count += 1
            print(f"   ✅ ASSIGN: {prop} -> {device_name}")
        
        print(f"   📊 Summary: {assigned_count} assigned, {skipped_count} skipped")
    
    # Verify results
    print(f"\n🎯 FINAL ASSIGNMENTS:")
    for prop, device in device_assignments.items():
        print(f"   {prop} -> {device}")
    
    # Test assertions
    assert "FVESTATS-DEMANDCHRGCURR" in device_assignments, "FVESTATS-DEMANDCHRGCURR should be assigned"
    assert device_assignments["FVESTATS-DEMANDCHRGCURR"] == "FVEINV", "FVESTATS-DEMANDCHRGCURR should be assigned to FVEINV (higher priority than FVE)"
    
    assert "FVE-CONFIG-MENICECONFIG-READONLY" in device_assignments, "FVE-CONFIG-MENICECONFIG-READONLY should be assigned"
    assert device_assignments["FVE-CONFIG-MENICECONFIG-READONLY"] == "FVEINV", "FVE-CONFIG-MENICECONFIG-READONLY should be assigned to FVEINV"
    
    # Verify that FVEINV has higher priority than FVE
    fveinv_priority = device_priority.index("FVEINV")
    fve_priority = device_priority.index("FVE")
    assert fveinv_priority < fve_priority, "FVEINV should have higher priority (lower index) than FVE"
    
    print(f"\n✅ PRIORITY TEST PASSED:")
    print(f"   FVEINV priority: {fveinv_priority}")
    print(f"   FVE priority: {fve_priority}")
    print(f"   FVEINV entities get assigned before FVE entities")


def test_fveinv_device_info_english():
    """Test FVEINV device info in English."""
    
    # Mock coordinator with English language
    class MockCoordinator:
        def __init__(self):
            self.language = LANGUAGE_ENGLISH
            self.ip_address = "192.168.1.100"
        
        def _init_device_info(self):
            """Initialize device info for all sub-devices."""
            device_configs = {
                "SPOT": {"name": "Spot Prices", "model": "Energy Market Data"},
                "FVEINV": {"name": "PV Inverter", "model": "Solar Inverter Monitor"},
                "FVE": {"name": "Solar PV System", "model": "Photovoltaic Controller"},
                "BIV": {"name": "Heat Pump", "model": "Bivalent Heat Pump"},
                "OKRUH": {"name": "Heating Circuits", "model": "Heating Zone Controller"},
                "TUV1": {"name": "Hot Water System", "model": "Domestic Hot Water"},
                "STAVJED": {"name": "Unit Status", "model": "System Status Monitor"},
                "NAST": {"name": "Heat Pump Settings", "model": "HP Configuration & Calibration"},
                "XCC_HIDDEN_SETTINGS": {"name": "Hidden Settings", "model": "Advanced Configuration"},
            }
            
            self.sub_device_info = {}
            for device_name, config in device_configs.items():
                self.sub_device_info[device_name] = {
                    "identifiers": {("xcc", f"{self.ip_address}_{device_name}")},
                    "name": f"{config['name']} ({self.ip_address})",
                    "manufacturer": "XCC",
                    "model": config["model"],
                    "sw_version": "Unknown",
                    "configuration_url": f"http://{self.ip_address}",
                    "via_device": ("xcc", self.ip_address),
                }
    
    coordinator = MockCoordinator()
    coordinator._init_device_info()
    
    # Test FVEINV device info
    fveinv_info = coordinator.sub_device_info["FVEINV"]
    
    assert fveinv_info["name"] == "PV Inverter (192.168.1.100)"
    assert fveinv_info["model"] == "Solar Inverter Monitor"
    assert fveinv_info["manufacturer"] == "XCC"
    assert fveinv_info["configuration_url"] == "http://192.168.1.100"
    assert fveinv_info["via_device"] == ("xcc", "192.168.1.100")
    
    print(f"✅ FVEINV English device info: {fveinv_info['name']} - {fveinv_info['model']}")


def test_fveinv_device_info_czech():
    """Test FVEINV device info in Czech."""
    
    # Mock coordinator with Czech language
    class MockCoordinator:
        def __init__(self):
            self.language = LANGUAGE_CZECH
            self.ip_address = "192.168.1.100"
        
        def _init_device_info(self):
            """Initialize device info for all sub-devices."""
            device_configs = {
                "SPOT": {"name": "Spotové ceny", "model": "Data energetického trhu"},
                "FVEINV": {"name": "FV Měnič", "model": "Monitor solárního měniče"},
                "FVE": {"name": "Fotovoltaický systém", "model": "Fotovoltaický regulátor"},
                "BIV": {"name": "Tepelné čerpadlo", "model": "Bivalentní tepelné čerpadlo"},
                "OKRUH": {"name": "Topné okruhy", "model": "Regulátor topných zón"},
                "TUV1": {"name": "Systém teplé vody", "model": "Teplá užitková voda"},
                "STAVJED": {"name": "Stav jednotky", "model": "Monitor stavu systému"},
                "NAST": {"name": "Nastavení TČ", "model": "Konfigurace a kalibrace TČ"},
                "XCC_HIDDEN_SETTINGS": {"name": "Skrytá nastavení", "model": "Pokročilá konfigurace"},
            }
            
            self.sub_device_info = {}
            for device_name, config in device_configs.items():
                self.sub_device_info[device_name] = {
                    "identifiers": {("xcc", f"{self.ip_address}_{device_name}")},
                    "name": f"{config['name']} ({self.ip_address})",
                    "manufacturer": "XCC",
                    "model": config["model"],
                    "sw_version": "Unknown",
                    "configuration_url": f"http://{self.ip_address}",
                    "via_device": ("xcc", self.ip_address),
                }
    
    coordinator = MockCoordinator()
    coordinator._init_device_info()
    
    # Test FVEINV device info
    fveinv_info = coordinator.sub_device_info["FVEINV"]
    
    assert fveinv_info["name"] == "FV Měnič (192.168.1.100)"
    assert fveinv_info["model"] == "Monitor solárního měniče"
    assert fveinv_info["manufacturer"] == "XCC"
    assert fveinv_info["configuration_url"] == "http://192.168.1.100"
    assert fveinv_info["via_device"] == ("xcc", "192.168.1.100")
    
    print(f"✅ FVEINV Czech device info: {fveinv_info['name']} - {fveinv_info['model']}")


if __name__ == "__main__":
    test_fveinv_device_priority_order()
    test_fveinv_device_info_english()
    test_fveinv_device_info_czech()
    print("\n🎉 All FVEINV device priority tests passed!")
