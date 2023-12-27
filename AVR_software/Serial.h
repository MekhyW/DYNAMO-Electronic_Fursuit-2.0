#define NUM_INPUTS 12
int inputs[NUM_INPUTS] = {0};

String readFromSerial() {
  String received_data;
  while (Serial.available() > 0) {
    received_data = Serial.readStringUntil('\n');
  }
  return received_data;
}

bool parseReceivedData(String received_data) {
  int commaIndex = -1;
  int startIndex = 0;
  for (int i = 0; i < NUM_INPUTS; i++) {
    commaIndex = received_data.indexOf(',', startIndex);
    if (commaIndex != -1) {
      inputs[i] = received_data.substring(startIndex, commaIndex).toInt();
      startIndex = commaIndex + 1;
    } else {
      return false;
    }
  }
  return true;
}

void updateSerial() {
  String received_data = readFromSerial();
  if (received_data.length() > 0) {
    if (parseReceivedData(received_data)) {
      Serial.println("Acknowledged: " + received_data);
    } else {
      Serial.println("Invalid message format!");
    }
  }
}