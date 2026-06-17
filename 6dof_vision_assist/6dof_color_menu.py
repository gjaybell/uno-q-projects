import cv2
import numpy as np
import serial
import time
import math

ARM_PORT = "COM4"
BAUD_RATE = 115200
CAMERA_ID = 0

# Vision Home / camera calibration pose
# Claw open for best camera view
VISION_HOME = [80, 113, 0, 118, 118, 70]

CLAW_OPEN = 70
CLAW_CLOSED = 103
HOLD_TIME = 5

POINTS = {
    "RL": {
        "cam": (600, 368),
        "above": [33, 73, 30, 132, 97, CLAW_OPEN],
        "on":    [33, 68, 33, 132, 97, CLAW_OPEN],
    },
    "LL": {
        "cam": (56, 307),
        "above": [118, 85, 50, 112, 147, CLAW_OPEN],
        "on":    [118, 73, 46, 112, 147, CLAW_OPEN],
    },
    "RU": {
        "cam": (590, 148),
        "above": [47, 47, 0, 119, 97, CLAW_OPEN],
        "on":    [47, 40, 0, 112, 115, CLAW_OPEN],
    },
    "LU": {
        "cam": (75, 125),
        "above": [104, 43, 0, 109, 137, CLAW_OPEN],
        "on":    [104, 43, 0, 117, 144, CLAW_OPEN],
    },
    "CENTER": {
        "cam": (330, 247),
        "above": [76, 79, 43, 118, 118, CLAW_OPEN],
        "on":    [76, 72, 43, 115, 116, CLAW_OPEN],
    },
}


def send_to_arm(ser, pos):
    line = ",".join(str(int(v)) for v in pos) + "\n"
    ser.write(line.encode())
    print("Sent:", line.strip())


def move_slow(ser, start, end, delay=0.04):
    current = start[:]
    max_steps = max(abs(end[i] - start[i]) for i in range(6))

    if max_steps == 0:
        send_to_arm(ser, end)
        return end[:]

    for step in range(1, max_steps + 1):
        for i in range(6):
            current[i] = int(round(start[i] + (end[i] - start[i]) * step / max_steps))
        send_to_arm(ser, current)
        time.sleep(delay)

    return end[:]


def color_mask(hsv, color):
    if color == "red":
        lower1 = np.array([0, 80, 80])
        upper1 = np.array([10, 255, 255])
        lower2 = np.array([170, 80, 80])
        upper2 = np.array([180, 255, 255])
        return cv2.inRange(hsv, lower1, upper1) | cv2.inRange(hsv, lower2, upper2)

    if color == "yellow":
        return cv2.inRange(hsv, np.array([20, 80, 80]), np.array([35, 255, 255]))

    if color == "green":
        return cv2.inRange(hsv, np.array([40, 60, 60]), np.array([85, 255, 255]))

    if color == "blue":
        return cv2.inRange(hsv, np.array([90, 60, 60]), np.array([130, 255, 255]))

    return None


def detect_color(frame, color):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = color_mask(hsv, color)

    if mask is None:
        return None

    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best = None
    best_area = 0

    for c in contours:
        area = cv2.contourArea(c)
        if area > best_area:
            best_area = area
            best = c

    if best is None or best_area < 300:
        return None

    x, y, w, h = cv2.boundingRect(best)
    cx = x + w // 2
    cy = y + h // 2

    return cx, cy, w, h, int(best_area)


def nearest_point(x, y):
    best_name = None
    best_dist = 999999

    for name, data in POINTS.items():
        px, py = data["cam"]
        d = math.sqrt((x - px) ** 2 + (y - py) ** 2)

        if d < best_dist:
            best_dist = d
            best_name = name

    return best_name, best_dist


def find_selected_color(color):
    cap = cv2.VideoCapture(CAMERA_ID)

    if not cap.isOpened():
        print("ERROR: Camera not found.")
        return None

    print(f"Looking for {color.upper()} block...")

    result = None

    for _ in range(40):
        ret, frame = cap.read()

        if not ret:
            print("Camera read failed. Retrying...")
            time.sleep(0.2)
            continue

        result = detect_color(frame, color)

        display = frame.copy()

        if result:
            x, y, w, h, area = result
            cv2.rectangle(display, (x - w // 2, y - h // 2),
                          (x + w // 2, y + h // 2), (255, 255, 255), 2)
            cv2.putText(display, f"{color.upper()} {x},{y}", (x - 40, y - 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Color Pickup Vision", display)
        cv2.waitKey(100)

        if result:
            break

    cap.release()
    cv2.destroyAllWindows()

    return result


def pickup_color(arm, current_pos, color):
    print()
    print("Moving to Vision Home...")
    current_pos = move_slow(arm, current_pos, VISION_HOME)
    time.sleep(1)

    found = find_selected_color(color)

    if not found:
        print(f"No {color.upper()} block found.")
        return current_pos

    x, y, w, h, area = found

    print(f"{color.upper()} found at X={x}, Y={y}, W={w}, H={h}, AREA={area}")

    target_name, dist = nearest_point(x, y)
    target = POINTS[target_name]

    print(f"Nearest calibration point: {target_name}, distance={dist:.1f} pixels")

    above = target["above"]
    on = target["on"]

    grab = on[:]
    grab[5] = CLAW_CLOSED

    lift = above[:]
    lift[5] = CLAW_CLOSED

    release_home = VISION_HOME[:]
    release_home[5] = CLAW_OPEN

    print("Move above block...")
    current_pos = move_slow(arm, current_pos, above)

    print("Lower to block...")
    current_pos = move_slow(arm, current_pos, on)

    print("Close claw...")
    current_pos = move_slow(arm, current_pos, grab, delay=0.05)
    time.sleep(1)

    print("Lift block...")
    current_pos = move_slow(arm, current_pos, lift)

    print("Return to Vision Home while holding block...")
    hold_home = VISION_HOME[:]
    hold_home[5] = CLAW_CLOSED
    current_pos = move_slow(arm, current_pos, hold_home)

    print(f"Holding for {HOLD_TIME} seconds...")
    time.sleep(HOLD_TIME)

    print("Open claw and drop block...")
    current_pos = move_slow(arm, current_pos, release_home, delay=0.05)
    time.sleep(1)

    print("Ready for next color.")
    return current_pos


def check_camera_calibration(arm, current_pos):
    print()
    print("Moving to Vision Home...")
    current_pos = move_slow(arm, current_pos, VISION_HOME)
    time.sleep(1)

    cap = cv2.VideoCapture(CAMERA_ID)

    if not cap.isOpened():
        print("ERROR: Camera not found.")
        return current_pos

    print()
    print("Camera calibration check running.")
    print("Place one block at LU, RU, LL, RL, or CENTER.")
    print("Press Q in the camera window to quit.")
    print()
    print("COLOR      X     Y     W     H     AREA")

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Camera read failed. Retrying...")
            time.sleep(0.2)
            continue

        display = frame.copy()

        for color in ["red", "yellow", "green", "blue"]:
            r = detect_color(frame, color)
            if r:
                x, y, w, h, area = r
                print(f"{color.upper():<8} {x:>4} {y:>5} {w:>5} {h:>5} {area:>8}")

                cv2.rectangle(display, (x - w // 2, y - h // 2),
                              (x + w // 2, y + h // 2), (255, 255, 255), 2)
                cv2.putText(display, f"{color.upper()} {x},{y}", (x - 40, y - 20),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        cv2.imshow("Camera Calibration Check", display)

        key = cv2.waitKey(150) & 0xFF
        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()

    return current_pos


def main():
    print("Opening arm port...")
    arm = serial.Serial(ARM_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)

    current_pos = VISION_HOME[:]

    print("Sending Vision Home...")
    send_to_arm(arm, VISION_HOME)
    time.sleep(2)

    while True:
        print()
        print("===== COLOR PICKUP MENU =====")
        print("R = Pick RED")
        print("Y = Pick YELLOW")
        print("G = Pick GREEN")
        print("B = Pick BLUE")
        print("C = Check camera calibration")
        print("H = Move to Vision Home")
        print("Q = Quit")
        choice = input("Select option: ").strip().lower()

        if choice == "r":
            current_pos = pickup_color(arm, current_pos, "red")
        elif choice == "y":
            current_pos = pickup_color(arm, current_pos, "yellow")
        elif choice == "g":
            current_pos = pickup_color(arm, current_pos, "green")
        elif choice == "b":
            current_pos = pickup_color(arm, current_pos, "blue")
        elif choice == "c":
            current_pos = check_camera_calibration(arm, current_pos)
        elif choice == "h":
            current_pos = move_slow(arm, current_pos, VISION_HOME)
        elif choice == "q":
            print("Returning to Vision Home...")
            current_pos = move_slow(arm, current_pos, VISION_HOME)
            break
        else:
            print("Invalid selection.")

    arm.close()
    print("Finished.")


if __name__ == "__main__":
    main()
