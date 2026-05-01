from arduino.app_utils import App, Bridge
import time
import urllib.request

URL = "http://192.168.1.242:5000/cmd"

def loop():
    try:
        response = urllib.request.urlopen(URL, timeout=1)
        cmd = response.read().decode().strip()

        print("Received:", cmd)

        if cmd == "forward":
            Bridge.call("set_motor", 120)
        elif cmd == "reverse":
            Bridge.call("set_motor", -120)
        elif cmd == "stop":
            Bridge.call("set_motor", 0)

    except Exception as e:
        print("Error:", e)

    time.sleep(1)

App.run(user_loop=loop)
