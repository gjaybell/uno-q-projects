#include <Arduino_RouterBridge.h>

const int IN1 = D3;
const int IN2 = D4;

void stop_motor() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}

void set_motor(int speed) {
  // Limit speed
  if (speed > 255) speed = 255;
  if (speed < -255) speed = -255;

  if (speed > 0) {
    analogWrite(IN1, speed);   // forward
    digitalWrite(IN2, LOW);
  }
  else if (speed < 0) {
    digitalWrite(IN1, LOW);
    analogWrite(IN2, -speed);  // reverse
  }
  else {
    stop_motor();
  }
}

void setup() {
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  stop_motor();

  Bridge.begin();
  Bridge.provide_safe("set_motor", set_motor);
}

void loop() {
}
