/*
 ==============================================================================
 Project #190: AI-Powered Queue & Toll Enforcement Node
 Microcontroller: ESP32 DevKit V1 + HC-SR04 Ultrasonic Distance Sensor
 Feature: Embedded Edge AI (TinyML) on-chip Queue State Classification
 
 ALL CONNECTIONS ON THE LEFT SIDE OF ESP32:
  ESP32 V5 (5V)    --------> HC-SR04 VCC (5V)
  ESP32 GND        --------> HC-SR04 GND
  ESP32 G14        --------> HC-SR04 TRIG (GPIO 14 Output)
  ESP32 G27        --------> Voltage Divider Center (GPIO 27 Input: Safe ~3.3V)
 ==============================================================================
*/

#include <WiFi.h>
#include <HTTPClient.h>
#include "queue_tinyml_model.h"

// Set to true only when real Wi-Fi credentials are provided
// (Disabling prevents radio power spikes and reboots on USB power)
const bool ENABLE_WIFI = false;
const char* WIFI_SSID     = "YOUR_WIFI_SSID";
const char* WIFI_PASSWORD = "YOUR_WIFI_PASSWORD";
const char* WEBHOOK_URL   = "https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec";

// HC-SR04 Pin Assignments: Verified Row 23 = G14 (TRIG), Row 22 = G27 (ECHO)
const int PIN_TRIG = 14; 
const int PIN_ECHO = 27; 

// Telemetry & Edge AI Timing
const unsigned long SEND_INTERVAL_MS = 1000; // Measure every 1 second
unsigned long lastSendTime = 0;

// Feature Engineering on ESP32
float rollingAvgDistance = 200.0;
float prevDistance = 200.0;
const float ALPHA = 0.3; // Smoothing coefficient for Exponential Moving Average

void setup() {
  Serial.begin(115200);
  delay(500);
  Serial.println("\n==================================================");
  Serial.println("[ESP32] Initializing Edge AI Smart Queue Sensor...");
  Serial.println("[ESP32] Hardware: TRIG=G14, ECHO=G27 (Left Side)");
  Serial.println("[ESP32] TinyML Decision Tree Model: Loaded on-chip");
  Serial.println("==================================================");

  pinMode(PIN_TRIG, OUTPUT);
  pinMode(PIN_ECHO, INPUT);

  if (ENABLE_WIFI) {
    Serial.printf("[ESP32] Connecting to Wi-Fi: %s", WIFI_SSID);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 10) {
      delay(500);
      Serial.print(".");
      attempts++;
    }
    if (WiFi.status() == WL_CONNECTED) {
      Serial.println("\n[ESP32] Wi-Fi Connected!");
    } else {
      Serial.println("\n[ESP32] Wi-Fi offline.");
    }
  } else {
    Serial.println("[ESP32] Running in High-Speed Local Edge AI Mode (Wi-Fi Radio OFF).");
  }
}

long lastDuration = 0;

float measureDistanceCm() {
  digitalWrite(PIN_TRIG, LOW);
  delayMicroseconds(2);
  digitalWrite(PIN_TRIG, HIGH);
  delayMicroseconds(10);
  digitalWrite(PIN_TRIG, LOW);

  // 30ms timeout ~ 5 meters
  lastDuration = pulseIn(PIN_ECHO, HIGH, 30000);
  if (lastDuration == 0) {
    return 400.0; // Out of range
  }
  return (lastDuration * 0.0343) / 2.0;
}

void loop() {
  unsigned long now = millis();

  if (now - lastSendTime >= SEND_INTERVAL_MS) {
    lastSendTime = now;

    // 1. Raw Sensor Reading
    float currentDistance = measureDistanceCm();

    // 2. Feature Extraction on ESP32: Exponential Moving Average & Rate of Change
    rollingAvgDistance = (ALPHA * currentDistance) + ((1.0 - ALPHA) * rollingAvgDistance);
    float rateOfChange = currentDistance - prevDistance;
    prevDistance = currentDistance;

    // 3. Run TinyML Edge AI Inference Directly on ESP32 Chip!
    QueueState predictedState = predictQueueStateOnChip(currentDistance, rollingAvgDistance, rateOfChange);
    const char* stateName = getQueueStateName(predictedState);

    // 4. Output Inference Results over Serial
    Serial.printf("[Sensor] Distance: %5.1f cm (duration: %ld us) | Rolling: %5.1f cm | TinyML AI: >>> %s <<<\n", 
                  currentDistance, lastDuration, rollingAvgDistance, stateName);
  }

  delay(20);
}
