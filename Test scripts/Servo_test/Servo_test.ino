#include <Servo.h>

Servo servo_1;
Servo servo_2;
Servo servo_3;
Servo servo_4;
Servo servo_5;
Servo servo_6;
Servo servo_7;
Servo servo_8;
Servo servo_9;
Servo servo_10;
Servo servo_11;

int pos = 0;

void setup() {
    Serial.begin(9600);
    servo_1.attach(2);
    servo_2.attach(3);
    servo_3.attach(4);
    servo_4.attach(5);
    servo_5.attach(6);
    servo_6.attach(7);
    servo_7.attach(8);
    servo_8.attach(9);
    servo_9.attach(10);
    servo_10.attach(11);
    servo_11.attach(12);
    Serial.println("Attached");
}

void writepos(int pos) {
    servo_1.write(pos);
    servo_2.write(pos);
    servo_3.write(pos);
    servo_4.write(pos);
    servo_5.write(pos);
    servo_6.write(pos);
    servo_7.write(pos);
    servo_8.write(pos);
    servo_9.write(pos);
    servo_10.write(pos);
    servo_11.write(pos);
}

void loop() {
  Serial.println("Sweep...");
  for (pos = 0; pos <= 180; pos += 1) {
    writepos(pos);
    delay(15);
  }
  for (pos = 180; pos >= 0; pos -= 1) {
    writepos(pos);
    delay(15); 
  }
}
