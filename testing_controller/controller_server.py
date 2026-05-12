# controller_server.py
import serial
from flask import Flask
import threading

app = Flask(__name__)

controller = serial.Serial("COM8", 115200, timeout=1)

x_val = 0
y_val = 0

def read_controller():
    global x_val, y_val

    while True:
        try:
            line = controller.readline().decode().strip()

            if line:
                s1, s2, s3, s4, h1, c1 = map(int, line.split(","))

                x_val = s1
                y_val = s2

        except Exception as e:
            print("Controller error:", e)

@app.route("/cmd")
def cmd():
    return f"{x_val},{y_val}"

threading.Thread(target=read_controller, daemon=True).start()

app.run(host="0.0.0.0", port=5000)
