from arduino.app_utils import App, Bridge
import time

def loop():
    print("Forward slow")
    Bridge.call("set_motor", 80)
    time.sleep(3)

    print("Forward faster")
    Bridge.call("set_motor", 150)
    time.sleep(3)

    print("Stop")
    Bridge.call("set_motor", 0)
    time.sleep(2)

    print("Reverse")
    Bridge.call("set_motor", -120)
    time.sleep(3)

    print("Stop")
    Bridge.call("set_motor", 0)
    time.sleep(2)

App.run(user_loop=loop)

