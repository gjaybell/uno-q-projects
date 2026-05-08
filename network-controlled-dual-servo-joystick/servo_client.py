import time
import urllib.request
import serial

CMD_URL = "http://192.168.1.242:5000/cmd"

ser = serial.Serial("COM4", 115200, timeout=1)
time.sleep(2)

last_sent1 = None
last_sent2 = None

smooth_servo1 = 90
smooth_servo2 = 90

while True:
    try:
        response = urllib.request.urlopen(CMD_URL, timeout=0.5)
        data = response.read().decode().strip()

        x, y = data.split(",")
        x = int(x)
        y = int(y)

        # dead zone
        if abs(x) < 2:
            x = 0
        if abs(y) < 2:
            y = 0

        target_servo1 = max(0, min(180, 90 + x))
        target_servo2 = max(0, min(180, 90 + y))

        # smoothing
        smooth_servo1 = int((smooth_servo1 * 0.5) + (target_servo1 * 0.5))
        smooth_servo2 = int((smooth_servo2 * 0.5) + (target_servo2 * 0.5))

        if (
            last_sent1 is None
            or abs(smooth_servo1 - last_sent1) >= 2
            or abs(smooth_servo2 - last_sent2) >= 2
        ):
            command = f"{smooth_servo1},{smooth_servo2}\n"
            ser.write(command.encode())

            last_sent1 = smooth_servo1
            last_sent2 = smooth_servo2

    except Exception as e:
        print("Error:", e)

    time.sleep(0.02)
