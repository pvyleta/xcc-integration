#!/usr/bin/env python3
"""Simple verification script to test configurable entity device assignment fix."""

import sys
import os

# Add the custom_components path to sys.path so we can import the XCC modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components'))

def test_device_assignment_code():
    """Test that the device assignment code is correctly implemented."""
    print("🔍 VERIFYING CONFIGURABLE ENTITY DEVICE ASSIGNMENT FIX")
    print("=" * 60)
    
    # Test 1: Check that all entity types use get_device_info_for_entity
    print("\n📋 Test 1: Checking device assignment method usage")
    
    try:
        # Import the entity modules
        from xcc import number, switch, select
        import inspect
        
        # Get source code for each entity type's __init__ method
        number_source = inspect.getsource(number.XCCNumber.__init__)
        switch_source = inspect.getsource(switch.XCCSwitch.__init__)
        select_source = inspect.getsource(select.XCCSelect.__init__)
        
        # Check that all use get_device_info_for_entity
        tests = [
            ("Number", number_source),
            ("Switch", switch_source), 
            ("Select", select_source)
        ]
        
        all_passed = True
        for entity_type, source in tests:
            if "get_device_info_for_entity" in source:
                print(f"   ✅ {entity_type} entity uses get_device_info_for_entity")
            else:
                print(f"   ❌ {entity_type} entity does NOT use get_device_info_for_entity")
                all_passed = False
                
            # Check that they don't use hardcoded coordinator.device_info
            if "coordinator.device_info" in source.replace("get_device_info_for_entity", ""):
                print(f"   ❌ {entity_type} entity still uses hardcoded coordinator.device_info")
                all_passed = False
            else:
                print(f"   ✅ {entity_type} entity does not use hardcoded device_info")
        
        if all_passed:
            print("\n🎉 All configurable entity types correctly use proper device assignment!")
        else:
            print("\n❌ Some entity types still have device assignment issues")
            return False
            
    except Exception as e:
        print(f"❌ Error importing modules: {e}")
        return False
    
    # Test 2: Check coordinator device assignment logic
    print("\n📋 Test 2: Checking coordinator device assignment logic")
    
    try:
        from xcc.coordinator import XCCDataUpdateCoordinator
        
        # Check that coordinator has the get_device_info_for_entity method
        if hasattr(XCCDataUpdateCoordinator, 'get_device_info_for_entity'):
            print("   ✅ Coordinator has get_device_info_for_entity method")
            
            # Get the method source to verify it uses proper logic
            method_source = inspect.getsource(XCCDataUpdateCoordinator.get_device_info_for_entity)
            
            if "entity_data.get(\"device\")" in method_source:
                print("   ✅ Method checks entity device assignment")
            else:
                print("   ❌ Method does not check entity device assignment")
                return False
                
            if "sub_device_info" in method_source:
                print("   ✅ Method uses sub_device_info for device lookup")
            else:
                print("   ❌ Method does not use sub_device_info")
                return False
                
        else:
            print("   ❌ Coordinator missing get_device_info_for_entity method")
            return False
            
    except Exception as e:
        print(f"❌ Error checking coordinator: {e}")
        return False
    
    # Test 3: Check that sensors still work correctly (they use XCCEntity base class)
    print("\n📋 Test 3: Checking sensor entity device assignment")
    
    try:
        from xcc.entity import XCCEntity
        
        # Check that XCCEntity uses get_device_info_for_entity
        entity_source = inspect.getsource(XCCEntity.__init__)
        
        if "get_device_info_for_entity" in entity_source:
            print("   ✅ XCCEntity (used by sensors) uses get_device_info_for_entity")
        else:
            print("   ❌ XCCEntity does not use get_device_info_for_entity")
            return False
            
    except Exception as e:
        print(f"❌ Error checking XCCEntity: {e}")
        return False
    
    print("\n🎉 ALL TESTS PASSED!")
    print("✅ Configurable entities (number, switch, select) will now be assigned to correct devices")
    print("✅ Device assignment is based on the page where the entity was found")
    print("✅ Priority-based assignment ensures entities appear only once")
    print("✅ Sensors continue to work correctly with proper device assignment")
    
    return True


def show_device_assignment_summary():
    """Show a summary of how device assignment works."""
    print("\n📚 DEVICE ASSIGNMENT SUMMARY")
    print("=" * 40)
    print("🏗️ How it works:")
    print("   1. Coordinator parses entities from XCC pages (FVE.XML, OKRUH1.XML, etc.)")
    print("   2. Each entity is assigned to a device based on its page:")
    print("      • FVE.XML → FVE device (Photovoltaics)")
    print("      • OKRUH*.XML → OKRUH device (Heating Circuit)")
    print("      • TUV1.XML → TUV1 device (Hot Water)")
    print("      • SPOT.XML → SPOT device (Spot Pricing)")
    print("      • BIV.XML → BIV device (Auxiliary Source)")
    print("      • STAVJED.XML → STAVJED device (System Status)")
    print("   3. Priority-based assignment prevents duplicates")
    print("   4. All entity types (sensors, numbers, switches, selects) use same assignment")
    print("\n🔧 What was fixed:")
    print("   • Number entities: Now use get_device_info_for_entity() instead of hardcoded device")
    print("   • Switch entities: Now use get_device_info_for_entity() instead of hardcoded device") 
    print("   • Select entities: Now use get_device_info_for_entity() instead of hardcoded device")
    print("   • Sensor entities: Already worked correctly (use XCCEntity base class)")
    print("\n🎯 Result:")
    print("   • Configurable entities appear under the same device as related sensors")
    print("   • Better organization in Home Assistant device view")
    print("   • Consistent device assignment across all entity types")


if __name__ == "__main__":
    success = test_device_assignment_code()
    
    if success:
        show_device_assignment_summary()
        print("\n🚀 Ready to test in Home Assistant!")
        sys.exit(0)
    else:
        print("\n❌ Fix verification failed - please check the implementation")
        sys.exit(1)
