#include <Arduino_RouterBridge.h>

const int SERVO1_PIN = D9;
const int SERVO2_PIN = D10;

volatile int servo1Pos = 90;
volatile int servo2Pos = 90;

int angleToPulse(int angle) {
  angle = constrain(angle, 0, 180);
  return map(angle, 0, 180, 544, 2400);
}

void set_servos(int pos1, int pos2) {
  servo1Pos = constrain(pos1, 0, 180);
  servo2Pos = constrain(pos2, 0, 180);
}

void setup() {
  pinMode(SERVO1_PIN, OUTPUT);
  pinMode(SERVO2_PIN, OUTPUT);

  digitalWrite(SERVO1_PIN, LOW);
  digitalWrite(SERVO2_PIN, LOW);

  Bridge.begin();
  Bridge.provide_safe("set_servos", set_servos);
}

void loop() {
  int pulse1 = angleToPulse(servo1Pos);
  int pulse2 = angleToPulse(servo2Pos);

  digitalWrite(SERVO1_PIN, HIGH);
  digitalWrite(SERVO2_PIN, HIGH);

  if (pulse1 < pulse2) {
    delayMicroseconds(pulse1);
    digitalWrite(SERVO1_PIN, LOW);
    delayMicroseconds(pulse2 - pulse1);
    digitalWrite(SERVO2_PIN, LOW);
  }
  else {
    delayMicroseconds(pulse2);
    digitalWrite(SERVO2_PIN, LOW);
    delayMicroseconds(pulse1 - pulse2);
    digitalWrite(SERVO1_PIN, LOW);
  }

  delay(18);
}
