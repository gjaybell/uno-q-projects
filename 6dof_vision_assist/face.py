import cv2
import time

CAMERA_ID = 0

FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS = 30

print("Starting C920x face detection test.")
print("Press ESC to quit.")

# Open Logitech C920x camera
cam = cv2.VideoCapture(CAMERA_ID, cv2.CAP_DSHOW)

cam.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
cam.set(cv2.CAP_PROP_FPS, FPS)

time.sleep(1)

if not cam.isOpened():
    print("ERROR: Camera did not open.")
    print("Try changing CAMERA_ID from 0 to 1.")
    exit()

# Built-in OpenCV face detector file
cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
face_detector = cv2.CascadeClassifier(cascade_path)

if face_detector.empty():
    print("ERROR: Could not load face detector.")
    exit()

while True:
    ret, frame = cam.read()

    if not ret or frame is None:
        print("No frame received. Retrying...")
        time.sleep(0.2)
        continue

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80)
    )

    for (x, y, w, h) in faces:
        cx = x + w // 2
        cy = y + h // 2

        cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 255, 255), 2)
        cv2.circle(frame, (cx, cy), 5, (255, 255, 255), -1)

        cv2.putText(frame, f"FACE X={cx} Y={cy}",
                    (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (255, 255, 255),
                    2)

        print(f"Face detected: X={cx} Y={cy} W={w} H={h}")

    cv2.imshow("C920x Face Detection Test", frame)

    key = cv2.waitKey(1) & 0xFF
    if key == 27:
        break

cam.release()
cv2.destroyAllWindows()

print("Finished.")
