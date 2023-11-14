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
Servo tail_left;
Servo tail_right;
Servo tail_up;

int eyebrow_left_pos = 90;
int eyebrow_right_pos = 90;
int ear_pan_left_pos = 90;
int ear_tilt_left_pos = 90;
int ear_pan_right_pos = 90;
int ear_tilt_right_pos = 90;
int mouth_left_pos = 90;
int mouth_right_pos = 90;
int muzzle_pos = 90;
int tail_left_pos = 90;
int tail_right_pos = 90;
int tail_up_pos = 90;

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
  tail_left.attach(21);
  tail_right.attach(22);
  tail_up.attach(23);
}

void writepos() {
  eyebrow_left.write(eyebrow_left_pos);
  eyebrow_right.write(eyebrow_right_pos);
  ear_pan_left.write(ear_pan_left_pos);
  ear_tilt_left.write(ear_tilt_left_pos);
  ear_pan_right.write(ear_pan_right_pos);
  ear_tilt_right.write(ear_tilt_right_pos);
  mouth_left.write(mouth_left_pos);
  mouth_right.write(mouth_right_pos);
  muzzle.write(muzzle_pos);
  tail_left.write(tail_left_pos);
  tail_right.write(tail_right_pos);
  tail_up.write(tail_up_pos);
}