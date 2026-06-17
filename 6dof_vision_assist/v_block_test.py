# vision_block_test.py
# Sends arm to VISION_HOME, then detects colored blocks in camera view.

import cv2
import numpy as np
import serial
import time

ARM_PORT = "COM4"      # change if needed
BAUD_RATE = 115200

VISION_HOME = [60, 110, 0, 124, 118, 70]

CAMERA_ID = 0

# Ignore claw area: upper-left part of image
IGNORE_CLAW_AREA = False # True Jay


def send_to_arm(ser, pos):
    line = ",".join(str(int(v)) for v in pos) + "\n"
    ser.write(line.encode())
    print("Sent:", line.strip())


def detect_color(frame, color_name, lower, upper):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, lower, upper)

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

    return {
        "color": color_name,
        "x": cx,
        "y": cy,
        "w": w,
        "h": h,
        "area": int(best_area),
        "box": (x, y, w, h)
    }


def main():
    print("Opening arm port...")
    arm = serial.Serial(ARM_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)

    print("Sending VISION_HOME...")
    send_to_arm(arm, VISION_HOME)
    time.sleep(1.5)

    print("Opening camera...")
    cap = cv2.VideoCapture(CAMERA_ID)

    if not cap.isOpened():
        print("ERROR: Camera not found.")
        return

    # HSV color ranges
    colors = {
        "RED1":   (np.array([0, 80, 80]),   np.array([10, 255, 255])),
        "RED2":   (np.array([170, 80, 80]), np.array([180, 255, 255])),
        "YELLOW": (np.array([20, 80, 80]),  np.array([35, 255, 255])),
        "GREEN":  (np.array([40, 60, 60]),  np.array([85, 255, 255])),
        "BLUE":   (np.array([90, 60, 60]),  np.array([130, 255, 255])),
    }

    print("Vision test running.")
    print("Press Q to quit.")
    print()
    print("COLOR      X     Y     W     H     AREA")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Camera read failed.")
            break

        h_img, w_img = frame.shape[:2]

        # Mask out claw area visually
        #if IGNORE_CLAW_AREA:
        #    frame[0:int(h_img * 0.55), 0:int(w_img * 0.45)] = 0

        results = []

        # Red needs two HSV ranges
        red1 = detect_color(frame, "RED", colors["RED1"][0], colors["RED1"][1])
        red2 = detect_color(frame, "RED", colors["RED2"][0], colors["RED2"][1])

        red = red1
        if red2 and (not red1 or red2["area"] > red1["area"]):
            red = red2

        if red:
            results.append(red)

        for name in ["YELLOW", "GREEN", "BLUE"]:
            lower, upper = colors[name]
            r = detect_color(frame, name, lower, upper)
            if r:
                results.append(r)

        display = frame.copy()

        for r in results:
            x, y, w, h = r["box"]
            cv2.rectangle(display, (x, y), (x + w, y + h), (255, 255, 255), 2)
            cv2.putText(display, r["color"], (x, y - 8),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

            print(f"{r['color']:<8} {r['x']:>4} {r['y']:>5} {r['w']:>5} {r['h']:>5} {r['area']:>8}")

        cv2.imshow("Vision Block Test", display)

        key = cv2.waitKey(100) & 0xFF
        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    arm.close()


if __name__ == "__main__":
    main()
