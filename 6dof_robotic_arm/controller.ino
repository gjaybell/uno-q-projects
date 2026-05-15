#include <Wire.h>
#include <U8g2lib.h>

const int J1_X_PIN = A0;
const int J1_Y_PIN = A1;
const int J2_X_PIN = A2;
const int J2_Y_PIN = A3;

const int BASE_SLIDER_PIN = A6;
const int CLAW_SLIDER_PIN = A7;

const int DEADZONE = 35;

// OLED
U8G2_SSD1306_128X64_NONAME_F_HW_I2C display(U8G2_R0, U8X8_PIN_NONE);

int applyDeadzone(int value) {
  if (abs(value) < DEADZONE) {
    return 0;
  }
  return value;
}

int readJoystickAxis(int pin) {
  int raw = analogRead(pin);          // 0 to 1023
  int centered = raw - 512;           // about -512 to +511
  int mappedVal = map(centered, -512, 511, -90, 90);

  return applyDeadzone(mappedVal);
}

int readSliderServo(int pin) {
  int raw = analogRead(pin);          // 0 to 1023
  return map(raw, 0, 1023, 0, 180);
}

void updateOLED(int h1, int c1, int s1, int s2, int s3, int s4) {
  display.clearBuffer();
  display.setFont(u8g2_font_6x12_tf);

  display.setCursor(0, 10);
  display.print("H1:");
  display.print(h1);
  display.setCursor(64, 10);
  display.print("C1:");
  display.print(c1);

  display.setCursor(0, 24);
  display.print("S1:");
  display.print(s1);
  display.setCursor(64, 24);
  display.print("S2:");
  display.print(s2);

  display.setCursor(0, 38);
  display.print("S3:");
  display.print(s3);
  display.setCursor(64, 38);
  display.print("S4:");
  display.print(s4);

  display.sendBuffer();
}

void setup() {
  Serial.begin(115200);

  Wire.begin();
  display.begin();

  display.clearBuffer();
  display.setFont(u8g2_font_10x20_tf);
  display.setCursor(0, 25);
  display.print("READY");
  display.sendBuffer();

  delay(1000);
}

void loop() {
  int s1 = readJoystickAxis(J1_X_PIN);
  int s2 = readJoystickAxis(J1_Y_PIN);
  int s3 = readJoystickAxis(J2_X_PIN);
  int s4 = readJoystickAxis(J2_Y_PIN);

  int h1 = readSliderServo(BASE_SLIDER_PIN);
  int c1 = readSliderServo(CLAW_SLIDER_PIN);

  Serial.print(s1);
  Serial.print(",");
  Serial.print(s2);
  Serial.print(",");
  Serial.print(s3);
  Serial.print(",");
  Serial.print(s4);
  Serial.print(",");
  Serial.print(h1);
  Serial.print(",");
  Serial.println(c1);

  updateOLED(h1, c1, s1, s2, s3, s4);

  delay(20);
}
