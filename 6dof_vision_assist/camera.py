import cv2
import time

cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)

cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cam.set(cv2.CAP_PROP_FPS, 30)

time.sleep(1)

if not cam.isOpened():
    print("Camera did not open")
    exit()

while True:
    ret, frame = cam.read()

    if not ret or frame is None:
        print("No frame received")
        time.sleep(0.2)
        continue

    cv2.imshow("C920x Arm Camera", frame)

    if cv2.waitKey(1) == 27:
        break

cam.release()
cv2.destroyAllWindows()
