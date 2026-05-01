#include <Arduino_RouterBridge.h>

const int IN1 = D3;
const int IN2 = D5;

void set_motor(int speed) {
  if (speed > 255) speed = 255;
  if (speed < -255) speed = -255;

  // Ensure clean direction changes
  analogWrite(IN1, 0);
  analogWrite(IN2, 0);
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  delay(150);

  if (speed > 0) {
    analogWrite(IN1, speed);
    digitalWrite(IN2, LOW);
  }
  else if (speed < 0) {
    digitalWrite(IN1, LOW);
    analogWrite(IN2, -speed);
  }
  else {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
  }
}

void setup() {
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);

  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);

  Bridge.begin();
  Bridge.provide_safe("set_motor", set_motor);
}

void loop() {}
