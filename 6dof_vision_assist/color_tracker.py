import cv2
import numpy as np
import time

CAMERA_INDEX = 0

# Use DirectShow on Windows
cam = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_DSHOW)

cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cam.set(cv2.CAP_PROP_FPS, 30)

time.sleep(1)

if not cam.isOpened():
    print("Camera did not open.")
    exit()

print("Color tracker running.")
print("Press ESC to quit.")
print("Tracking RED object.")

while True:
    ret, frame = cam.read()

    if not ret or frame is None:
        print("No frame received")
        time.sleep(0.2)
        continue

    # Convert camera image from BGR to HSV
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    # Red wraps around HSV hue, so use two ranges
    lower_red1 = np.array([0, 100, 80])
    upper_red1 = np.array([10, 255, 255])

    lower_red2 = np.array([170, 100, 80])
    upper_red2 = np.array([180, 255, 255])

    mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
    mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
    mask = mask1 + mask2

    # Clean up noise
    mask = cv2.erode(mask, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )

    height, width = frame.shape[:2]

    # Draw screen center crosshair
    cv2.line(frame, (width // 2 - 20, height // 2), (width // 2 + 20, height // 2), (255, 255, 255), 2)
    cv2.line(frame, (width // 2, height // 2 - 20), (width // 2, height // 2 + 20), (255, 255, 255), 2)

    if contours:
        largest = max(contours, key=cv2.contourArea)
        area = cv2.contourArea(largest)

        if area > 500:
            x, y, w, h = cv2.boundingRect(largest)

            center_x = x + w // 2
            center_y = y + h // 2

            # Pixel offset from center of screen
            error_x = center_x - width // 2
            error_y = center_y - height // 2

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.circle(frame, (center_x, center_y), 6, (0, 255, 255), -1)

            cv2.putText(frame, f"RED OBJECT", (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            cv2.putText(frame, f"Pixel Center: X={center_x} Y={center_y}",
                        (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (0, 255, 255), 2)

            cv2.putText(frame, f"Offset: X={error_x} Y={error_y}",
                        (20, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (0, 255, 255), 2)

            cv2.putText(frame, f"Area: {int(area)}",
                        (20, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8,
                        (0, 255, 255), 2)

            print(f"Object found: center=({center_x},{center_y}) offset=({error_x},{error_y}) area={int(area)}")

    cv2.imshow("6DOF Arm Color Tracker", frame)
    cv2.imshow("Mask", mask)

    if cv2.waitKey(1) == 27:
        break

cam.release()
cv2.destroyAllWindows()
