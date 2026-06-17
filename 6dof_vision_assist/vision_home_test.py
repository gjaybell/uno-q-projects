import serial
import time

ARM_PORT = "COM4"
BAUD_RATE = 115200

MECHANICAL_HOME = [75, 85, 42, 125, 90, 97]

VISION_HOME = [80, 113, 0, 118, 118, 70]# 70,110,0,124,118,70


def send_position(arm, pos):
    command = ",".join(str(v) for v in pos)
    arm.write((command + "\n").encode())
    print("Sent:", command)


print("Connecting to arm...")

arm = serial.Serial(ARM_PORT, BAUD_RATE, timeout=1)

time.sleep(5)

print()
print("Moving to Mechanical Home...")
send_position(arm, MECHANICAL_HOME)

time.sleep(3)

print()
print("Moving to Vision Home...")
send_position(arm, VISION_HOME)

print()
print("Vision Home reached.")

arm.close()
