# No JOG
import serial
import time

CONTROLLER_PORT = "COM8"
ARM_PORT = "COM4"
BAUD_RATE = 115200

# Final arm output safety limits based on your calibration chart
SAFE_LOW  = [0, 40, 0, 70, 0, 70]
SAFE_HIGH = [170, 130, 85, 180, 180, 120]

HOME_POS = [75, 85, 42, 125, 90, 97]

last_sent = None


def clamp(value, low, high):
    return max(low, min(high, value))


def map_range(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)


def map_piecewise(x, in_a, out_a, in_b, out_b, in_c, out_c):
    if x <= in_b:
        return map_range(x, in_a, in_b, out_a, out_b)
    else:
        return map_range(x, in_b, in_c, out_b, out_c)


def clamp_positions(values):
    return [
        clamp(values[i], SAFE_LOW[i], SAFE_HIGH[i])
        for i in range(6)
    ]


def send_to_arm(arm, values):
    global last_sent

    values = clamp_positions(values)

    if values == last_sent:
        return

    command = ",".join(str(v) for v in values)
    arm.write((command + "\n").encode())

    print("Sent to arm:", command)
    last_sent = values.copy()


def main():
    print("Starting 6DOF PC Bridge...")
    print("Controller:", CONTROLLER_PORT)
    print("Arm:", ARM_PORT)

    controller = serial.Serial(CONTROLLER_PORT, BAUD_RATE, timeout=1)
    arm = serial.Serial(ARM_PORT, BAUD_RATE, timeout=1)

    time.sleep(2)

    print("Sending HOME position...")
    send_to_arm(arm, HOME_POS)

    print("Bridge running.")
    print("Move controller slowly.")
    print("Press Ctrl+C to stop.")

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

            # Controller raw order:
            # raw[0] = JS1
            # raw[1] = JS2
            # raw[2] = JS3
            # raw[3] = JS4
            # raw[4] = PS0 Base
            # raw[5] = PS5 Claw

            values = [
                map_piecewise(raw[4], 0, 170, 91, 75, 178, 0),       # Servo 0 Base
                map_piecewise(raw[0], -90, 130, 0, 85, 89, 40),      # Servo 1
                map_piecewise(raw[1], -90, 0, 0, 42, 89, 85),        # Servo 2
                map_piecewise(raw[2], -90, 70, 0, 125, 89, 180),     # Servo 3
                map_piecewise(raw[3], -90, 180, 0, 90, 89, 0),       # Servo 4
                map_piecewise(raw[5], 0, 70, 96, 97, 179, 120),      # Servo 5 Claw
            ]

            safe_values = clamp_positions(values)

            print("Raw:", raw, "Mapped:", values, "Safe:", safe_values)

            send_to_arm(arm, safe_values)

        except KeyboardInterrupt:
            print("\nStopping bridge.")
            send_to_arm(arm, HOME_POS)
            time.sleep(1)
            break

        except Exception as e:
            print("Error:", e)


if __name__ == "__main__":
    main()
