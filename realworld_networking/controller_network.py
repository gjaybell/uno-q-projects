import serial
from flask import Flask
import threading
import time

CONTROLLER_PORT = "COM4"
BAUD_RATE = 115200

latest_data = "0,0,0,0,90,90"

app = Flask(__name__)

def read_controller():
    global latest_data

    print("Opening controller on", CONTROLLER_PORT)
    controller = serial.Serial(CONTROLLER_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)

    print("Controller server running.")
    print("Latest controller values available at /cmd")

    while True:
        try:
            line = controller.readline().decode(errors="ignore").strip()

            if not line:
                continue

            parts = line.split(",")

            if len(parts) == 6:
                latest_data = line
                print("Controller:", latest_data)
            else:
                print("Ignored bad line:", line)

        except Exception as e:
            print("Controller error:", e)
            time.sleep(1)

@app.route("/cmd")
def cmd():
    return latest_data

if __name__ == "__main__":
    t = threading.Thread(target=read_controller, daemon=True)
    t.start()

    print("HTTP server starting on port 5000")
    print("Use: http://PC1-IP:5000/cmd")

    app.run(host="0.0.0.0", port=5000)
