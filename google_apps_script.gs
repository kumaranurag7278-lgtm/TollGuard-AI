/**
 * ==============================================================================
 * Google Apps Script Webhook: IoT Telemetry Receiver (Project #190)
 * 
 * DEPLOYMENT INSTRUCTIONS:
 * 1. Open Google Sheets -> Extensions -> Apps Script.
 * 2. Paste this entire code into `Code.gs`.
 * 3. Click "Deploy" -> "New deployment".
 * 4. Select type: "Web app".
 * 5. Description: "ESP32 Toll Queue Telemetry".
 * 6. Execute as: "Me (your email)".
 * 7. Who has access: "Anyone" (allows ESP32 without OAuth headers).
 * 8. Click Deploy, copy the "Web app URL", and paste it into `esp32_sensor_node.ino`.
 * ==============================================================================
 */

function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    
    // Ensure header row exists on first run
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(["Timestamp", "Device ID", "Distance (cm)", "Queue Proximity State"]);
    }
    
    var data = JSON.parse(e.postData.contents);
    var timestamp = new Date();
    var deviceId = data.device_id || "UNKNOWN_NODE";
    var distanceCm = parseFloat(data.distance_cm);
    
    // Proximity classification rule
    var state = "Empty / Standby";
    if (distanceCm < 60) {
      state = "Object at Barrier / Counter";
    } else if (distanceCm < 150) {
      state = "Active Approaching Object";
    }
    
    // Append row to Google Sheets
    sheet.appendRow([timestamp, deviceId, distanceCm, state]);
    
    return ContentService.createTextOutput(JSON.stringify({
      "status": "success",
      "logged_at": timestamp.toISOString(),
      "distance": distanceCm
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      "status": "error",
      "message": error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}

function doGet(e) {
  return ContentService.createTextOutput("Toll/Queue IoT Webhook is ACTIVE.");
}
