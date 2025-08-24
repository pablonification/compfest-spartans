#!/usr/bin/env python3
"""
ESP32 Backend Testing Script

This script simulates ESP32 device interactions with the backend API
to test the fixes for device registration persistence and commands polling.
"""

import requests
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "http://localhost:8000"  # Local backend
# BASE_URL = "https://api.setorin.app"  # Production backend

DEVICE_ID = "ESP32-SMARTBIN-TEST-001"
DEVICE_CONFIG = {
    "device_id": DEVICE_ID,
    "firmware_version": "1.2.3-test",
    "hardware_version": "ESP32-WROOM-32",
    "location": "Test Lab",
    "ip_address": "127.0.0.1"
}

class ESP32Tester:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        
    def log(self, message: str, level: str = "INFO"):
        """Log messages with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
        
    def test_health(self) -> bool:
        """Test if backend is healthy"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.log("✅ Backend is healthy")
                return True
            else:
                self.log(f"❌ Backend health check failed: {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log(f"❌ Backend connection failed: {e}", "ERROR")
            return False
    
    def register_device(self) -> bool:
        """Simulate ESP32 device registration"""
        self.log("🔄 Registering ESP32 device...")
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/esp32/register",
                json=DEVICE_CONFIG,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                self.log(f"✅ Device registered successfully: {data}")
                return True
            else:
                self.log(f"❌ Registration failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Registration error: {e}", "ERROR")
            return False
    
    def send_status_update(self, status: str = "online") -> bool:
        """Simulate ESP32 status update"""
        self.log(f"🔄 Sending status update: {status}")
        
        status_data = {
            "device_id": DEVICE_ID,
            "status": status,
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "battery_level": 85,
            "temperature": 25.5,
            "error_message": None
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/esp32/status",
                json=status_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 200:
                self.log("✅ Status update sent successfully")
                return True
            else:
                self.log(f"❌ Status update failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Status update error: {e}", "ERROR")
            return False
    
    def check_for_commands(self) -> Optional[Dict[str, Any]]:
        """Simulate ESP32 checking for commands (this was failing before)"""
        self.log("🔄 Checking for commands...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/esp32/commands",
                params={"device_id": DEVICE_ID},
                timeout=10
            )
            
            if response.status_code == 204:
                self.log("✅ No pending commands (HTTP 204)")
                return None
            elif response.status_code == 200:
                command = response.json()
                self.log(f"✅ Command received: {command}")
                return command
            elif response.status_code == 404:
                self.log("❌ Device not found (HTTP 404) - This should be FIXED now!", "ERROR")
                return None
            else:
                self.log(f"❌ Command check failed: {response.status_code} - {response.text}", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Command check error: {e}", "ERROR")
            return None
    
    def create_command(self, command: str = "open_lid", duration: int = 5) -> bool:
        """Create a command for the ESP32 device"""
        self.log(f"🔄 Creating command: {command} (duration: {duration}s)")
        
        command_data = {
            "device_id": DEVICE_ID,
            "command": command,
            "duration_seconds": duration,
            "priority": "normal"
        }
        
        try:
            response = self.session.post(
                f"{self.base_url}/api/esp32/commands",
                json=command_data,
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            
            if response.status_code == 201:
                data = response.json()
                self.log(f"✅ Command created: {data}")
                return True
            else:
                self.log(f"❌ Command creation failed: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Command creation error: {e}", "ERROR")
            return False
    
    def get_device_list(self) -> bool:
        """Get list of registered devices"""
        self.log("🔄 Getting device list...")
        
        try:
            response = self.session.get(f"{self.base_url}/api/esp32/devices", timeout=10)
            
            if response.status_code == 200:
                devices = response.json()
                self.log(f"✅ Found {len(devices)} registered devices")
                for device in devices:
                    self.log(f"   - {device.get('device_id')} ({device.get('status')})")
                return True
            else:
                self.log(f"❌ Failed to get device list: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Device list error: {e}", "ERROR")
            return False
    
    def get_logs(self, limit: int = 5) -> bool:
        """Get ESP32 action logs"""
        self.log(f"🔄 Getting last {limit} logs...")
        
        try:
            response = self.session.get(
                f"{self.base_url}/api/esp32/logs",
                params={"device_id": DEVICE_ID, "limit": limit},
                timeout=10
            )
            
            if response.status_code == 200:
                logs = response.json()
                self.log(f"✅ Found {len(logs)} logs")
                for log in logs[:3]:  # Show first 3
                    self.log(f"   - {log.get('action')} ({log.get('status')}) at {log.get('timestamp')}")
                return True
            else:
                self.log(f"❌ Failed to get logs: {response.status_code} - {response.text}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"❌ Logs error: {e}", "ERROR")
            return False

def main():
    """Main testing function"""
    print("=" * 60)
    print("🧪 ESP32 Backend Integration Test")
    print("=" * 60)
    
    tester = ESP32Tester()
    
    # Test 1: Health Check
    print("\n📋 Test 1: Backend Health Check")
    if not tester.test_health():
        print("❌ Backend is not available. Exiting.")
        return
    
    # Test 2: Device Registration
    print("\n📋 Test 2: Device Registration")
    tester.register_device()
    
    # Test 3: Status Update
    print("\n📋 Test 3: Status Update")
    tester.send_status_update()
    
    # Test 4: Get Device List
    print("\n📋 Test 4: Device List")
    tester.get_device_list()
    
    # Test 5: Check Commands (This was failing before!)
    print("\n📋 Test 5: Command Check (The main fix)")
    tester.check_for_commands()
    
    # Test 6: Create a Command
    print("\n📋 Test 6: Create Command")
    tester.create_command("open_lid", 3)
    
    # Test 7: Check Commands Again (Should return the command)
    print("\n📋 Test 7: Check Commands Again")
    command = tester.check_for_commands()
    
    # Test 8: Get Logs
    print("\n📋 Test 8: Action Logs")
    tester.get_logs()
    
    # Test 9: Simulate ESP32 Polling Loop
    print("\n📋 Test 9: ESP32 Polling Simulation (5 iterations)")
    for i in range(5):
        print(f"\n--- Polling Iteration {i+1} ---")
        tester.send_status_update()
        tester.check_for_commands()
        time.sleep(2)
    
    print("\n" + "=" * 60)
    print("✅ ESP32 Backend Integration Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
