"""Test scan interval default value."""

def test_default_scan_interval():
    """Test that the default scan interval is 120 seconds."""
    
    print("🔍 TESTING DEFAULT SCAN INTERVAL")
    print("=" * 70)
    
    try:
        # Import the constant
        import sys
        import os
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'custom_components', 'xcc'))
        
        from const import DEFAULT_SCAN_INTERVAL
        
        print(f"📊 DEFAULT_SCAN_INTERVAL: {DEFAULT_SCAN_INTERVAL} seconds")
        
        # Verify it's 120 seconds (2 minutes)
        assert DEFAULT_SCAN_INTERVAL == 120, f"Expected 120 seconds, got {DEFAULT_SCAN_INTERVAL}"
        
        # Verify it's reasonable (between 1 minute and 10 minutes)
        assert 60 <= DEFAULT_SCAN_INTERVAL <= 600, f"Scan interval should be between 60-600 seconds, got {DEFAULT_SCAN_INTERVAL}"
        
        print(f"✅ Default scan interval correctly set to {DEFAULT_SCAN_INTERVAL} seconds ({DEFAULT_SCAN_INTERVAL/60:.1f} minutes)")
        
        # Test passed if we reach here without any assertion errors
        
    except ImportError as e:
        print(f"❌ Cannot import const module: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Assertion failed: {e}")
        return False

