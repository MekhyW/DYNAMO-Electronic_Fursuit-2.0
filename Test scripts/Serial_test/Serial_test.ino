int value1 = 0;
int value2 = 0;
int value3 = 0;
int value4 = 0;
int value5 = 0;
int value6 = 0;
int value7 = 0;
int value8 = 0;
int value9 = 0;
int value10 = 0;
int value11 = 0;

void setup() {
  Serial.begin(9600);
}

String readFromSerial() {
  String received_data;
  while (Serial.available() > 0) {
    received_data = Serial.readStringUntil('\n');
  }
  return received_data;
}

void parseReceivedData(String received_data) {
  int commaIndex1 = received_data.indexOf(',');
  int commaIndex2 = received_data.indexOf(',', commaIndex1 + 1);
  int commaIndex3 = received_data.indexOf(',', commaIndex2 + 1);
  int commaIndex4 = received_data.indexOf(',', commaIndex3 + 1);
  int commaIndex5 = received_data.indexOf(',', commaIndex4 + 1);
  int commaIndex6 = received_data.indexOf(',', commaIndex5 + 1);
  int commaIndex7 = received_data.indexOf(',', commaIndex6 + 1);
  int commaIndex8 = received_data.indexOf(',', commaIndex7 + 1);
  int commaIndex9 = received_data.indexOf(',', commaIndex8 + 1);
  int commaIndex10 = received_data.indexOf(',', commaIndex9 + 1);
  if (commaIndex1 != -1 && commaIndex2 != -1) {
    value1 = received_data.substring(0, commaIndex1).toInt();
    value2 = received_data.substring(commaIndex1 + 1, commaIndex2).toInt();
    value3 = received_data.substring(commaIndex2 + 1, commaIndex3).toInt();
    value4 = received_data.substring(commaIndex3 + 1, commaIndex4).toInt();
    value5 = received_data.substring(commaIndex4 + 1, commaIndex5).toInt();
    value6 = received_data.substring(commaIndex5 + 1, commaIndex6).toInt();
    value7 = received_data.substring(commaIndex6 + 1, commaIndex7).toInt();
    value8 = received_data.substring(commaIndex7 + 1, commaIndex8).toInt();
    value9 = received_data.substring(commaIndex8 + 1, commaIndex9).toInt();
    value10 = received_data.substring(commaIndex9 + 1, commaIndex10).toInt();
    value11 = received_data.substring(commaIndex10 + 1).toInt();
    printValues();
  }
}

void printValues() {
    Serial.print("Received values: ");
    Serial.print(value1);
    Serial.print(", ");
    Serial.print(value2);
    Serial.print(", ");
    Serial.print(value3);
    Serial.print(", ");
    Serial.print(value4);
    Serial.print(", ");
    Serial.print(value5);
    Serial.print(", ");
    Serial.print(value6);
    Serial.print(", ");
    Serial.print(value7);
    Serial.print(", ");
    Serial.print(value8);
    Serial.print(", ");
    Serial.print(value9);
    Serial.print(", ");
    Serial.print(value10);
    Serial.print(", ");
    Serial.println(value11);
}

void loop() {
  String received_data = readFromSerial();
  parseReceivedData(received_data);
}
