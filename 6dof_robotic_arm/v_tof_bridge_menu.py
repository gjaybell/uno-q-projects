import cv2
import numpy as np
import serial
import time
import re

# ============================================================
# PORTS
# ============================================================

ARM_PORT = "COM4"      # UNO Q arm receiver
TOF_PORT = "COM8"      # Pro Mini TOF400C
BAUD_RATE = 115200
CAMERA_ID = 0

# ============================================================
# SERVO POSITIONS
# ============================================================

CLAW_OPEN = 70
CLAW_CLOSED = 103

VISION_HOME = [70, 116, 48, 180, 102, CLAW_OPEN]
APPROACH_POS = [76, 105, 43, 138, 116, CLAW_OPEN]
LIFT_POS = [76, 105, 43, 138, 116, CLAW_CLOSED]

SAFE_LOW  = [0, 40, 0, 70, 0, 70]
SAFE_HIGH = [165, 130, 140, 185, 175, 120]

# ============================================================
# TOF SETTINGS
# ============================================================

TOF_PICKUP_MM = 125
TOF_TIMEOUT_SEC = 2.0

# ============================================================
# VISION SETTINGS
# ============================================================

TRACK_COLOR = "red"
MIN_AREA = 1200
EDGE_MARGIN = 40

CENTER_DEADZONE_X = 60
CENTER_DEADZONE_Y = 50

SERVO0_MIN = 20
SERVO0_MAX = 140

SERVO1_MIN = 40
SERVO1_MAX = 130

SERVO0_STEP = 1
SERVO1_KP = 0.10
SERVO1_MAX_ADJUST = 30

TRACK_LOOPS = 120
CENTER_HOLD_COUNT = 12
LOOP_DELAY = 0.08

# S0 direction corrected for new camera mount
# If it ever goes wrong again, change this to -1.
SERVO0_DIRECTION = 1

DESCENT_STEPS = [
    [76, 105, 43, 138, 116, CLAW_OPEN],
    [76, 99, 43, 135, 116, CLAW_OPEN],
    [76, 94, 43, 130, 116, CLAW_OPEN],
    [76, 89, 43, 115, 116, CLAW_OPEN],
    [76, 85, 43, 115, 116, CLAW_OPEN],
    [76, 80, 43, 115, 116, CLAW_OPEN],
    [76, 75, 43, 115, 116, CLAW_OPEN],
]


def clamp(value, low, high):
    return max(low, min(high, value))


def send_to_arm(arm, pos):
    line = ",".join(str(int(v)) for v in pos) + "\n"
    arm.write(line.encode())
    print("ARM:", line.strip())


def move_slow(arm, start, end, delay=0.04):
    current = start[:]
    max_steps = max(abs(end[i] - start[i]) for i in range(6))

    if max_steps == 0:
        send_to_arm(arm, end)
        return end[:]

    for step in range(1, max_steps + 1):
        for i in range(6):
            current[i] = int(round(start[i] + (end[i] - start[i]) * step / max_steps))
        send_to_arm(arm, current)
        time.sleep(delay)

    return end[:]


def read_tof_mm(tof):
    start = time.time()

    while time.time() - start < TOF_TIMEOUT_SEC:
        try:
            line = tof.readline().decode(errors="ignore").strip()

            if not line:
                continue

            print("TOF:", line)

            if "TOF raw:" in line:
                m = re.search(r"TOF raw:\s*(-?\d+)", line)
                if m:
                    return int(m.group(1))

            elif line.startswith("Distance:"):
                m = re.search(r"Distance:\s*(-?\d+)", line)
                if m:
                    return int(m.group(1))

        except Exception:
            pass

    return None


def color_mask(hsv, color):
    if color == "red":
        mask1 = cv2.inRange(hsv, np.array([0, 80, 80]), np.array([10, 255, 255]))
        mask2 = cv2.inRange(hsv, np.array([170, 80, 80]), np.array([180, 255, 255]))
        return mask1 | mask2

    if color == "yellow":
        return cv2.inRange(hsv, np.array([20, 80, 80]), np.array([35, 255, 255]))

    if color == "green":
        return cv2.inRange(hsv, np.array([40, 60, 60]), np.array([85, 255, 255]))

    if color == "blue":
        return cv2.inRange(hsv, np.array([90, 60, 60]), np.array([130, 255, 255]))

    return None


def find_block(frame, last_target=None):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = color_mask(hsv, TRACK_COLOR)

    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    height, width = frame.shape[:2]

    candidates = []

    for c in contours:
        area = cv2.contourArea(c)

        if area < MIN_AREA:
            continue

        x, y, w, h = cv2.boundingRect(c)
        cx = x + w // 2
        cy = y + h // 2

        if cx < EDGE_MARGIN or cx > width - EDGE_MARGIN:
            continue

        if cy < EDGE_MARGIN or cy > height - EDGE_MARGIN:
            continue

        candidates.append((cx, cy, x, y, w, h, int(area)))

    if not candidates:
        return None, mask

    if last_target is not None:
        lx, ly = last_target

        def dist_to_last(item):
            cx, cy, *_ = item
            return abs(cx - lx) + abs(cy - ly)

        best = min(candidates, key=dist_to_last)
    else:
        best = max(candidates, key=lambda item: item[6])

    return best, mask


def vision_test(cap):
    print()
    print("Vision test running.")
    print("Press Q in camera window to quit.")

    last_target = None

    while True:
        ret, frame = cap.read()

        if not ret or frame is None:
            print("Camera read failed.")
            time.sleep(0.2)
            continue

        height, width = frame.shape[:2]
        center_x = width // 2
        center_y = height // 2

        result, mask = find_block(frame, last_target)

        cv2.line(frame, (center_x, 0), (center_x, height), (255, 255, 255), 2)
        cv2.line(frame, (0, center_y), (width, center_y), (255, 255, 255), 2)

        if result:
            cx, cy, x, y, w, h, area = result
            last_target = (cx, cy)

            error_x = cx - center_x
            error_y = cy - center_y

            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 2)
            cv2.circle(frame, (cx, cy), 6, (255, 255, 255), -1)

            cv2.putText(frame, f"{TRACK_COLOR.upper()} X={cx} Y={cy} AREA={area}",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (255, 255, 255), 2)

            cv2.putText(frame, f"ERR X={error_x:+d} Y={error_y:+d}",
                        (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (255, 255, 255), 2)

            print(f"X={cx} Y={cy} errX={error_x:+4d} errY={error_y:+4d} area={area}")

        else:
            cv2.putText(frame, "No valid target",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (255, 255, 255), 2)

        cv2.imshow("Vision Test", frame)
        cv2.imshow("Mask", mask)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q") or key == ord("Q"):
            break

    cv2.destroyWindow("Vision Test")
    cv2.destroyWindow("Mask")


def servo_jog_menu(arm, current_pos):
    print()
    print("===== SERVO JOG TEST =====")
    print("Select servo 0-5.")
    print("+ = increase selected servo")
    print("- = decrease selected servo")
    print("S = show current position")
    print("H = move to Vision Home")
    print("A = move to Approach")
    print("Q = return to main menu")

    selected = 0
    step = 1

    while True:
        print()
        print("Current pos:", current_pos)
        print("Selected servo:", selected, " value:", current_pos[selected])
        choice = input("Servo jog command: ").strip().lower()

        if choice in ["0", "1", "2", "3", "4", "5"]:
            selected = int(choice)

        elif choice == "+":
            current_pos[selected] += step
            current_pos[selected] = clamp(current_pos[selected], SAFE_LOW[selected], SAFE_HIGH[selected])
            send_to_arm(arm, current_pos)

        elif choice == "-":
            current_pos[selected] -= step
            current_pos[selected] = clamp(current_pos[selected], SAFE_LOW[selected], SAFE_HIGH[selected])
            send_to_arm(arm, current_pos)

        elif choice == "s":
            print("Current position:", current_pos)

        elif choice == "h":
            current_pos = move_slow(arm, current_pos, VISION_HOME)

        elif choice == "a":
            target = APPROACH_POS[:]
            target[0] = current_pos[0]
            current_pos = move_slow(arm, current_pos, target)

        elif choice == "q":
            return current_pos

        else:
            print("Invalid command.")


def track_to_center(arm, cap, current_pos):
    centered_count = 0
    last_error_y = 0
    last_target = None

    print()
    print("Tracking target...")
    print("Press ESC in camera window to abort.")

    for _ in range(TRACK_LOOPS):
        ret, frame = cap.read()

        if not ret or frame is None:
            print("Camera read failed.")
            time.sleep(0.2)
            continue

        height, width = frame.shape[:2]
        center_x = width // 2
        center_y = height // 2

        result, mask = find_block(frame, last_target)

        cv2.line(frame, (center_x, 0), (center_x, height), (255, 255, 255), 2)
        cv2.line(frame, (0, center_y), (width, center_y), (255, 255, 255), 2)

        if result:
            cx, cy, x, y, w, h, area = result
            last_target = (cx, cy)

            error_x = cx - center_x
            error_y = cy - center_y
            last_error_y = error_y

            servo0 = current_pos[0]

            if abs(error_x) > CENTER_DEADZONE_X:
                if error_x > 0:
                    servo0 += SERVO0_STEP * SERVO0_DIRECTION
                    direction = "S0 RIGHT"
                else:
                    servo0 -= SERVO0_STEP * SERVO0_DIRECTION
                    direction = "S0 LEFT"

                servo0 = clamp(servo0, SERVO0_MIN, SERVO0_MAX)
                current_pos[0] = servo0
                send_to_arm(arm, current_pos)
                centered_count = 0

            else:
                direction = "X CENTERED"
                centered_count += 1

            cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 2)
            cv2.circle(frame, (cx, cy), 6, (255, 255, 255), -1)

            cv2.putText(frame, f"{TRACK_COLOR.upper()} X={cx} Y={cy} AREA={area}",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (255, 255, 255), 2)

            cv2.putText(frame, f"ERR X={error_x:+d} Y={error_y:+d}",
                        (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (255, 255, 255), 2)

            cv2.putText(frame, f"S0={current_pos[0]} {direction}",
                        (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (255, 255, 255), 2)

            print(
                f"X={cx} Y={cy} errX={error_x:+4d} "
                f"errY={error_y:+4d} area={area} S0={current_pos[0]} {direction}"
            )

            if centered_count >= CENTER_HOLD_COUNT:
                print("Target centered.")
                cv2.imshow("Vision TOF Pickup", frame)
                cv2.waitKey(250)
                return current_pos, last_error_y

        else:
            cv2.putText(frame, "No valid target",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (255, 255, 255), 2)
            centered_count = 0

        cv2.imshow("Vision TOF Pickup", frame)
        cv2.imshow("Mask", mask)

        key = cv2.waitKey(1) & 0xFF
        if key == 27:
            print("Aborted by user.")
            return None, last_error_y

        time.sleep(LOOP_DELAY)

    print("Tracking timed out.")
    return current_pos, last_error_y


def build_approach_from_y(current_pos, error_y):
    target = APPROACH_POS[:]
    target[0] = current_pos[0]

    if abs(error_y) > CENTER_DEADZONE_Y:
        adjust = error_y * SERVO1_KP
        adjust = clamp(adjust, -SERVO1_MAX_ADJUST, SERVO1_MAX_ADJUST)

        # If S1 goes the wrong forward/back direction, change + adjust to - adjust.
        target[1] = int(round(APPROACH_POS[1] + adjust))
    else:
        adjust = 0
        target[1] = APPROACH_POS[1]

    target[1] = clamp(target[1], SERVO1_MIN, SERVO1_MAX)

    print()
    print("Approach target:")
    print("Y error:", error_y)
    print("Servo1 adjust:", adjust)
    print("Target:", target)

    return target


def lower_using_tof(arm, tof, current_pos):
    print()
    print("Lowering using TOF...")
    print("Target pickup TOF:", TOF_PICKUP_MM, "mm")

    for step in DESCENT_STEPS:
        target = step[:]
        target[0] = current_pos[0]
        target[1] = current_pos[1]

        current_pos = move_slow(arm, current_pos, target, delay=0.03)

        tof.reset_input_buffer()
        time.sleep(0.2)

        d = read_tof_mm(tof)

        if d is None:
            print("No TOF reading. Stopping descent.")
            return current_pos, False

        print("Current TOF distance:", d, "mm")

        if d <= TOF_PICKUP_MM:
            print("Pickup distance reached.")
            return current_pos, True

    print("Reached last descent step.")
    return current_pos, True


def automatic_red_pickup(arm, tof, cap, current_pos):
    input("Place RED block in workspace, then press Enter to start pickup...")

    tracked_pos, error_y = track_to_center(arm, cap, current_pos)

    if tracked_pos is None:
        print("Tracking failed or aborted.")
        return current_pos

    current_pos = tracked_pos

    approach = build_approach_from_y(current_pos, error_y)

    print("Moving to approach position...")
    current_pos = move_slow(arm, current_pos, approach)

    tof.reset_input_buffer()
    time.sleep(0.5)

    d = read_tof_mm(tof)
    print("TOF at approach:", d, "mm")

    current_pos, ok = lower_using_tof(arm, tof, current_pos)

    if not ok:
        print("TOF descent failed. Returning home.")
        current_pos = move_slow(arm, current_pos, VISION_HOME)
        return current_pos

    print("Closing claw...")
    grab = current_pos[:]
    grab[5] = CLAW_CLOSED
    current_pos = move_slow(arm, current_pos, grab, delay=0.05)
    time.sleep(1)

    print("Lifting object...")
    lift = LIFT_POS[:]
    lift[0] = current_pos[0]
    lift[1] = current_pos[1]
    current_pos = move_slow(arm, current_pos, lift)

    print("Returning Vision Home with object...")
    hold_home = VISION_HOME[:]
    hold_home[5] = CLAW_CLOSED
    current_pos = move_slow(arm, current_pos, hold_home)

    print("Holding for 5 seconds...")
    time.sleep(5)

    print("Opening claw...")
    release = VISION_HOME[:]
    release[5] = CLAW_OPEN
    current_pos = move_slow(arm, current_pos, release, delay=0.05)

    print("Finished pickup.")
    return current_pos


def main():
    print("Opening arm port:", ARM_PORT)
    arm = serial.Serial(ARM_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)

    print("Opening TOF port:", TOF_PORT)
    tof = serial.Serial(TOF_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    tof.reset_input_buffer()

    print("Opening camera...")
    cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)
    print("Camera width:", cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    print("Camera height:", cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    if not cap.isOpened():
        print("ERROR: Camera not found.")
        arm.close()
        tof.close()
        return

    current_pos = VISION_HOME[:]

    print("Sending Vision Home...")
    send_to_arm(arm, current_pos)
    time.sleep(1)

    while True:
        print()
        print("===== VISION TOF BRIDGE MENU =====")
        print("1 = Automatic RED pickup")
        print("2 = Vision test only")
        print("3 = Servo jog test")
        print("4 = Move to Vision Home")
        print("5 = Read TOF")
        print("Q = Quit")

        choice = input("Select option: ").strip().lower()

        if choice == "1":
            current_pos = automatic_red_pickup(arm, tof, cap, current_pos)

        elif choice == "2":
            vision_test(cap)

        elif choice == "3":
            current_pos = servo_jog_menu(arm, current_pos)

        elif choice == "4":
            current_pos = move_slow(arm, current_pos, VISION_HOME)

        elif choice == "5":
            tof.reset_input_buffer()
            time.sleep(0.5)
            d = read_tof_mm(tof)
            print("TOF distance:", d, "mm")

        elif choice == "q":
            print("Returning to Vision Home...")
            current_pos = move_slow(arm, current_pos, VISION_HOME)
            break

        else:
            print("Invalid selection.")

    arm.close()
    tof.close()
    cap.release()
    cv2.destroyAllWindows()
    print("Finished.")


if __name__ == "__main__":
    main()
