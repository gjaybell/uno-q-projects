import serial
import time
import math

CONTROLLER_PORT = "COM8"
ARM_PORT = "COM4"
BAUD_RATE = 115200

# Servo order:
# 0 = Base
# 1 = Shoulder / S1
# 2 = Elbow    / S2
# 3 = Wrist 1  / S3
# 4 = Wrist 2  / S4
# 5 = Claw

HOME_POS = [75, 90, 100, 130, 108, 97]

SAFE_LOW  = [5, 45, 5, 90, 5, 80]
SAFE_HIGH = [165, 125, 80, 200, 175, 120]

# ------------------------------------------------------------
# IK SETTINGS
# ------------------------------------------------------------

L1 = 100.0
L2 = 100.0

target_x = 120.0
target_y = 80.0

TARGET_Y_SPEED = 1.5
BASE_SPEED = 0.7

DEADZONE = 8
LOOP_DELAY = 0.05

WRIST_COMPENSATION = 1.2 # was 0.6

last_sent = None


def clamp(value, low, high):
    return max(low, min(high, value))


def apply_deadzone(value):
    if abs(value) < DEADZONE:
        return 0
    return value


def send_to_arm(arm, values):
    global last_sent

    values = [int(round(v)) for v in values]

    if values == last_sent:
        return

    command = ",".join(str(v) for v in values)
    arm.write((command + "\n").encode())

    print("SENT:", command)
    last_sent = values.copy()


def ik_2link(x, y):
    distance = math.sqrt(x*x + y*y)

    max_reach = L1 + L2 - 1
    min_reach = abs(L1 - L2) + 1

    distance = clamp(distance, min_reach, max_reach)

    cos_elbow = (distance*distance - L1*L1 - L2*L2) / (2 * L1 * L2)
    cos_elbow = clamp(cos_elbow, -1, 1)

    elbow_rad = math.acos(cos_elbow)

    k1 = L1 + L2 * math.cos(elbow_rad)
    k2 = L2 * math.sin(elbow_rad)

    shoulder_rad = math.atan2(y, x) - math.atan2(k2, k1)

    shoulder_deg = math.degrees(shoulder_rad)
    elbow_deg = math.degrees(elbow_rad)

    return shoulder_deg, elbow_deg


def ik_angles_to_servos(shoulder_deg, elbow_deg):
    # First-test mapping.
    # Reverse signs here if motion direction is wrong.

    s1 = 85 + shoulder_deg
    s2 = 42 + (elbow_deg - 90)

    s1 = clamp(s1, SAFE_LOW[1], SAFE_HIGH[1])
    s2 = clamp(s2, SAFE_LOW[2], SAFE_HIGH[2])

    return s1, s2


def main():
    global target_y

    print("Starting 3-Servo IK Test")
    print("JS1 left/right controls Servo 0 base.")
    print("JS1 up/down controls IK target Y for Servo 1 and Servo 2.")
    print("Press Ctrl+C to stop.")

    controller = serial.Serial(CONTROLLER_PORT, BAUD_RATE, timeout=1)
    arm = serial.Serial(ARM_PORT, BAUD_RATE, timeout=1)

    time.sleep(3)

    controller.reset_input_buffer()
    arm.reset_input_buffer()

    values = HOME_POS.copy()

    print("Sending HOME...")
    send_to_arm(arm, values)
    time.sleep(1)

    while True:
        try:
            line = controller.readline().decode(errors="ignore").strip()

            if not line:
                continue

            parts = line.split(",")

            if len(parts) != 6:
                print("Ignored bad line:", line)
                continue

            raw = [int(p) for p in parts]

            # Same joystick:
            # raw[0] = left/right axis
            # raw[1] = up/down axis
            js_base = apply_deadzone(raw[0])
            js_y = apply_deadzone(raw[1])
            js_wrist = apply_deadzone(raw[2])
            js_claw  = apply_deadzone(raw[3])

            # ------------------------------------------------
            # Servo 0 base control from joystick left/right
            # ------------------------------------------------
            values[0] += js_base * BASE_SPEED * 0.03
            values[0] = clamp(values[0], SAFE_LOW[0], SAFE_HIGH[0])

            # ------------------------------------------------
            # IK target Y from joystick up/down
            # ------------------------------------------------
            target_y += js_y * TARGET_Y_SPEED * 0.03
            target_y = clamp(target_y, 20, 180)

            shoulder_deg, elbow_deg = ik_2link(target_x, target_y)
            s1, s2 = ik_angles_to_servos(shoulder_deg, elbow_deg)

            values[1] = s1
            values[2] = s2
            

            # Keep remaining servos fixed for now
            #values[3] = HOME_POS[3]
            # Servo 3 follows IK up/down motion as wrist compensation
            values[3] = HOME_POS[3] - ((values[1] - HOME_POS[1]) * WRIST_COMPENSATION)
            values[3] = clamp(values[3], SAFE_LOW[3], SAFE_HIGH[3])

            # ----------------------------------------
            # Servo 4 Wrist Rotate
            # ----------------------------------------
            values[4] += js_wrist * 0.7 * 0.03
            values[4] = clamp(values[4], SAFE_LOW[4], SAFE_HIGH[4])

            # ----------------------------------------
            # Servo 5 Claw
            # ----------------------------------------
            values[5] += js_claw * 0.7 * 0.03
            values[5] = clamp(values[5], SAFE_LOW[5], SAFE_HIGH[5])

            #values[4] = HOME_POS[4]
            #values[5] = HOME_POS[5]

            print(
                f"RAW base={raw[0]} y={raw[1]} | "
                f"Base S0={values[0]:.0f} | "
                f"Target X={target_x:.1f} Y={target_y:.1f} | "
                f"IK shoulder={shoulder_deg:.1f} elbow={elbow_deg:.1f} | "
                f"S1={values[1]:.0f} S2={values[2]:.0f}"
            )

            send_to_arm(arm, values)

            time.sleep(LOOP_DELAY)

        except KeyboardInterrupt:
            print("\nStopping. Returning to HOME.")
            send_to_arm(arm, HOME_POS)
            time.sleep(1)
            break

        except Exception as e:
            print("Error:", e)
            time.sleep(0.2)


if __name__ == "__main__":
    main()
