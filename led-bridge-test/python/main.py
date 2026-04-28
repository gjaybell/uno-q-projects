from arduino.app_utils import App, Bridge
import time

led_state = False

def loop():
    global led_state
    led_state = not led_state
    print("Python sending LED state:", led_state)
    Bridge.call("set_led", led_state)
    time.sleep(1)

App.run(user_loop=loop)
