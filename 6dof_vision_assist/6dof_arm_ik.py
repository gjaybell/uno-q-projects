import serial
import time

# ============================================================
# 6DOF ARM IK / JOG TEST LAB BRIDGE
# Controller -> PC Python -> UNO Q Arm
# ============================================================

CONTROLLER_PORT = "COM8"
ARM_PORT = "COM4"
BAUD_RATE = 115200

# Servo order sent to arm:
# 0 = Base
# 1 = Shoulder / S1
# 2 = Elbow    / S2
# 3 = Wrist 1  / S3
# 4 = Wrist 2  / S4
# 5 = Claw

HOME_POS = [75, 85, 42, 125, 90, 97]

SAFE_LOW  = [5, 45, 5, 90, 5, 80]
SAFE_HIGH = [165, 125, 80, 155, 175, 120]

# ============================================================
# CHANGE THESE SETTINGS TO PLAY WITH TESTS
# ============================================================

# Number of arm servos to actively test: 1, 2, 3, or 4
# This does NOT include claw.
TEST_SERVO_COUNT = 2

# Joystick input order from controller:
# raw[0] = JS1
# raw[1] = JS2
# raw[2] = JS3
# raw[3] = JS4
# raw[4] = PS0 base pot
# raw[5] = PS5 claw pot

# Modes:
# "JOG"    = joystick nudges servo slowly
# "DIRECT" = joystick position maps directly to servo position
#
# For early IK testing, use JOG first.
# It is safer and easier to understand.

CONTROL_RULES = [
    # servo, input, mode, speed
    {"servo": 0, "input": 0, "mode": "DIRECT", "speed": 0.7},  # JS1 controls Base
    {"servo": 1, "input": 1, "mode": "DIRECT", "speed": 0.5},  # JS2 controls S1
    {"servo": 2, "input": 2, "mode": "JOG", "speed": 0.5},  # JS3 controls S2
    {"servo": 3, "input": 3, "mode": "JOG", "speed": 0.5},  # JS4 controls S3
]

# Claw can stay controlled by PS5 pot
ENABLE_CLAW = True

DEADZONE = 8
LOOP_DELAY = 0.03
MIN_SEND_CHANGE = 1

last_sent = None


# ============================================================
# BASIC FUNCTIONS
# ============================================================

def clamp(value, low, high):
    return max(low, min(high, value))


def map_range(x, in_min, in_max, out_min, out_max):
    if in_max == in_min:
        return out_min
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min


def apply_deadzone(value):
    if abs(value) < DEADZONE:
        return 0
    return value


def send_to_arm(arm, values):
    global last_sent

    values = [int(round(v)) for v in values]

    if last_sent is not None:
        diffs = [abs(values[i] - last_sent[i]) for i in range(6)]
        if max(diffs) < MIN_SEND_CHANGE:
            return

    command = ",".join(str(v) for v in values)
    arm.write((command + "\n").encode())

    print("SENT:", command)
    last_sent = values.copy()


def joystick_direct_to_servo(js_value, servo):
    """
    Converts joystick value to servo position.
    Assumes joystick value is about:
    left/down  = -90
    center     = 0
    right/up   = +89
    """

    low = SAFE_LOW[servo]
    high = SAFE_HIGH[servo]
    center = HOME_POS[servo]

    if js_value < 0:
        return map_range(js_value, -90, 0, low, center)
    else:
        return map_range(js_value, 0, 89, center, high)


def update_servo_from_rule(values, raw, rule):
    servo = rule["servo"]
    input_index = rule["input"]
    mode = rule["mode"]
    speed = rule["speed"]

    js = apply_deadzone(raw[input_index])

    if mode == "JOG":
        values[servo] += js * speed * 0.03

    elif mode == "DIRECT":
        values[servo] = joystick_direct_to_servo(js, servo)

    values[servo] = clamp(values[servo], SAFE_LOW[servo], SAFE_HIGH[servo])


def map_claw(ps5):
    # Your known claw range
    # PS5 roughly 0 to 179
    return map_range(ps5, 0, 179, SAFE_LOW[5], SAFE_HIGH[5])


# ============================================================
# MAIN PROGRAM
# ============================================================

def main():
    print("Starting 6DOF IK / JOG Test Lab Bridge")
    print("Controller:", CONTROLLER_PORT)
    print("Arm:", ARM_PORT)
    print("Active test servo count:", TEST_SERVO_COUNT)
    print("Press Ctrl+C to stop.")

    controller = serial.Serial(CONTROLLER_PORT, BAUD_RATE, timeout=1)
    arm = serial.Serial(ARM_PORT, BAUD_RATE, timeout=1)

    time.sleep(3)

    controller.reset_input_buffer()
    arm.reset_input_buffer()

    values = HOME_POS.copy()

    print("Sending HOME...")
    send_to_arm(arm, values)
    time.sleep(0.5)

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

            # Start each loop from current values, not HOME.
            # This allows joystick JOG movement.
            active_rules = CONTROL_RULES[:TEST_SERVO_COUNT]

            for rule in active_rules:
                update_servo_from_rule(values, raw, rule)

            # Any servos outside the test count stay home.
            active_servos = [rule["servo"] for rule in active_rules]

            for s in [0, 1, 2, 3]:
                if s not in active_servos:
                    values[s] = HOME_POS[s]

            # Servo 4 wrist stays home for now unless you add it later
            values[4] = HOME_POS[4]

            # Claw
            if ENABLE_CLAW:
                values[5] = clamp(map_claw(raw[5]), SAFE_LOW[5], SAFE_HIGH[5])
            else:
                values[5] = HOME_POS[5]

            print(
                f"RAW JS1={raw[0]} JS2={raw[1]} JS3={raw[2]} JS4={raw[3]} "
                f"PS0={raw[4]} PS5={raw[5]} | "
                f"VALUES={ [int(v) for v in values] }"
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
