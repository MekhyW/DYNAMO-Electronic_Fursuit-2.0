#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

uint16_t BNO055_SAMPLERATE_DELAY_MS = 100;

Adafruit_BNO055 bno = Adafruit_BNO055(55, 0x29, &Wire);
sensors_event_t orientationData , angVelocityData , linearAccelData;

void setupIMU() {
    if (!bno.begin())
    {
        Serial.print("No BNO055 detected ... Check your wiring or I2C ADDR!");
    }
}

void updateIMU() {
    bno.getEvent(&orientationData, Adafruit_BNO055::VECTOR_EULER);
    bno.getEvent(&angVelocityData, Adafruit_BNO055::VECTOR_GYROSCOPE);
    bno.getEvent(&linearAccelData, Adafruit_BNO055::VECTOR_LINEARACCEL);
    vTaskDelay(BNO055_SAMPLERATE_DELAY_MS / portTICK_PERIOD_MS);
}
