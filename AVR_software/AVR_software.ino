#include <Arduino_FreeRTOS.h>
#include <semphr.h>
#include <queue.h>
#include "LEDs.h"
#include "Servos.h"
#include "Serial.h"
#include "IMU.h"

void setup() {
  Serial.begin(9600);
  while (!Serial) {;}
  Serial.println("Starting up...");
  setupLEDs();
  setupServos();
}

void loop() {}

/*--------------------------------------------------*/
/*---------------------- Tasks ---------------------*/
/*--------------------------------------------------*/
