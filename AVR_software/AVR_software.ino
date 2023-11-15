#include <Arduino_FreeRTOS.h>
#include <semphr.h>
#include <queue.h>
#include "LEDs.h"
#include "Servos.h"
#include "Serial.h"
#include "IMU.h"

QueueHandle_t queue_leds;
QueueHandle_t queue_servos;

void setup() {
  Serial.begin(9600);
  while (!Serial) {;}
  Serial.println("Starting up...");
  setupLEDs();
  setupServos();
  xTaskCreate(TaskReadSerial, "ReadSerial", 128, NULL, 1, NULL);
  xTaskCreate(TaskLEDs, "LEDs", 128, NULL, 1, NULL);
  xTaskCreate(TaskServos, "Servos", 128, NULL, 1, NULL);
  queue_leds = xQueueCreate(10, sizeof(LEDsTaskInput));
  queue_servos = xQueueCreate(10, sizeof(ServosTaskInput));
}

void loop() {}

/*--------------------------------------------------*/
/*---------------------- Tasks ---------------------*/
/*--------------------------------------------------*/

void TaskReadSerial(void *pvParameters) {
  (void) pvParameters;
  for (;;) {
    updateSerial();
    LEDsTaskInput leds_input;
    ServosTaskInput servos_input;
    servos_input.animatronics_on = inputs[0];
    leds_input.leds_on = inputs[1];
    leds_input.leds_brightness = inputs[2];
    leds_input.leds_color = inputs[3];
    leds_input.leds_effect = inputs[4];
    leds_input.leds_level = inputs[5];
    servos_input.emotion_angry = inputs[6];
    servos_input.emotion_disgusted = inputs[7];
    servos_input.emotion_happy = inputs[8];
    servos_input.emotion_neutral = inputs[9];
    servos_input.emotion_sad = inputs[10];
    servos_input.emotion_surprised = inputs[11];
    xQueueSendToFront(queue_leds, &leds_input, 0);
    xQueueSendToFront(queue_servos, &servos_input, 0);
    vTaskDelay(10);
  }
}

void TaskLEDs(void *pvParameters) {
  (void) pvParameters;
  for (;;) {
    LEDsTaskInput leds_input;
    xQueueReceive(queue_leds, &leds_input, portMAX_DELAY);
    if (leds_input.leds_on == 1) {
      Color_Brightness = leds_input.leds_brightness;
      color = (leds_input.leds_color == 0) ? white : (leds_input.leds_color == 1) ? red : (leds_input.leds_color == 2) ? purple
            : (leds_input.leds_color == 3) ? yellow : (leds_input.leds_color == 4) ? pink : (leds_input.leds_color == 5) ? deep_blue
            : (leds_input.leds_color == 6) ? light_blue : (leds_input.leds_color == 7) ? orange : (leds_input.leds_color == 8) ? green 
            : white;
      switch (leds_input.leds_effect) {
        case 0: colorStatic(); break;
        case 1: colorFade(); break;
        case 2: colorWipe(); break;
        case 3: colorTheaterChase(); break;
        case 4: Rainbow(); break;
        case 5: colorStrobe(); break;
        case 6: colorMovingSubstrips(); break;
        case 7: off(); break;
        case 8: colorLevel(leds_input.leds_level); break;
        default: colorStatic(); break;
      }
    } else {
      off();
    }
    vTaskDelay(10);
  }
}

void TaskServos(void *pvParameters) {
  (void) pvParameters;
  for (;;) {
    ServosTaskInput servos_input;
    xQueueReceive(queue_servos, &servos_input, portMAX_DELAY);
    int expressions_sum = servos_input.emotion_angry + servos_input.emotion_disgusted + servos_input.emotion_happy
                            + servos_input.emotion_neutral + servos_input.emotion_sad + servos_input.emotion_surprised;
    if (servos_input.animatronics_on == 1 && expressions_sum > 0) {
      float emotions[6] = {servos_input.emotion_angry / expressions_sum, servos_input.emotion_disgusted / expressions_sum,
                          servos_input.emotion_happy / expressions_sum, servos_input.emotion_neutral / expressions_sum,
                          servos_input.emotion_sad / expressions_sum, servos_input.emotion_surprised / expressions_sum};
      int pos[9] = {0, 0, 0, 0, 0, 0, 0, 0, 0};
      for (int i = 0; i < 6; i++) {
        for (int j = 0; j < 9; j++) {
          pos[j] += emotions[i] * servo_calibration_matrix[i][j];
        }
      }
      writepos(pos[0], pos[1], pos[2], pos[3], pos[4], pos[5], pos[6], pos[7], pos[8]);
    }
    vTaskDelay(10);
  }
}
