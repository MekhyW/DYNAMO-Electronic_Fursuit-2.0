#include <Servo.h>
#define NUM_SERVOS 8
#define NUM_EMOTIONS 6
#define DETACH_THRESHOLD 1000
#define POSITION_CHANGE_TOLERANCE 10

Servo eyebrow_left;
Servo eyebrow_right;
Servo ear_pan_left;
Servo ear_tilt_left;
Servo ear_pan_right;
Servo ear_tilt_right;
Servo mouth_left;
Servo mouth_right;
Servo servos[] = {eyebrow_left,eyebrow_right,ear_pan_left,ear_tilt_left,ear_pan_right,ear_tilt_right,mouth_left,mouth_right};

int servo_calibration_matrix[NUM_EMOTIONS][NUM_SERVOS] = {
  {90, 90, 90, 90, 90, 90, 90, 90}, // angry
  {90, 90, 90, 90, 90, 90, 90, 90}, // disgusted
  {90, 90, 90, 90, 90, 90, 90, 90}, // happy
  {90, 90, 90, 90, 90, 90, 90, 90}, // neutral
  {90, 90, 90, 90, 90, 90, 90, 90}, // sad
  {90, 90, 90, 90, 90, 90, 90, 90}  // surprised
};
int previousServoPositions[NUM_SERVOS] = {90, 90, 90, 90, 90, 90, 90, 90};
unsigned long lastChangeTime[NUM_SERVOS];

struct ServosTaskInput
{
  int animatronics_on;
  int emotion_angry;
  int emotion_disgusted;
  int emotion_happy;
  int emotion_neutral;
  int emotion_sad;
  int emotion_surprised;
};

void setupServos() {
  for (int i = 0; i < NUM_SERVOS; i++) {
    servos[i].attach(i + 4);
  }
}

void detachIfNoChange(int servoIndex, int newPos) {
  if (abs(newPos - previousServoPositions[servoIndex]) > POSITION_CHANGE_TOLERANCE) {
    servos[servoIndex].attach(servoIndex + 4);
    lastChangeTime[servoIndex] = millis();
  } else {
    if (millis() - lastChangeTime[servoIndex] > DETACH_THRESHOLD) {
      servos[servoIndex].detach();
    }
  }
}

void writepos(int eyebrow_left_pos, int eyebrow_right_pos, int ear_pan_left_pos, int ear_tilt_left_pos,
              int ear_pan_right_pos, int ear_tilt_right_pos, int mouth_left_pos, int mouth_right_pos) {
  int newServoPositions[NUM_SERVOS] = {
    eyebrow_left_pos, eyebrow_right_pos, ear_pan_left_pos, ear_tilt_left_pos,
    ear_pan_right_pos, ear_tilt_right_pos, mouth_left_pos, mouth_right_pos
  };
  for (int i = 0; i < NUM_SERVOS; i++) {
    detachIfNoChange(i, newServoPositions[i]);
    servos[i].write(newServoPositions[i]);
    previousServoPositions[i] = newServoPositions[i];
  }
}
