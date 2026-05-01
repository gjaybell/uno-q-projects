from arduino.app_utils import App, Bridge
import time
import urllib.request

URL = "http://192.168.1.242:5000/cmd"

def loop():
    try:
        response = urllib.request.urlopen(URL, timeout=0.5)
        cmd = response.read().decode().strip()

        print("Received:", cmd)

        try:
            speed = int(cmd)

            if abs(speed) < 20:
                speed = 0

            if speed > 255:
                speed = 255
            if speed < -255:
                speed = -255

            Bridge.call("set_motor", speed)

        except:
            Bridge.call("set_motor", 0)

    except Exception as e:
        print("Error:", e)
        Bridge.call("set_motor", 0)

    time.sleep(0.2)

App.run(user_loop=loop)
