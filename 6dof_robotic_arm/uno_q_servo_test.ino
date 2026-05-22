#include <Arduino_RouterBridge.h>

const int NUM_SERVOS = 6;

const int servoPins[NUM_SERVOS] = {
  D9,   // Servo 0 Base
  D10,  // Servo 1
  D5,   // Servo 2
  D6,   // Servo 3
  D3,   // Servo 4
  D4    // Servo 5 Claw
};

int servoPos[NUM_SERVOS] = {
  90, 100, 80, 100, 100, 100
};

unsigned long lastRefresh = 0;

int angleToPulse(int angle) {
  angle = constrain(angle, 0, 180);
  return map(angle, 0, 180, 544, 2400);
}

void pulseServo(int pin, int angle) {
  int pulse = angleToPulse(angle);

  digitalWrite(pin, HIGH);
  delayMicroseconds(pulse);
  digitalWrite(pin, LOW);
}

void setup() {
  Serial.begin(115200);

  for (int i = 0; i < NUM_SERVOS; i++) {
    pinMode(servoPins[i], OUTPUT);
    digitalWrite(servoPins[i], LOW);
  }

  Serial.println("=================================");
  Serial.println("UNO Q Servo Range Tester");
  Serial.println("Enter: servo,angle");
  Serial.println("Example: 1,100");
  Serial.println("=================================");
}

void loop() {

  // ---- Servo refresh ----
  for (int i = 0; i < NUM_SERVOS; i++) {
    pulseServo(servoPins[i], servoPos[i]);
  }

  delay(20);

  // ---- Serial commands ----
  if (Serial.available()) {

    String cmd = Serial.readStringUntil('\n');
    cmd.trim();

    int commaIndex = cmd.indexOf(',');

    if (commaIndex > 0) {

      int servoNum = cmd.substring(0, commaIndex).toInt();
      int angle = cmd.substring(commaIndex + 1).toInt();

      if (servoNum >= 0 && servoNum < NUM_SERVOS) {

        angle = constrain(angle, 0, 180);

        servoPos[servoNum] = angle;

        Serial.print("Servo ");
        Serial.print(servoNum);
        Serial.print(" -> ");
        Serial.println(angle);

      } else {

        Serial.println("Invalid servo number");
      }

    } else {

      Serial.println("Format: servo,angle");
    }
  }
}
