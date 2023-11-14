#include <Adafruit_NeoPixel.h>
#define LED_PIN 13
#define LED_COUNT 240
Adafruit_NeoPixel GearsStrip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);
uint32_t black = GearsStrip.Color(0, 0, 0);
uint32_t white = GearsStrip.Color(255, 255, 255);
uint32_t red = GearsStrip.Color(255, 0, 0);
uint32_t purple = GearsStrip.Color(115, 0, 255);
uint32_t yellow = GearsStrip.Color(255, 255, 0);
uint32_t pink = GearsStrip.Color(255, 0, 255);
uint32_t deep_blue = GearsStrip.Color(0, 0, 255);
uint32_t light_blue = GearsStrip.Color(0, 255, 255);
uint32_t orange = GearsStrip.Color(255, 165, 0);
uint32_t green = GearsStrip.Color(0, 255, 0);

int Color_Brightness = 25;
uint32_t color = white;

struct LEDsTaskInput
{
  int leds_on;
  int leds_brightness;
  int leds_color;
  int leds_effect;
  int leds_level;
};

void colorStatic() {
  GearsStrip.setBrightness(Color_Brightness/2);
  GearsStrip.fill(color, 0, GearsStrip.numPixels());
  GearsStrip.show();
}

void colorFade() {
    GearsStrip.setBrightness(Color_Brightness);
    for(int k = 0; k < Color_Brightness*2; k++) {
      GearsStrip.fill(color, 0, GearsStrip.numPixels());
      GearsStrip.setBrightness(k);
      GearsStrip.show();
      vTaskDelay(20 / portTICK_PERIOD_MS);
    }
    for(int k = Color_Brightness*2; k > 0; k--) {
      GearsStrip.fill(color, 0, GearsStrip.numPixels());
      GearsStrip.setBrightness(k);
      GearsStrip.show();
      vTaskDelay(20 / portTICK_PERIOD_MS);
    }
}

void colorWipe() {
  GearsStrip.setBrightness(Color_Brightness);
  if (GearsStrip.getPixelColor(0) == 0)
  {
    for(uint16_t i=0; i<GearsStrip.numPixels(); i++) {
      GearsStrip.setPixelColor(i, color);
      GearsStrip.show();
      vTaskDelay(20 / portTICK_PERIOD_MS);
    }
  } else {
    for(uint16_t i=0; i<GearsStrip.numPixels(); i++) {
      GearsStrip.setPixelColor(i, black);
      GearsStrip.show();
      vTaskDelay(20 / portTICK_PERIOD_MS);
    }
  }
}


void colorTheaterChase() {
  GearsStrip.setBrightness(Color_Brightness*2);
  for(int b=0; b<3; b++) {
    GearsStrip.clear();
    for(int c=b; c<GearsStrip.numPixels(); c += 3) {
      GearsStrip.setPixelColor(c, color);
    }
    GearsStrip.show();
    vTaskDelay(200 / portTICK_PERIOD_MS);
  }
}

void Rainbow() {
  GearsStrip.setBrightness(Color_Brightness*2);
  for(long firstPixelHue = 0; firstPixelHue < 65536; firstPixelHue += 512) {
    for(int i=0; i<GearsStrip.numPixels(); i++) {
      int pixelHue = firstPixelHue + (i * 65536L / GearsStrip.numPixels());
      GearsStrip.setPixelColor(i, GearsStrip.gamma32(GearsStrip.ColorHSV(pixelHue)));
    }
    GearsStrip.show();
    vTaskDelay(50 / portTICK_PERIOD_MS);
  }
}

void colorStrobe() {
  GearsStrip.setBrightness(Color_Brightness/2);
  for(int j = 0; j < 5; j++) {
    GearsStrip.fill(color, 0, GearsStrip.numPixels());
    GearsStrip.show();
    vTaskDelay(50 / portTICK_PERIOD_MS);
    GearsStrip.clear();
    GearsStrip.show();
    vTaskDelay(50 / portTICK_PERIOD_MS);
  }
  vTaskDelay(1000 / portTICK_PERIOD_MS);
}

void colorMovingSubstrips() {
  uint32_t color_a = color;
  uint32_t color_b = black;
  int substrip_size = LED_COUNT/10;
  GearsStrip.setBrightness(Color_Brightness*2);
  int numPixels = GearsStrip.numPixels();
  for(int i = 0; i < numPixels; i++) {
    GearsStrip.clear();
    for(int j = 0; j < numPixels; j += substrip_size*2) {
      int startPixel = (i + j) % numPixels;
      GearsStrip.fill(color_a, startPixel, substrip_size);
      int endPixel = (startPixel + substrip_size) % numPixels;
      GearsStrip.fill(color_b, endPixel, substrip_size);
    }
    GearsStrip.show();
    vTaskDelay(20 / portTICK_PERIOD_MS);
  }
}

void off() {
  GearsStrip.clear();
  GearsStrip.show();
}

void colorLevel(int level){
  GearsStrip.setBrightness(Color_Brightness);
  GearsStrip.clear();
  GearsStrip.fill(color, 0, level);
  GearsStrip.show();
}

void setupLEDs() {
  GearsStrip.begin();
  GearsStrip.setBrightness(Color_Brightness);
  GearsStrip.clear();
  GearsStrip.show();
}