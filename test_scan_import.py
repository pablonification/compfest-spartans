#!/usr/bin/env python3
"""
Test script to check if scan router can be imported without errors
"""

import sys
import os

# Add the backend src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend', 'src'))

def test_scan_import():
    """Test if scan router can be imported"""
    
    print("🔍 Testing scan router import...")
    
    try:
        # Test importing the scan router
        from backend.routers.scan import router
        print("✅ Scan router imported successfully")
        print(f"Router prefix: {getattr(router, 'prefix', 'None')}")
        print(f"Router tags: {getattr(router, 'tags', 'None')}")
        
        # Check if the router has any routes
        routes = router.routes
        print(f"Number of routes: {len(routes)}")
        
        for route in routes:
            print(f"  - {route.methods} {route.path}")
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False
    
    return True

def test_scan_services():
    """Test if scan router dependencies can be imported"""
    
    print("\n🔍 Testing scan router dependencies...")
    
    try:
        # Test importing services
        from backend.services.opencv_service import BottleMeasurer
        print("✅ OpenCV service imported successfully")
        
        from backend.services.roboflow_service import RoboflowClient
        print("✅ Roboflow service imported successfully")
        
        from backend.services.validation_service import validate_scan
        print("✅ Validation service imported successfully")
        
        from backend.services.transaction_service import get_transaction_service
        print("✅ Transaction service imported successfully")
        
        from backend.services.iot_client import SmartBinClient
        print("✅ IoT client imported successfully")
        
        from backend.services.ws_manager import manager
        print("✅ WebSocket manager imported successfully")
        
        from backend.services.reward_service import add_points
        print("✅ Reward service imported successfully")
        
        from backend.routers.auth import verify_token
        print("✅ Auth router imported successfully")
        
    except ImportError as e:
        print(f"❌ Service import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected service error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🧪 Testing SmartBin scan router import and dependencies...\n")
    
    # Test scan router import
    scan_import_ok = test_scan_import()
    
    # Test dependencies
    services_ok = test_scan_services()
    
    print(f"\n📊 Test Results:")
    print(f"  Scan Router Import: {'✅ PASS' if scan_import_ok else '❌ FAIL'}")
    print(f"  Services Import: {'✅ PASS' if services_ok else '❌ FAIL'}")
    
    if scan_import_ok and services_ok:
        print("\n🎉 All tests passed! Scan router should work properly.")
    else:
        print("\n⚠️ Some tests failed. Check the errors above.")

