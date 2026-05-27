#include <Arduino_RouterBridge.h>
#include <Wire.h>
#include <U8g2lib.h>

const int NUM_SERVOS = 6;
const int MOVE_DELAY = 20;

const int servoPins[NUM_SERVOS] = {
  A0,  // 0 Base
  A1,  // 1 Joint 2
  A2,  // 2 Joint 3
  A3,  // 3 Joint 4
  A4,  // 4 Joint 5
  A5   // 5 Claw
};

int servoPos[NUM_SERVOS] = {
  75, 85, 60, 125, 90, 97
};

int targetPos[NUM_SERVOS] = {
  75, 85, 60, 125, 90, 97
};

const int SAFE_LOW  = 0;
const int SAFE_HIGH = 180;

// 2.42 inch I2C OLED - try SSD1309 first
U8G2_SSD1309_128X64_NONAME0_F_HW_I2C display(U8G2_R0, U8X8_PIN_NONE);

// If blank, comment the line above and use this instead:
// U8G2_SSD1306_128X64_NONAME_F_HW_I2C display(U8G2_R0, U8X8_PIN_NONE);

void writeServoPulse(int pin, int angle) {
  angle = constrain(angle, 0, 180);
  int pulse = map(angle, 0, 180, 544, 2400);

  digitalWrite(pin, HIGH);
  delayMicroseconds(pulse);
  digitalWrite(pin, LOW);
}

void refreshServos() {
  for (int i = 0; i < NUM_SERVOS; i++) {
    writeServoPulse(servoPins[i], servoPos[i]);
  }
  delay(15);
}

void centerAllServos() {
  for (int t = 0; t < 150; t++) {
    refreshServos();
  }
}

void updateServoPositions() {
  for (int i = 0; i < NUM_SERVOS; i++) {
    if (servoPos[i] < targetPos[i]) {
      servoPos[i]++;
    } else if (servoPos[i] > targetPos[i]) {
      servoPos[i]--;
    }
  }
}

void updateDisplay() {

  display.clearBuffer();

  display.setFont(u8g2_font_6x10_tf);

  display.setCursor(0, 10);
  display.print("Servo:0 Base A0: ");
  display.print(servoPos[0]);

  display.setCursor(0, 20);
  display.print("Servo:1 J2   A1: ");
  display.print(servoPos[1]);

  display.setCursor(0, 30);
  display.print("Servo:2 J3   A2: ");
  display.print(servoPos[2]);

  display.setCursor(0, 40);
  display.print("Servo:3 J4   A3: ");
  display.print(servoPos[3]);

  display.setCursor(0, 50);
  display.print("Servo:4 J5   A4: ");
  display.print(servoPos[4]);

  display.setCursor(0, 60);
  display.print("Servo:5 Claw A5: ");
  display.print(servoPos[5]);

  display.sendBuffer();
}

void printHelp() {
  Serial.println();
  Serial.println("6DOF Six-Value Serial Control");
  Serial.println("Command format: s0,s1,s2,s3,s4,s5");
  Serial.println("Example:");
  Serial.println("75,85,60,125,90,97");
  Serial.println();
}

void handleSerialCommand() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    data.trim();

    int values[NUM_SERVOS];
    int index = 0;

    char buffer[80];
    data.toCharArray(buffer, sizeof(buffer));

    char *token = strtok(buffer, ",");

    while (token != NULL && index < NUM_SERVOS) {
      values[index] = atoi(token);
      token = strtok(NULL, ",");
      index++;
    }

    if (index == NUM_SERVOS) {
      for (int i = 0; i < NUM_SERVOS; i++) {
        targetPos[i] = constrain(values[i], SAFE_LOW, SAFE_HIGH);
      }

      Serial.print("Targets: ");
      for (int i = 0; i < NUM_SERVOS; i++) {
        Serial.print(targetPos[i]);
        if (i < NUM_SERVOS - 1) Serial.print(",");
      }
      Serial.println();
    }
  }
}

void setup() {
  Bridge.begin();
  Serial.begin(115200);

  for (int i = 0; i < NUM_SERVOS; i++) {
    pinMode(servoPins[i], OUTPUT);
    digitalWrite(servoPins[i], LOW);
  }

  Wire.begin();
  display.begin();

  updateDisplay();
  printHelp();
  centerAllServos();
}

void loop() {
  handleSerialCommand();
  updateServoPositions();
  refreshServos();

  static unsigned long lastDisplay = 0;
  if (millis() - lastDisplay > 150) {
    updateDisplay();
    lastDisplay = millis();
  }
}
