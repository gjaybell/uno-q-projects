from arduino.app_utils import App, Bridge
import time
import urllib.request

URL = "http://192.168.1.242:5000/cmd"

def loop():
    try:
        response = urllib.request.urlopen(URL, timeout=0.5)
        data = response.read().decode().strip()

        print("Received:", data)

        try:
            s1, s2 = data.split(",")

            s1 = int(s1)
            s2 = int(s2)

            # Clamp values
            s1 = max(0, min(180, s1))
            s2 = max(0, min(180, s2))

            Bridge.call("set_servos", s1, s2)

        except:
            pass

    except Exception as e:
        print("Error:", e)

    time.sleep(0.2)

App.run(user_loop=loop)


