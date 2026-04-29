#include <Arduino_RouterBridge.h>

void set_led(bool state) {
  digitalWrite(LED_BUILTIN, state ? LOW : HIGH);
}

void setup() {
  pinMode(LED_BUILTIN, OUTPUT);
  digitalWrite(LED_BUILTIN, HIGH);

  Bridge.begin();
  Bridge.provide_safe("set_led", set_led);
}

void loop() {}
