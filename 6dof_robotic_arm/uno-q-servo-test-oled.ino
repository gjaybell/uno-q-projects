// Upload this into the Arduino UNO-Q 
#include <Arduino_RouterBridge.h>
#include <Wire.h>
#include <U8g2lib.h>

const int NUM_SERVOS = 6;
const int MOVE_DELAY = 20;

const int servoPins[NUM_SERVOS] = {
  A0,  // 0 Base
  A1,  // 1 Joint 2
  A2,  // 2 Joint 32,
  A3,  // 3 Joint 4
  A4,  // 4 Joint 5
  A5   // 5 Claw3,100
  
};

int servoPos[NUM_SERVOS] = {
  90, 90, 90, 90, 90, 90
};

const int SAFE_LOW  = 0;
const int SAFE_HIGH = 180;

U8G2_SSD1306_128X64_NONAME_F_HW_I2C display(U8G2_R0, U8X8_PIN_NONE);

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
  for (int t = 0; t < 150; t++) {   // about 3 seconds
    for (int i = 0; i < NUM_SERVOS; i++) {
      writeServoPulse(servoPins[i], servoPos[i]);
    }
    delay(15);
  }
}

void updateDisplay() {
  display.clearBuffer();
  display.setFont(u8g2_font_6x10_tf);

  display.setCursor(0, 10);
  display.print("6DOF Serial Control");

  display.setCursor(0, 22);
  display.print("0 Base A0: ");
  display.print(servoPos[0]);

  display.setCursor(0, 32);
  display.print("1 J2   A1: ");
  display.print(servoPos[1]);

  display.setCursor(0, 42);
  display.print("2 J3   A2: ");
  display.print(servoPos[2]);

  display.setCursor(0, 52);
  display.print("3 J4   A3: ");
  display.print(servoPos[3]);

  display.setCursor(0, 62);
  display.print("4 J5:");
  display.print(servoPos[4]);
  display.print(" 5 Claw:");
  display.print(servoPos[5]);

  display.sendBuffer();
}

void printHelp() {
  Serial.println();
  Serial.println("6DOF Arm Serial Control");
  Serial.println("Command format: servo,angle");
  Serial.println("Examples:");
  Serial.println("0,92  = move Base to 92");
  Serial.println("1,88  = move Joint 2 to 88");
  Serial.println("5,95  = move Claw to 95");
  Serial.println();
  Serial.println("Servo numbers:");
  Serial.println("0 = Base  A0");
  Serial.println("1 = J2    A1");
  Serial.println("2 = J3    A2");
  Serial.println("3 = J4    A3");
  Serial.println("4 = J5    A4");
  Serial.println("5 = Claw  A5");
  Serial.println();
  Serial.print("Safe range: ");
  Serial.print(SAFE_LOW);
  Serial.print(" to ");
  Serial.println(SAFE_HIGH);
  Serial.println();
}

void handleSerialCommand() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    data.trim();

    int comma = data.indexOf(',');

    if (comma > 0) {
      int servoNumber = data.substring(0, comma).toInt();
      int angle = data.substring(comma + 1).toInt();

   if (servoNumber >= 0 && servoNumber < NUM_SERVOS) {

  angle = constrain(angle, SAFE_LOW, SAFE_HIGH);

  // Move gradually upward
  while (servoPos[servoNumber] < angle) {
    servoPos[servoNumber]++;

    refreshServos();
    updateDisplay();

    delay(MOVE_DELAY);
  }

  // Move gradually downward
  while (servoPos[servoNumber] > angle) {
    servoPos[servoNumber]--;

    refreshServos();
    updateDisplay();

    delay(MOVE_DELAY);
  }

  Serial.print("Servo ");
  Serial.print(servoNumber);
  Serial.print(" moved to ");
  Serial.println(angle);
}
    else {
        Serial.println("Invalid servo number. Use 0-5.");
      }
    } else {
      Serial.println("Invalid command. Use servo,angle");
      Serial.println("Example: 0,92");
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
  refreshServos();
}
