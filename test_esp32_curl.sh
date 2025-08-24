#!/bin/bash

# ESP32 Backend Testing Script (curl version)
# This script uses curl commands to test ESP32-backend interaction

BASE_URL="http://localhost:8000"
DEVICE_ID="ESP32-SMARTBIN-CURL-001"

echo "=============================================="
echo "🧪 ESP32 Backend Integration Test (curl)"
echo "=============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

# Test 1: Health Check
echo -e "\n📋 Test 1: Backend Health Check"
log_info "Testing backend health..."
HEALTH_RESPONSE=$(curl -s -w "%{http_code}" "$BASE_URL/health")
HTTP_CODE="${HEALTH_RESPONSE: -3}"
RESPONSE_BODY="${HEALTH_RESPONSE%???}"

if [ "$HTTP_CODE" = "200" ]; then
    log_success "Backend is healthy: $RESPONSE_BODY"
else
    log_error "Backend health check failed: HTTP $HTTP_CODE"
    exit 1
fi

# Test 2: Device Registration
echo -e "\n📋 Test 2: Device Registration"
log_info "Registering ESP32 device..."

REGISTER_DATA='{
    "device_id": "'$DEVICE_ID'",
    "firmware_version": "1.2.3-curl",
    "hardware_version": "ESP32-WROOM-32",
    "location": "Curl Test Lab",
    "ip_address": "127.0.0.1"
}'

REGISTER_RESPONSE=$(curl -s -w "%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d "$REGISTER_DATA" \
    "$BASE_URL/api/esp32/register")

HTTP_CODE="${REGISTER_RESPONSE: -3}"
RESPONSE_BODY="${REGISTER_RESPONSE%???}"

if [ "$HTTP_CODE" = "201" ]; then
    log_success "Device registered: $RESPONSE_BODY"
else
    log_error "Registration failed: HTTP $HTTP_CODE - $RESPONSE_BODY"
fi

# Test 3: Status Update
echo -e "\n📋 Test 3: Status Update"
log_info "Sending status update..."

STATUS_DATA='{
    "device_id": "'$DEVICE_ID'",
    "status": "online",
    "last_seen": "'$(date -u +%Y-%m-%dT%H:%M:%S.%3NZ)'",
    "battery_level": 90,
    "temperature": 24.5,
    "error_message": null
}'

STATUS_RESPONSE=$(curl -s -w "%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d "$STATUS_DATA" \
    "$BASE_URL/api/esp32/status")

HTTP_CODE="${STATUS_RESPONSE: -3}"
RESPONSE_BODY="${STATUS_RESPONSE%???}"

if [ "$HTTP_CODE" = "200" ]; then
    log_success "Status update sent: $RESPONSE_BODY"
else
    log_error "Status update failed: HTTP $HTTP_CODE - $RESPONSE_BODY"
fi

# Test 4: Get Device List
echo -e "\n📋 Test 4: Get Device List"
log_info "Getting registered devices..."

DEVICES_RESPONSE=$(curl -s -w "%{http_code}" "$BASE_URL/api/esp32/devices")
HTTP_CODE="${DEVICES_RESPONSE: -3}"
RESPONSE_BODY="${DEVICES_RESPONSE%???}"

if [ "$HTTP_CODE" = "200" ]; then
    log_success "Devices retrieved:"
    echo "$RESPONSE_BODY" | jq '.' 2>/dev/null || echo "$RESPONSE_BODY"
else
    log_error "Failed to get devices: HTTP $HTTP_CODE - $RESPONSE_BODY"
fi

# Test 5: Check Commands (The main fix!)
echo -e "\n📋 Test 5: Check Commands (The Main Fix)"
log_info "Checking for commands (this was failing before)..."

COMMANDS_RESPONSE=$(curl -s -w "%{http_code}" "$BASE_URL/api/esp32/commands?device_id=$DEVICE_ID")
HTTP_CODE="${COMMANDS_RESPONSE: -3}"
RESPONSE_BODY="${COMMANDS_RESPONSE%???}"

if [ "$HTTP_CODE" = "204" ]; then
    log_success "✅ No pending commands (HTTP 204) - This means the fix worked!"
elif [ "$HTTP_CODE" = "200" ]; then
    log_success "✅ Command received: $RESPONSE_BODY"
elif [ "$HTTP_CODE" = "404" ]; then
    log_error "❌ Device not found (HTTP 404) - The fix didn't work!"
else
    log_error "Command check failed: HTTP $HTTP_CODE - $RESPONSE_BODY"
fi

# Test 6: Create Command
echo -e "\n📋 Test 6: Create Command"
log_info "Creating a command for the device..."

COMMAND_DATA='{
    "device_id": "'$DEVICE_ID'",
    "command": "open_lid",
    "duration_seconds": 5,
    "priority": "normal"
}'

CREATE_CMD_RESPONSE=$(curl -s -w "%{http_code}" \
    -X POST \
    -H "Content-Type: application/json" \
    -d "$COMMAND_DATA" \
    "$BASE_URL/api/esp32/commands")

HTTP_CODE="${CREATE_CMD_RESPONSE: -3}"
RESPONSE_BODY="${CREATE_CMD_RESPONSE%???}"

if [ "$HTTP_CODE" = "201" ]; then
    log_success "Command created: $RESPONSE_BODY"
else
    log_error "Command creation failed: HTTP $HTTP_CODE - $RESPONSE_BODY"
fi

# Test 7: Check Commands Again
echo -e "\n📋 Test 7: Check Commands Again"
log_info "Checking for commands (should return the command we just created)..."

COMMANDS_RESPONSE2=$(curl -s -w "%{http_code}" "$BASE_URL/api/esp32/commands?device_id=$DEVICE_ID")
HTTP_CODE="${COMMANDS_RESPONSE2: -3}"
RESPONSE_BODY="${COMMANDS_RESPONSE2%???}"

if [ "$HTTP_CODE" = "200" ]; then
    log_success "✅ Command received: $RESPONSE_BODY"
elif [ "$HTTP_CODE" = "204" ]; then
    log_warning "No pending commands (maybe command was already processed)"
elif [ "$HTTP_CODE" = "404" ]; then
    log_error "❌ Device not found (HTTP 404) - The fix didn't work!"
else
    log_error "Command check failed: HTTP $HTTP_CODE - $RESPONSE_BODY"
fi

# Test 8: Get Logs
echo -e "\n📋 Test 8: Get Action Logs"
log_info "Getting device logs..."

LOGS_RESPONSE=$(curl -s -w "%{http_code}" "$BASE_URL/api/esp32/logs?device_id=$DEVICE_ID&limit=5")
HTTP_CODE="${LOGS_RESPONSE: -3}"
RESPONSE_BODY="${LOGS_RESPONSE%???}"

if [ "$HTTP_CODE" = "200" ]; then
    log_success "Logs retrieved:"
    echo "$RESPONSE_BODY" | jq '.[0:3]' 2>/dev/null || echo "$RESPONSE_BODY"
else
    log_error "Failed to get logs: HTTP $HTTP_CODE - $RESPONSE_BODY"
fi

# Test 9: ESP32 Polling Simulation
echo -e "\n📋 Test 9: ESP32 Polling Simulation (3 iterations)"
for i in {1..3}; do
    echo -e "\n--- Polling Iteration $i ---"
    
    # Status update
    log_info "Sending status update..."
    STATUS_RESPONSE=$(curl -s -w "%{http_code}" \
        -X POST \
        -H "Content-Type: application/json" \
        -d "$STATUS_DATA" \
        "$BASE_URL/api/esp32/status")
    HTTP_CODE="${STATUS_RESPONSE: -3}"
    
    if [ "$HTTP_CODE" = "200" ]; then
        log_success "Status update sent"
    else
        log_error "Status update failed: HTTP $HTTP_CODE"
    fi
    
    # Check commands
    log_info "Checking for commands..."
    COMMANDS_RESPONSE=$(curl -s -w "%{http_code}" "$BASE_URL/api/esp32/commands?device_id=$DEVICE_ID")
    HTTP_CODE="${COMMANDS_RESPONSE: -3}"
    RESPONSE_BODY="${COMMANDS_RESPONSE%???}"
    
    if [ "$HTTP_CODE" = "204" ]; then
        log_success "✅ No pending commands (HTTP 204)"
    elif [ "$HTTP_CODE" = "200" ]; then
        log_success "✅ Command received: $RESPONSE_BODY"
    elif [ "$HTTP_CODE" = "404" ]; then
        log_error "❌ Device not found (HTTP 404)"
    else
        log_error "Command check failed: HTTP $HTTP_CODE"
    fi
    
    sleep 2
done

echo -e "\n=============================================="
echo -e "${GREEN}✅ ESP32 Backend Integration Test Complete!${NC}"
echo "=============================================="
