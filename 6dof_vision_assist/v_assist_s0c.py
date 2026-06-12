import cv2
import numpy as np
import serial
import time

# -----------------------------
# USER SETTINGS
# -----------------------------
CAMERA_INDEX = 0       # Try 1 or 2 if this is your built-in webcam

ARM_PORT  = "COM4"
BAUD_RATE = 115200

HOME_POS = [75, 85, 42, 125, 90, 97]

# Servo 0 limits (from your calibration chart)
SERVO0_MIN    = 45
SERVO0_CENTER = 75
SERVO0_MAX    = 110

# Camera settings
FRAME_WIDTH  = 1280
FRAME_HEIGHT = 720
FPS          = 30

# Detection settings
MIN_AREA = 5000         # 1000 Jay minimum contour area to count as a valid object
                        # increase if getting false detections, decrease if missing small objects

# Tracking settings
CENTER_DEADZONE_X = 80  # 40 Jay pixels — how close to center before stopping movement
SERVO0_KP         = 0.005  # .03 Jay proportional gain — increase for faster response, decrease if oscillating
LOOP_DELAY        = 0.08  # .02 Jay seconds between corrections (~50fps)

# -----------------------------
# STATE
# -----------------------------
last_sent   = None
servo0_pos  = float(SERVO0_CENTER)


def clamp(value, low, high):
    return max(low, min(high, value))


def send_to_arm(arm, values):
    global last_sent

    values = [int(round(v)) for v in values]

    if values == last_sent:
        return

    command = ",".join(str(v) for v in values)
    arm.write((command + "\n").encode())
    print("Sent to arm:", command)
    last_sent = values.copy()


def get_color_masks(hsv):
    """
    Returns HSV color masks for RED, BLUE, GREEN, YELLOW.
    Adjust the HSV ranges if your lighting makes colors hard to detect.
    """
    masks = {}

    # Red wraps around the HSV hue boundary — needs two ranges combined
    red1 = cv2.inRange(hsv, np.array([0,   100, 80]),  np.array([10,  255, 255]))
    red2 = cv2.inRange(hsv, np.array([170, 100, 80]),  np.array([180, 255, 255]))
    masks["RED"]    = red1 + red2

    masks["BLUE"]   = cv2.inRange(hsv, np.array([95,  80, 60]),  np.array([130, 255, 255]))
    masks["GREEN"]  = cv2.inRange(hsv, np.array([40,  70, 60]),  np.array([85,  255, 255]))
    masks["YELLOW"] = cv2.inRange(hsv, np.array([20,  80, 80]),  np.array([35,  255, 255]))

    return masks


def find_largest_colored_object(frame):
    """
    Scans for RED, BLUE, GREEN, YELLOW objects.
    Returns the largest one found above MIN_AREA, or None.
    """
    hsv  = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    masks = get_color_masks(hsv)

    best = None

    for color_name, mask in masks.items():
        # Clean up noise
        mask = cv2.erode(mask,  None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            continue

        largest = max(contours, key=cv2.contourArea)
        area    = cv2.contourArea(largest)

        if area < MIN_AREA:
            continue

        x, y, w, h = cv2.boundingRect(largest)
        center_x   = x + w // 2
        center_y   = y + h // 2

        if best is None or area > best["area"]:
            best = {
                "color":    color_name,
                "area":     area,
                "x": x, "y": y, "w": w, "h": h,
                "center_x": center_x,
                "center_y": center_y,
            }

    return best


def find_available_cameras():
    """Scan indices 0-4 and print which cameras are available."""
    print("Scanning for cameras...")
    for i in range(5):
        cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
        if cap.isOpened():
            print(f"  Camera index {i} — available")
            cap.release()
        else:
            print(f"  Camera index {i} — not found")


def main():
    global servo0_pos, last_sent

    print("=" * 55)
    print(" Vision-Assisted Servo 0 Tracking")
    print("=" * 55)
    print(f" Arm port    : {ARM_PORT}")
    print(f" Camera index: {CAMERA_INDEX}")
    print(f" Deadzone    : ±{CENTER_DEADZONE_X}px")
    print(f" KP gain     : {SERVO0_KP}")
    print(f" Min area    : {MIN_AREA}px²")
    print("=" * 55)
    print(" Detects: RED  BLUE  GREEN  YELLOW")
    print(" Servo 0 tracks object horizontally.")
    print(" S1-S5 stay at HOME.")
    print(" Press ESC in video window or Ctrl+C to stop.")
    print("=" * 55)
    print()

    # Scan cameras so user knows which indices are available
    find_available_cameras()
    print()

    # Connect to arm
    arm = serial.Serial(ARM_PORT, BAUD_RATE, timeout=1)
    time.sleep(3)
    arm.reset_input_buffer()

    print("Sending HOME position...")
    send_to_arm(arm, HOME_POS)
    time.sleep(0.5)
    last_sent = None
    send_to_arm(arm, HOME_POS)
    print("HOME sent.")
    print()

    # Open camera
    cam = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cam.set(cv2.CAP_PROP_FPS,          FPS)
    time.sleep(1)

    if not cam.isOpened():
        print(f"ERROR: Camera index {CAMERA_INDEX} did not open.")
        print("Check the camera scan above and update CAMERA_INDEX.")
        return

    print("Camera open. Starting tracking loop.")

    while True:
        ret, frame = cam.read()

        if not ret or frame is None:
            print("No frame received — retrying...")
            time.sleep(0.2)
            continue

        height, width    = frame.shape[:2]
        screen_center_x  = width  // 2
        screen_center_y  = height // 2

        best       = find_largest_colored_object(frame)
        status     = "NO TARGET"
        correction = "SEARCHING"

        # ── Draw center crosshair ─────────────────────────────
        cv2.line(frame,
                 (screen_center_x - 30, screen_center_y),
                 (screen_center_x + 30, screen_center_y),
                 (255, 255, 255), 2)
        cv2.line(frame,
                 (screen_center_x, screen_center_y - 30),
                 (screen_center_x, screen_center_y + 30),
                 (255, 255, 255), 2)

        # Draw deadzone band
        cv2.line(frame,
                 (screen_center_x - CENTER_DEADZONE_X, 0),
                 (screen_center_x - CENTER_DEADZONE_X, height),
                 (80, 80, 80), 1)
        cv2.line(frame,
                 (screen_center_x + CENTER_DEADZONE_X, 0),
                 (screen_center_x + CENTER_DEADZONE_X, height),
                 (80, 80, 80), 1)

        if best:
            color_name = best["color"]
            x, y, w, h = best["x"], best["y"], best["w"], best["h"]
            center_x   = best["center_x"]
            center_y   = best["center_y"]
            area       = best["area"]

            error_x = center_x - screen_center_x
            error_y = center_y - screen_center_y

            # ── FIXED DIRECTION + PROPORTIONAL CONTROL ────────
            # From calibration chart:
            #   PS0 increasing → turns LEFT (CCW)
            #   PS0 decreasing → turns RIGHT (CW)
            # Object RIGHT of center (error_x > 0) → need to turn RIGHT → decrease servo0
            # Object LEFT  of center (error_x < 0) → need to turn LEFT  → increase servo0
            if abs(error_x) > CENTER_DEADZONE_X:
                correction_amount = error_x * SERVO0_KP
                servo0_pos -= correction_amount   # subtract: right=decrease, left=increase
                correction  = "TURN RIGHT" if error_x > 0 else "TURN LEFT"
            else:
                correction = "CENTERED"

            servo0_pos = clamp(servo0_pos, SERVO0_MIN, SERVO0_MAX)

            values = [
                servo0_pos,
                HOME_POS[1],
                HOME_POS[2],
                HOME_POS[3],
                HOME_POS[4],
                HOME_POS[5],
            ]
            send_to_arm(arm, values)

            status = f"{color_name} LOCKED"

            # ── Draw detection overlay ─────────────────────────
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (center_x, center_y), 7, (0, 255, 255), -1)
            cv2.line(frame, (screen_center_x, screen_center_y),
                     (center_x, center_y), (0, 200, 255), 1)

            cv2.putText(frame, f"{color_name}",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            cv2.putText(frame, f"Center  X={center_x}  Y={center_y}",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, f"Offset  X={error_x:+d}  Y={error_y:+d}",
                        (20, 72),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, f"Servo0  {int(servo0_pos)} deg",
                        (20, 104),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, f"Area    {int(area)} px",
                        (20, 136),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            cv2.putText(frame, correction,
                        (20, 172),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)

            print(
                f"{color_name:<7} "
                f"cx={center_x:4d}  "
                f"err={error_x:+4d}  "
                f"servo0={int(servo0_pos):3d}  "
                f"area={int(area):6d}  "
                f"{correction}"
            )

        else:
            # No object detected
            cv2.putText(frame, "No target detected",
                        (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)
            cv2.putText(frame, f"Servo0  {int(servo0_pos)} deg",
                        (20, 75),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (100, 100, 255), 2)

        # ── Status bar at bottom ──────────────────────────────
        cv2.rectangle(frame, (0, height - 36), (width, height), (0, 0, 0), -1)
        cv2.putText(frame, f"STATUS: {status}   |   Servo0: {int(servo0_pos)}   |   ESC to quit",
                    (10, height - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)

        cv2.imshow("Vision Tracking — Servo 0", frame)

        key = cv2.waitKey(1)
        if key == 27:   # ESC
            break

        time.sleep(LOOP_DELAY)

    print()
    print("Stopping. Returning to HOME.")
    send_to_arm(arm, HOME_POS)
    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nStopped by user.")
