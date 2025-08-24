/*
 * SmartBin ESP32 Controller (Corrected, Optimized & Verbose Logging)
 *
 * This ESP32 Arduino sketch controls a SmartBin lid via servo motor
 * and communicates with the backend API for bottle recycling operations.
 *
 * Revision Highlights:
 * - ADDED: Extensive serial logging for detailed execution tracing, state
 * machine transitions, and API interactions to simplify debugging.
 * - CRITICAL FIX: Added NTP time synchronization after every WiFi reconnect to
 * prevent SSL/TLS certificate validation failures caused by time drift.
 * - OPTIMIZED: Replaced String class concatenation for API URLs with snprintf
 * to prevent heap fragmentation and improve long-term stability.
 * - IMPROVED: Enhanced readability of JSON command parsing.
 * - Maintained non-blocking state machine for lid control.
 * - Maintained secure HTTPS implementation with WiFiClientSecure.
 * - Maintained efficient resource management using local HTTPClient instances.
 *
 * Hardware Requirements:
 * - ESP32 Development Board (ESP32-WROOM-32 recommended)
 * - Servo Motor (for lid control)
 * - Power Supply (5V for ESP32, appropriate for servo)
 * - WiFi Connection
 *
 * Pin Connections:
 * - GPIO 18 -> Servo Motor Signal
 * - GPIO 2  -> Status LED
 * - 5V      -> Servo Power
 * - GND     -> Common Ground
 *
 * Version: 1.2.3
 * Last Updated: 2025-08-24
 */

 #include <WiFi.h>
 #include <WiFiClientSecure.h>
 #include <HTTPClient.h>
 #include <ArduinoJson.h>
 #include <ESP32Servo.h>
 #include <time.h>
 
 // ============================================================================
 // CONFIGURATION SECTION - UPDATE THESE VALUES
 // ============================================================================
 
 // WiFi Configuration
 const char* ssid = "###";
 const char* password = "1234nais";
 
 // Backend Configuration
 const char* serverUrl = "https://api.setorin.app";
 const char* apiEndpoint = "/api/esp32";
 
 // Device Configuration
 const char* deviceId = "ESP32-SMARTBIN-001";
 const char* firmwareVersion = "1.2.3"; // Updated version
 const char* hardwareVersion = "ESP32-WROOM-32";
 const char* location = "Main Entrance";
 
 // Hardware Configuration
 #define SERVO_PIN 18
 #define STATUS_LED_PIN 2
 #define BATTERY_ADC_PIN 34 // Note: ADC2 pins cannot be used when WiFi is active. ADC1 (GPIOs 32-39) is safe.
 
 // ============================================================================
 // SSL CERTIFICATE
 // ============================================================================
 // Root CA certificate for api.setorin.app (Let's Encrypt ISRG Root X1)
 const char* rootCACertificate = \
 "-----BEGIN CERTIFICATE-----\n" \
 "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\n" \
 "-----END CERTIFICATE-----\n";
 
 // ============================================================================
 // TIMING CONSTANTS
 // ============================================================================
 const unsigned long STATUS_INTERVAL = 30000;       // 30 seconds
 const unsigned long COMMAND_CHECK_INTERVAL = 5000; // 5 seconds
 const unsigned long RECONNECT_INTERVAL = 10000;    // 10 seconds
 const unsigned long REGISTER_INTERVAL = 30000;     // 30 seconds to retry registration
 const unsigned long SERVO_TRAVEL_TIME = 750;       // Time in ms for servo to physically move
 
 // ============================================================================
 // SERVO POSITIONS
 // ============================================================================
 const int LID_CLOSED_POSITION = 38;
 const int LID_OPEN_POSITION = 180;
 
 // ============================================================================
 // NON-BLOCKING STATE MACHINE FOR LID CONTROL
 // ============================================================================
 enum LidState { IDLE, OPENING, AWAITING_OPEN, WAITING, CLOSING, AWAITING_CLOSE };
 LidState currentLidState = IDLE;
 unsigned long lidStateChangeTime = 0;
 unsigned long lidWaitDuration = 0;
 
 // ============================================================================
 // GLOBAL OBJECTS AND VARIABLES
 // ============================================================================
 Servo lidServo;
 
 // State Variables
 bool deviceRegistered = false;
 unsigned long lastStatusUpdate = 0;
 unsigned long lastCommandCheck = 0;
 unsigned long lastReconnectAttempt = 0;
 unsigned long lastRegisterAttempt = 0;
 
 // ============================================================================
 // SETUP FUNCTION
 // ============================================================================
 void setup() {
     Serial.begin(115200);
     Serial.println("\n\n=== SmartBin ESP32 Controller (Verbose) ===");
     Serial.printf("[SETUP] Firmware v%s, Device ID: %s\n", firmwareVersion, deviceId);
     
     initializeHardware();
     connectWiFi();
     // Time sync is now handled within connectWiFi()
     
     Serial.println("[SETUP] =====================================\n");
 }
 
 // ============================================================================
 // MAIN LOOP
 // ============================================================================
 void loop() {
     unsigned long currentMillis = millis();
 
     // Handle WiFi connection and reconnection logic
     if (WiFi.status() != WL_CONNECTED) {
         if (currentMillis - lastReconnectAttempt >= RECONNECT_INTERVAL) {
             // LOG: Indicate a reconnection attempt is starting.
             Serial.println("[LOOP] WiFi disconnected. Attempting to reconnect...");
             lastReconnectAttempt = currentMillis;
             connectWiFi();
         }
         return; // Do nothing else if not connected
     }

     // Test backend connectivity periodically
     static unsigned long lastConnectionTest = 0;
     if (currentMillis - lastConnectionTest >= 60000) { // Test every minute
         lastConnectionTest = currentMillis;
         if (!testBackendConnection()) {
             Serial.println("[LOOP] Backend connectivity test failed. Will retry registration.");
             deviceRegistered = false;
         }
     }

     // Ensure device is registered after connecting
     if (!deviceRegistered) {
         if (currentMillis - lastRegisterAttempt >= REGISTER_INTERVAL) {
             // LOG: Indicate a registration attempt is starting.
             Serial.println("[LOOP] Device not registered. Attempting registration...");
             lastRegisterAttempt = currentMillis;
             registerDevice();
         }
     }

     // Only perform network tasks if the device is successfully registered
     if (deviceRegistered) {
         // Send periodic status updates
         if (currentMillis - lastStatusUpdate >= STATUS_INTERVAL) {
             // LOG: Indicate a periodic status update is due.
             Serial.println("[LOOP] Status interval elapsed. Triggering status update.");
             lastStatusUpdate = currentMillis;
             sendStatusUpdate();
         }

         // Check for incoming commands from the backend
         if (currentMillis - lastCommandCheck >= COMMAND_CHECK_INTERVAL) {
             // LOG: Indicate a periodic command check is due.
             Serial.println("[LOOP] Command check interval elapsed. Triggering command check.");
             lastCommandCheck = currentMillis;
             checkForCommands();
         }
     }

     // Handle the non-blocking lid control state machine
     handleLidControl();

     // Handle persistent errors and recovery
     handlePersistentErrors();

     // Handle commands from the Serial monitor for debugging
     handleSerialCommands();
     
     delay(10); // Small delay to yield to other tasks
 }
 
 // ============================================================================
 // INITIALIZATION FUNCTIONS
 // ============================================================================
 void initializeHardware() {
     Serial.println("[INIT] Initializing hardware...");
     lidServo.attach(SERVO_PIN);
     lidServo.write(LID_CLOSED_POSITION);
     pinMode(STATUS_LED_PIN, OUTPUT);
     digitalWrite(STATUS_LED_PIN, LOW); // LED off initially
     Serial.println("[INIT] ✓ Hardware initialization complete.");
 }
 
 void connectWiFi() {
     Serial.printf("[WIFI] Attempting connection to SSID: %s\n", ssid);
     
     WiFi.begin(ssid, password);
     
     int attempts = 0;
     while (WiFi.status() != WL_CONNECTED && attempts < 20) {
         delay(500);
         Serial.print(".");
         attempts++;
     }
     
     if (WiFi.status() == WL_CONNECTED) {
         Serial.println("\n[WIFI] ✓ WiFi connected successfully!");
         Serial.printf("[WIFI]  - IP Address: %s\n", WiFi.localIP().toString().c_str());
         digitalWrite(STATUS_LED_PIN, HIGH); // LED on to indicate connection
         
         // CRITICAL FIX: Always re-synchronize time after a successful connection.
         syncTime(); 
 
         deviceRegistered = false; // Force re-registration attempt on new connection
         lastRegisterAttempt = millis(); // Set timer for the first registration attempt
     } else {
         Serial.println("\n[WIFI] ✗ WiFi connection failed.");
         digitalWrite(STATUS_LED_PIN, LOW);
     }
 }
 
 void syncTime() {
     Serial.print("[TIME] Synchronizing time with NTP server...");
     configTime(0, 0, "pool.ntp.org");
     
     time_t now = time(nullptr);
     // Wait until time is greater than a plausible value (e.g., year 2022)
     while (now < 1640995200) {
         delay(500);
         Serial.print(".");
         now = time(nullptr);
     }
     
     Serial.println(" ✓ Time synchronized!");
     struct tm timeinfo;
     gmtime_r(&now, &timeinfo);
     Serial.printf("[TIME]  - Current UTC time: %s", asctime(&timeinfo));
 }
 
 // ============================================================================
 // API COMMUNICATION FUNCTIONS
 // ============================================================================
 void registerDevice() {
     if (WiFi.status() != WL_CONNECTED) return;
     
     WiFiClientSecure client;
     client.setCACert(rootCACertificate);
     HTTPClient http;

     char url[128];
     snprintf(url, sizeof(url), "%s%s/register", serverUrl, apiEndpoint);

     // LOG: Announce the start of the device registration API call.
     Serial.println("[API] Attempting to register device with backend...");
     Serial.printf("[API]  - URL: %s\n", url);

     if (http.begin(client, url)) {
         http.addHeader("Content-Type", "application/json");
         
         JsonDocument doc;
         doc["device_id"] = deviceId;
         doc["firmware_version"] = firmwareVersion;
         doc["hardware_version"] = hardwareVersion;
         doc["location"] = location;
         
         String jsonString;
         serializeJson(doc, jsonString);
         
         // LOG: Show the JSON payload being sent.
         Serial.printf("[API]  - POST Body: %s\n", jsonString.c_str());
         
         int httpResponseCode = http.POST(jsonString);
         
         if (httpResponseCode == 200 || httpResponseCode == 201) {
             Serial.printf("[API] ✓ Device registration successful (HTTP %d)\n", httpResponseCode);
             deviceRegistered = true;
         } else {
             Serial.printf("[API] ✗ Device registration failed (HTTP %d): %s\n", httpResponseCode, http.errorToString(httpResponseCode).c_str());
             // Get response body for debugging
             String responseBody = http.getString();
             if (responseBody.length() > 0) {
                 Serial.printf("[API]  - Response: %s\n", responseBody.c_str());
             }
             deviceRegistered = false;
         }
         http.end();
     } else {
         Serial.println("[API] ✗ Failed to begin HTTP client for registration.");
         deviceRegistered = false;
     }
 }
 
 void sendStatusUpdate() {
     if (WiFi.status() != WL_CONNECTED || !deviceRegistered) return;
     
     WiFiClientSecure client;
     client.setCACert(rootCACertificate);
     HTTPClient http;

     char url[128];
     snprintf(url, sizeof(url), "%s%s/status", serverUrl, apiEndpoint);

     // LOG: Announce the start of the status update API call.
     Serial.println("[API] Sending status update...");
     Serial.printf("[API]  - URL: %s\n", url);

     if (http.begin(client, url)) {
         http.addHeader("Content-Type", "application/json");
         
         JsonDocument doc;
         doc["device_id"] = deviceId;
         doc["status"] = "online";
         doc["last_seen"] = getCurrentTimeISO(); // Use current time in ISO format
         doc["battery_level"] = (int)readBatteryLevel(); // Cast to int as backend expects
         doc["temperature"] = readTemperature(); // Keep as float
         
         String jsonString;
         serializeJson(doc, jsonString);
         
         // LOG: Show the JSON payload being sent.
         Serial.printf("[API]  - POST Body: %s\n", jsonString.c_str());
         
         int httpResponseCode = http.POST(jsonString);
         
         if (httpResponseCode == 200) {
             Serial.printf("[API] ✓ Status update sent (HTTP %d)\n", httpResponseCode);
             resetErrorCount(); // Reset error count on success
         } else {
             Serial.printf("[API] ✗ Status update failed (HTTP %d): %s\n", httpResponseCode, http.errorToString(httpResponseCode).c_str());
             // Get response body for debugging
             String responseBody = http.getString();
             if (responseBody.length() > 0) {
                 Serial.printf("[API]  - Response: %s\n", responseBody.c_str());
             }
             incrementErrorCount(); // Increment error count
         }
         http.end();
     } else {
         Serial.println("[API] ✗ Failed to begin HTTP client for status update.");
     }
 }
 
 void checkForCommands() {
     if (WiFi.status() != WL_CONNECTED || !deviceRegistered) return;

     WiFiClientSecure client;
     client.setCACert(rootCACertificate);
     HTTPClient http;

     char url[128];
     snprintf(url, sizeof(url), "%s%s/commands?device_id=%s", serverUrl, apiEndpoint, deviceId);

     // LOG: Announce the start of the command check API call.
     Serial.println("[API] Checking for commands...");
     Serial.printf("[API]  - URL: %s\n", url);

     if (http.begin(client, url)) {
         int httpResponseCode = http.GET();
         if (httpResponseCode == 200) {
             String payload = http.getString();
             // LOG: Show the raw payload received from the server.
             Serial.printf("[API] ✓ Received response (HTTP %d)\n", httpResponseCode);
             Serial.printf("[API]  - Payload: %s\n", payload.c_str());

             JsonDocument doc;
             DeserializationError error = deserializeJson(doc, payload);

             if (error) {
                 Serial.printf("[API] ✗ Failed to parse command JSON: %s\n", error.c_str());
             } else {
                 const char* command = doc["command"];
                 if (command) {
                     if (strcmp(command, "open_lid") == 0) {
                         int duration = doc["duration"] | 5; // Default to 5 seconds
                         // LOG: Command successfully parsed.
                         Serial.printf("[CMD] Parsed 'open_lid' command with duration: %d seconds\n", duration);
                         openLid(duration);
                     } else if (strcmp(command, "close_lid") == 0) {
                         // LOG: Command successfully parsed.
                         Serial.println("[CMD] Parsed 'close_lid' command.");
                         closeLid();
                     }
                 } else {
                     // LOG: Payload was valid JSON but contained no command.
                     Serial.println("[API]  - Valid JSON received, but no 'command' key found.");
                 }
             }
         } else if (httpResponseCode == 204) {
             // LOG: A 204 response is normal when there are no new commands.
             Serial.printf("[API] ✓ Received response (HTTP %d): No new commands.\n", httpResponseCode);
             resetErrorCount(); // Reset error count on success
         } else if (httpResponseCode == 404) {
             Serial.printf("[API] ✗ Command endpoint not found (HTTP %d). Device may not be properly registered.\n", httpResponseCode);
             // Try to re-register the device
             Serial.println("[API] Attempting to re-register device...");
             deviceRegistered = false;
             registerDevice();
             incrementErrorCount(); // Increment error count
         } else {
             Serial.printf("[API] ✗ Command check request failed (HTTP %d): %s\n", httpResponseCode, http.errorToString(httpResponseCode).c_str());
             // Get response body for debugging
             String responseBody = http.getString();
             if (responseBody.length() > 0) {
                 Serial.printf("[API]  - Response: %s\n", responseBody.c_str());
             }
             incrementErrorCount(); // Increment error count
         }
         http.end();
     } else {
         Serial.println("[API] ✗ Failed to begin HTTP client for command check.");
     }
 }
 
 // ============================================================================
 // LID CONTROL STATE MACHINE
 // ============================================================================
 void openLid(int durationSeconds) {
     if (currentLidState != IDLE) {
         // LOG: Explain why the command is being ignored.
         Serial.println("[LID] Lid is already busy. Ignoring new 'open' command.");
         return;
     }
     Serial.printf("[LID] Command received: Opening lid for %d seconds.\n", durationSeconds);
     lidWaitDuration = durationSeconds * 1000;
     // LOG: Manually log state change since it happens outside the state machine handler.
     Serial.println("[STATE] -> OPENING");
     currentLidState = OPENING;
     lidStateChangeTime = millis();
 }
 
 void closeLid() {
     if (currentLidState == IDLE || currentLidState == CLOSING || currentLidState == AWAITING_CLOSE) {
         // LOG: Explain why the command is being ignored.
         Serial.println("[LID] Lid is already closing or closed. Ignoring new 'close' command.");
         return;
     }
     Serial.println("[LID] Command received: Closing lid immediately.");
     // LOG: Manually log state change since it happens outside the state machine handler.
     Serial.println("[STATE] -> CLOSING");
     currentLidState = CLOSING;
     lidStateChangeTime = millis();
 }
 
 void handleLidControl() {
     unsigned long currentMillis = millis();
 
     switch (currentLidState) {
         case IDLE:
             // Do nothing
             break;
 
         case OPENING:
             // This case now acts as a trigger and immediately transitions.
             lidServo.write(LID_OPEN_POSITION);
             currentLidState = AWAITING_OPEN;
             lidStateChangeTime = currentMillis; 
             // LOG: Log the new state after the change.
             Serial.println("[STATE] -> AWAITING_OPEN");
             break;
 
         case AWAITING_OPEN:
             if (currentMillis - lidStateChangeTime >= SERVO_TRAVEL_TIME) {
                 currentLidState = WAITING;
                 lidStateChangeTime = currentMillis; // Reset timer for the wait period
                 // LOG: Log the new state after the change.
                 Serial.printf("[STATE] -> WAITING (for %lu ms)\n", lidWaitDuration);
             }
             break;
 
         case WAITING:
             if (currentMillis - lidStateChangeTime >= lidWaitDuration) {
                 currentLidState = CLOSING;
                 lidStateChangeTime = currentMillis;
                 // LOG: Log the new state after the change.
                 Serial.println("[STATE] -> CLOSING");
             }
             break;
 
         case CLOSING:
             // This case now acts as a trigger and immediately transitions.
             lidServo.write(LID_CLOSED_POSITION);
             currentLidState = AWAITING_CLOSE;  
             lidStateChangeTime = currentMillis;
             // LOG: Log the new state after the change.
             Serial.println("[STATE] -> AWAITING_CLOSE");
             break;
         
         case AWAITING_CLOSE:
             if (currentMillis - lidStateChangeTime >= SERVO_TRAVEL_TIME) {
                 currentLidState = IDLE;
                 // LOG: Log the new state after the change.
                 Serial.println("[STATE] -> IDLE (Lid sequence complete!)");
             }
             break;
     }
 }
 
 // ============================================================================
 // ERROR RECOVERY
 // ============================================================================
 void handlePersistentErrors() {
     static int consecutiveErrors = 0;
     static unsigned long lastErrorReset = 0;
     
     if (consecutiveErrors >= 5) {
         Serial.println("[ERROR] Too many consecutive errors. Attempting recovery...");
         Serial.println("[ERROR] Resetting device registration and reconnecting...");
         
         deviceRegistered = false;
         consecutiveErrors = 0;
         lastErrorReset = millis();
         
         // Force WiFi reconnection
         WiFi.disconnect();
         delay(1000);
         connectWiFi();
     }
 }

 void resetErrorCount() {
     static int consecutiveErrors = 0;
     consecutiveErrors = 0;
 }

 void incrementErrorCount() {
     static int consecutiveErrors = 0;
     consecutiveErrors++;
     Serial.printf("[ERROR] Error count: %d/5\n", consecutiveErrors);
 }

 // ============================================================================
 // CONNECTION TESTING
 // ============================================================================
 bool testBackendConnection() {
     if (WiFi.status() != WL_CONNECTED) return false;
     
     WiFiClientSecure client;
     client.setCACert(rootCACertificate);
     HTTPClient http;

     char url[128];
     snprintf(url, sizeof(url), "%s/health", serverUrl);

     Serial.println("[TEST] Testing backend connectivity...");
     Serial.printf("[TEST]  - URL: %s\n", url);

     if (http.begin(client, url)) {
         int httpResponseCode = http.GET();
         if (httpResponseCode == 200) {
             Serial.println("[TEST] ✓ Backend is reachable");
             http.end();
             return true;
         } else {
             Serial.printf("[TEST] ✗ Backend health check failed (HTTP %d)\n", httpResponseCode);
             http.end();
             return false;
         }
     } else {
         Serial.println("[TEST] ✗ Failed to begin HTTP client for health check");
         return false;
     }
 }
 
 // ============================================================================
 // TIME UTILITIES
 // ============================================================================
 String getCurrentTimeISO() {
     time_t now;
     struct tm timeinfo;
     if (!getLocalTime(&timeinfo)) {
         return "2025-08-24T01:46:56Z"; // Fallback if time sync fails
     }
     
     char timeString[32];
     strftime(timeString, sizeof(timeString), "%Y-%m-%dT%H:%M:%SZ", &timeinfo);
     return String(timeString);
 }

 // ============================================================================
 // SENSOR READING (MOCK FUNCTIONS)
 // ============================================================================
 float readBatteryLevel() {
     float level = 80.0 + (esp_random() % 15);
     // LOG: Report the mock value being generated.
     Serial.printf("[SENSOR] Mock battery level generated: %.2f%%\n", level);
     return level;
 }
 
 float readTemperature() {
     float temp = 25.0 + ((esp_random() % 100) / 10.0) - 5.0;
     // LOG: Report the mock value being generated.
     Serial.printf("[SENSOR] Mock temperature generated: %.2f C\n", temp);
     return temp;
 }
 
 // ============================================================================
 // SERIAL DEBUG INTERFACE
 // ============================================================================
 void handleSerialCommands() {
     if (Serial.available()) {
         String command = Serial.readStringUntil('\n');
         command.trim();
         // LOG: Show the command received via serial for easier debugging.
         Serial.printf("[SERIAL] Command received: '%s'\n", command.c_str());
         if (command == "open") {
             openLid(5); // Test open for 5 seconds
         } else if (command == "close") {
             closeLid();
         } else if (command == "status") {
             sendStatusUpdate();
         } else if (command == "register") {
             deviceRegistered = false;
             registerDevice();
         } else if (command == "commands") {
             checkForCommands();
         } else if (command == "test") {
             testBackendConnection();
         } else if (command == "reset") {
             resetErrorCount();
             Serial.println("[SERIAL] Error count reset to 0");
         } else if (command == "restart") {
             ESP.restart();
         } else if (command == "help") {
             Serial.println("[SERIAL] Available commands:");
             Serial.println("  open     - Open lid for 5 seconds");
             Serial.println("  close    - Close lid immediately");
             Serial.println("  status   - Send status update to backend");
             Serial.println("  register - Re-register device with backend");
             Serial.println("  commands - Check for commands from backend");
             Serial.println("  test     - Test backend connectivity");
             Serial.println("  reset    - Reset error count");
             Serial.println("  restart  - Restart ESP32");
             Serial.println("  help     - Show this help message");
         }
     }
 }