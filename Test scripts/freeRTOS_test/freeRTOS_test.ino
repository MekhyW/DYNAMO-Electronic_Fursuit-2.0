#include <Arduino_FreeRTOS.h>
#include <semphr.h>
#include <queue.h>
#include "freeRTOS_test.h"

QueueHandle_t integerQueue;

SemaphoreHandle_t mutex;

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB, on LEONARDO, MICRO, YUN, and other 32u4 based boards.
  }
  xTaskCreate(TaskBlink, "Blink", 128, NULL, 2, NULL); //stack size 128, priority 2
  xTaskCreate(TaskAnalogRead, "AnalogRead", 128, NULL, 1, NULL); //stack size 128, priority 1
  xTaskCreate(TaskPrint, "Print", 128, NULL, 1, NULL); //stack size 128, priority 1
  xTaskCreate(TaskNotifyLed, "NotifyLed", 128, NULL, 1, NULL); //stack size 128, priority 1
  integerQueue = xQueueCreate(10, sizeof(int)); //queue size 10, item size int
  mutex = xSemaphoreCreateMutex();
}

void loop(){}

/*--------------------------------------------------*/
/*---------------------- Tasks ---------------------*/
/*--------------------------------------------------*/

void TaskBlink(void *pvParameters)
{
  (void) pvParameters;
  pinMode(LED_BUILTIN, OUTPUT);
  for (;;)
  {
    digitalWrite(LED_BUILTIN, HIGH);
    xSemaphoreGive(mutex);
    vTaskDelay( 1000 / portTICK_PERIOD_MS ); // wait for one second
    digitalWrite(LED_BUILTIN, LOW);
    xSemaphoreGive(mutex);
    vTaskDelay( 1000 / portTICK_PERIOD_MS ); // wait for one second
  }
}

void TaskAnalogRead(void *pvParameters)
{
  (void) pvParameters;
  for (;;)
  {
    int sensorValue = analogRead(A0);
    xQueueSend(integerQueue, &sensorValue, portMAX_DELAY);
    vTaskDelay(100 / portTICK_PERIOD_MS);
  }
}

void TaskPrint(void *pvParameters)
{
  (void) pvParameters;
  for (;;)
  {
    int value = 0;
    if (xQueueReceive(integerQueue, &value, portMAX_DELAY) == pdPASS) {
      Serial.println(value);
    }
    vTaskDelay(1);
  }
}

void TaskNotifyLed(void *pvParameters)
{
  (void) pvParameters;
  for (;;)
  {
    if (xSemaphoreTake(mutex, 10) == pdTRUE) {
      Serial.println("LED switched");
    }
    vTaskDelay(1);
  }
}
