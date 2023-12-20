#include <Servo.h>

Servo eyebrow_left;
Servo eyebrow_right;
Servo ear_pan_left;
Servo ear_tilt_left;
Servo ear_pan_right;
Servo ear_tilt_right;
Servo mouth_left;
Servo mouth_right;
Servo muzzle;

int servo_calibration_matrix[6][9] = {
  {90, 90, 90, 90, 90, 90, 90, 90, 90}, // angry
  {90, 90, 90, 90, 90, 90, 90, 90, 90}, // disgusted
  {90, 90, 90, 90, 90, 90, 90, 90, 90}, // happy
  {90, 90, 90, 90, 90, 90, 90, 90, 90}, // neutral
  {90, 90, 90, 90, 90, 90, 90, 90, 90}, // sad
  {90, 90, 90, 90, 90, 90, 90, 90, 90}  // surprised
};

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
  eyebrow_left.attach(4);
  eyebrow_right.attach(5);
  ear_pan_left.attach(6);
  ear_tilt_left.attach(7);
  ear_pan_right.attach(8);
  ear_tilt_right.attach(9);
  mouth_left.attach(10);
  mouth_right.attach(11);
  muzzle.attach(12);
}

void writepos(int eyebrow_left_pos, int eyebrow_right_pos, int ear_pan_left_pos, int ear_tilt_left_pos,
              int ear_pan_right_pos, int ear_tilt_right_pos, int mouth_left_pos, int mouth_right_pos, int muzzle_pos) {
  eyebrow_left.write(eyebrow_left_pos);
  eyebrow_right.write(eyebrow_right_pos);
  ear_pan_left.write(ear_pan_left_pos);
  ear_tilt_left.write(ear_tilt_left_pos);
  ear_pan_right.write(ear_pan_right_pos);
  ear_tilt_right.write(ear_tilt_right_pos);
  mouth_left.write(mouth_left_pos);
  mouth_right.write(mouth_right_pos);
  muzzle.write(muzzle_pos);
}