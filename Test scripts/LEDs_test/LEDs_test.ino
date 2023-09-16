#include <Adafruit_NeoPixel.h>
#define LED_PIN 10
#define LED_COUNT 240
Adafruit_NeoPixel GearsStrip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);
int Color_Brightness = 25;
uint32_t black = GearsStrip.Color(0, 0, 0);
uint32_t white = GearsStrip.Color(255, 255, 255);
uint32_t red = GearsStrip.Color(255, 0, 0);
uint32_t yellow = GearsStrip.Color(255, 255, 0);
uint32_t pink = GearsStrip.Color(255, 0, 255);
uint32_t deep_blue = GearsStrip.Color(0, 0, 255);
uint32_t light_blue = GearsStrip.Color(0, 255, 255);
uint32_t orange = GearsStrip.Color(255, 165, 0);
uint32_t green = GearsStrip.Color(0, 255, 0);
uint32_t purple = GearsStrip.Color(115, 0, 255);

void colorStatic(uint32_t color) {
  GearsStrip.setBrightness(Color_Brightness/2);
  GearsStrip.fill(color, 0, GearsStrip.numPixels());
  GearsStrip.show();
}

void colorFade(uint32_t color){
    GearsStrip.setBrightness(Color_Brightness);
    for(int k = 0; k < Color_Brightness*2; k++) {
      GearsStrip.fill(color, 0, GearsStrip.numPixels());
      GearsStrip.setBrightness(k);
      GearsStrip.show();
      delay(20);
    }
    for(int k = Color_Brightness*2; k > 0; k--) {
      GearsStrip.fill(color, 0, GearsStrip.numPixels());
      GearsStrip.setBrightness(k);
      GearsStrip.show();
      delay(20);
    }
}

void colorWipe(uint32_t color) {
  GearsStrip.setBrightness(Color_Brightness);
  if (GearsStrip.getPixelColor(0) == 0)
  {
    for(uint16_t i=0; i<GearsStrip.numPixels(); i++) {
      GearsStrip.setPixelColor(i, color);
      GearsStrip.show();
      delay(20);
    }
  } else {
    for(uint16_t i=0; i<GearsStrip.numPixels(); i++) {
      GearsStrip.setPixelColor(i, black);
      GearsStrip.show();
      delay(20);
    }
  }
}


void colorTheaterChase(uint32_t color) {
  GearsStrip.setBrightness(Color_Brightness*2);
  for(int b=0; b<3; b++) {
    GearsStrip.clear();
    for(int c=b; c<GearsStrip.numPixels(); c += 3) {
      GearsStrip.setPixelColor(c, color);
    }
    GearsStrip.show();
    delay(200);
  }
}

void Rainbow(int wait) {
  GearsStrip.setBrightness(Color_Brightness*2);
  for(long firstPixelHue = 0; firstPixelHue < 65536; firstPixelHue += 512) {
    for(int i=0; i<GearsStrip.numPixels(); i++) {
      int pixelHue = firstPixelHue + (i * 65536L / GearsStrip.numPixels());
      GearsStrip.setPixelColor(i, GearsStrip.gamma32(GearsStrip.ColorHSV(pixelHue)));
    }
    GearsStrip.show();
    delay(wait);
  }
}

void colorStrobe(uint32_t color){
  GearsStrip.setBrightness(Color_Brightness/2);
  for(int j = 0; j < 5; j++) {
    GearsStrip.fill(color, 0, GearsStrip.numPixels());
    GearsStrip.show();
    delay(50);
    GearsStrip.clear();
    GearsStrip.show();
    delay(50);
  }
 delay(1000);
}

void colorLevel(uint32_t color, int level){
  GearsStrip.setBrightness(Color_Brightness);
  GearsStrip.clear();
  GearsStrip.fill(color, 0, level);
  GearsStrip.show();
}

void colorMovingSubstrips(uint32_t color_a, uint32_t color_b, int substrip_size){
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
    delay(20);
  }
}


void off() {
  GearsStrip.clear();
  GearsStrip.show();
}

void setup() {
  Serial.begin(9600);
  GearsStrip.begin();
  GearsStrip.show();
  GearsStrip.setBrightness(Color_Brightness);
}

void loop() {
  for (int i=0; i<1000; i++) {
    colorStatic(white);
    delay(1);
  }
  for (int i=0; i<5; i++) {
    colorFade(red);
    delay(1);
  }
  for (int i=0; i<5; i++) {
    colorWipe(yellow);
    delay(1);
  }
  for (int i=0; i<10; i++) {
    colorTheaterChase(pink);
    delay(1);
  }
  for (int i=0; i<5; i++) {
    Rainbow(50);
    delay(1);
  }
  for (int i=0; i<5; i++) {
    colorStrobe(deep_blue);
    delay(1);
  }
  for (int i=0; i<5; i++) {
    colorLevel(light_blue, 10);
    delay(1000);
    colorLevel(light_blue, 50);
    delay(1000);
    colorLevel(light_blue, 100);
    delay(1000);
  }
  colorMovingSubstrips(green, purple, 10);
  off();
  delay(1000);
}
