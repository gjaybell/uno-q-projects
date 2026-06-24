import cv2
import serial
import time
import math
import os
import json

ARM_PORT = "COM4"
BAUD_RATE = 115200
CAMERA_ID = 0

FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
FPS = 30

MODEL_FILE = "pam_jay_face_model.yml"
CAL_FILE = "face_calibration.json"
VISION_HOME_FILE = "vision_home.json"
CAMERA_SETTINGS_FILE = "camera_settings.json"

PEOPLE = {
    1: "Pam",
    2: "Jay",
}

VISION_HOME = [75, 113, 30, 185, 116, 70]

CLAW_OPEN = 70
CLAW_CLOSED = 103
HOLD_TIME = 5

CAMERA_SETTINGS = {
    "auto_exposure": 0.25,
    "exposure": -4,
    "gain": 0,
    "brightness": 150,
    "contrast": 128,
    "autofocus": 0
}

POINTS = {
    "RL": {
        "cam": (57, 225),
        "above": [33, 73, 30, 132, 97, CLAW_OPEN],
        "on":    [33, 68, 33, 132, 97, CLAW_OPEN],
    },
    "LL": {
        "cam": (1062, 160),
        "above": [118, 85, 50, 112, 147, CLAW_OPEN],
        "on":    [118, 73, 46, 112, 147, CLAW_OPEN],
    },
    "RU": {
        "cam": (112, 599),
        "above": [47, 47, 0, 119, 97, CLAW_OPEN],
        "on":    [47, 40, 0, 112, 115, CLAW_OPEN],
    },
    "LU": {
        "cam": (1062, 580),
        "above": [104, 43, 0, 109, 137, CLAW_OPEN],
        "on":    [104, 43, 0, 117, 144, CLAW_OPEN],
    },
    "CENTER": {
        "cam": (540, 400),
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


def load_camera_settings():
    global CAMERA_SETTINGS

    if not os.path.exists(CAMERA_SETTINGS_FILE):
        print("No camera_settings.json found. Using built-in camera settings.")
        return

    try:
        with open(CAMERA_SETTINGS_FILE, "r") as f:
            CAMERA_SETTINGS.update(json.load(f))

        print("Camera settings loaded from", CAMERA_SETTINGS_FILE)

    except Exception as e:
        print("Could not load camera settings.")
        print("Error:", e)


def save_camera_settings():
    with open(CAMERA_SETTINGS_FILE, "w") as f:
        json.dump(CAMERA_SETTINGS, f, indent=4)

    print("Camera settings saved to", CAMERA_SETTINGS_FILE)


def apply_camera_settings(cap):
    cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, CAMERA_SETTINGS["auto_exposure"])
    cap.set(cv2.CAP_PROP_EXPOSURE, CAMERA_SETTINGS["exposure"])
    cap.set(cv2.CAP_PROP_GAIN, CAMERA_SETTINGS["gain"])
    cap.set(cv2.CAP_PROP_BRIGHTNESS, CAMERA_SETTINGS["brightness"])
    cap.set(cv2.CAP_PROP_CONTRAST, CAMERA_SETTINGS["contrast"])
    cap.set(cv2.CAP_PROP_AUTOFOCUS, CAMERA_SETTINGS["autofocus"])

    print("Exposure:", cap.get(cv2.CAP_PROP_EXPOSURE))
    print("Gain:", cap.get(cv2.CAP_PROP_GAIN))
    print("Brightness:", cap.get(cv2.CAP_PROP_BRIGHTNESS))
    print("Contrast:", cap.get(cv2.CAP_PROP_CONTRAST))
    print("AutoFocus:", cap.get(cv2.CAP_PROP_AUTOFOCUS))


def camera_adjust_menu():
    print()
    print("===== CAMERA SETTINGS MENU =====")
    print("Current settings:")
    for k, v in CAMERA_SETTINGS.items():
        print(f"{k}: {v}")

    print()
    print("Suggested Brio exposure values:")
    print("-2 = brighter")
    print("-4 = medium")
    print("-6 = darker")
    print()
    print("Press Enter to keep current value.")

    for key in ["auto_exposure", "exposure", "gain", "brightness", "contrast", "autofocus"]:
        entry = input(f"New {key} ({CAMERA_SETTINGS[key]}): ").strip()

        if entry == "":
            continue

        try:
            if "." in entry:
                CAMERA_SETTINGS[key] = float(entry)
            else:
                CAMERA_SETTINGS[key] = int(entry)
        except Exception:
            print("Invalid value. Keeping old value.")

    save_camera_settings()
    print("New settings will be applied the next time the camera opens.")


def save_vision_home():
    with open(VISION_HOME_FILE, "w") as f:
        json.dump(VISION_HOME, f, indent=4)

    print("Vision Home saved to", VISION_HOME_FILE)
    print("Vision Home =", VISION_HOME)


def load_vision_home():
    global VISION_HOME

    if not os.path.exists(VISION_HOME_FILE):
        print("No vision_home.json found. Using built-in Vision Home.")
        return

    try:
        with open(VISION_HOME_FILE, "r") as f:
            data = json.load(f)

        if len(data) == 6:
            VISION_HOME = [int(v) for v in data]
            print("Vision Home loaded from", VISION_HOME_FILE)
            print("Vision Home =", VISION_HOME)
        else:
            print("Invalid vision_home.json. Using built-in Vision Home.")

    except Exception as e:
        print("Could not load Vision Home file.")
        print("Error:", e)


def set_vision_home_from_menu():
    global VISION_HOME

    print()
    print("Current Vision Home:")
    print(VISION_HOME)
    print()
    print("Enter new servo values.")
    print("Use six numbers: S0 S1 S2 S3 S4 S5")
    print("Example: 75 113 30 185 116 70")
    print("Press Enter to cancel.")
    print()

    entry = input("New Vision Home: ").strip()

    if entry == "":
        print("Cancelled.")
        return

    try:
        parts = entry.replace(",", " ").split()

        if len(parts) != 6:
            print("Invalid entry. Need exactly 6 values.")
            return

        VISION_HOME = [int(p) for p in parts]
        save_vision_home()

    except Exception:
        print("Invalid entry.")


def save_calibration():
    data = {}

    for name, point in POINTS.items():
        data[name] = {"cam": list(point["cam"])}

    with open(CAL_FILE, "w") as f:
        json.dump(data, f, indent=4)

    print("Calibration saved to", CAL_FILE)


def load_calibration():
    if not os.path.exists(CAL_FILE):
        print("No calibration file found. Using built-in face calibration values.")
        return

    try:
        with open(CAL_FILE, "r") as f:
            data = json.load(f)

        for name in data:
            if name in POINTS and "cam" in data[name]:
                POINTS[name]["cam"] = tuple(data[name]["cam"])

        print("Calibration loaded from", CAL_FILE)

    except Exception as e:
        print("Could not load calibration file.")
        print("Using built-in calibration values.")
        print("Error:", e)


def show_calibration():
    print()
    print("Current face calibration points:")
    for name in ["LU", "RU", "LL", "RL", "CENTER"]:
        x, y = POINTS[name]["cam"]
        print(f"{name:<6} = {x},{y}")

    print()
    print("Current Vision Home:")
    print(VISION_HOME)

    print()
    print("Current camera settings:")
    for k, v in CAMERA_SETTINGS.items():
        print(f"{k}: {v}")


def update_calibration_from_menu():
    print()
    print("Update face calibration points.")
    print("Use format: X,Y")
    print("Example: 540,400")
    print("Press Enter to keep current value.")
    print()

    for name in ["LU", "RU", "LL", "RL", "CENTER"]:
        current = POINTS[name]["cam"]
        print(f"{name} current = {current[0]},{current[1]}")

        entry = input(f"New {name} X,Y: ").strip()

        if entry == "":
            print("Keeping current value.")
            continue

        try:
            x_str, y_str = entry.split(",")
            x = int(x_str.strip())
            y = int(y_str.strip())

            POINTS[name]["cam"] = (x, y)
            print(f"{name} updated to {x},{y}")

        except Exception:
            print("Invalid entry. Use format like 540,400")
            print("Keeping current value.")

    save_calibration()
    show_calibration()


def nearest_point(x, y):
    best_name = None
    best_dist = 999999

    print(f"Face X={x}, Y={y}")

    for name, data in POINTS.items():
        px, py = data["cam"]
        d = math.sqrt((x - px) ** 2 + (y - py) ** 2)

        if d < best_dist:
            best_dist = d
            best_name = name

    return best_name, best_dist


def open_camera():
    cap = cv2.VideoCapture(CAMERA_ID, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, FPS)

    time.sleep(1)

    apply_camera_settings(cap)

    if not cap.isOpened():
        print("ERROR: Camera not found.")
        return None

    return cap


def get_face_detector():
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    detector = cv2.CascadeClassifier(cascade_path)

    if detector.empty():
        print("ERROR: Could not load face detector.")
        return None

    return detector


def load_recognizer():
    if not os.path.exists(MODEL_FILE):
        print("ERROR: Face model not found:", MODEL_FILE)
        print("Run face_train.py first and train the model.")
        return None

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(MODEL_FILE)

    return recognizer


def find_selected_person(person_name, confidence_limit=80):
    cap = open_camera()
    if cap is None:
        return None

    detector = get_face_detector()
    if detector is None:
        cap.release()
        return None

    recognizer = load_recognizer()
    if recognizer is None:
        cap.release()
        return None

    print(f"Looking for {person_name}...")
    print("Press Q in camera window to cancel.")

    result = None

    for _ in range(80):
        ret, frame = cap.read()

        if not ret or frame is None:
            print("Camera read failed. Retrying...")
            time.sleep(0.2)
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 50)
        )

        display = frame.copy()

        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (200, 200))

            label, confidence = recognizer.predict(face_img)
            detected_name = PEOPLE.get(label, "Unknown")

            if confidence > confidence_limit:
                detected_name = "Unknown"

            cx = x + w // 2
            cy = y + h // 2

            cv2.rectangle(display, (x, y), (x+w, y+h), (255, 255, 255), 2)
            cv2.circle(display, (cx, cy), 5, (255, 255, 255), -1)

            cv2.putText(display, f"{detected_name} conf={confidence:.1f}",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 255, 255),
                        2)

            cv2.putText(display, f"X={cx} Y={cy}",
                        (x, y + h + 25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2)

            print(f"Detected: {detected_name} X={cx} Y={cy} confidence={confidence:.1f}")

            if detected_name.lower() == person_name.lower():
                result = (cx, cy, w, h, confidence)
                break

        cv2.imshow("6DOF Face Pickup Vision", display)

        key = cv2.waitKey(100) & 0xFF
        if key == ord("q"):
            break

        if result:
            break

    cap.release()
    cv2.destroyAllWindows()

    return result


def pickup_person(arm, current_pos, person_name):
    print()
    print("Moving to Vision Home...")
    current_pos = move_slow(arm, current_pos, VISION_HOME)
    time.sleep(1)

    found = find_selected_person(person_name)

    if not found:
        print(f"{person_name} not found.")
        return current_pos

    x, y, w, h, confidence = found

    print(f"{person_name} found at X={x}, Y={y}, W={w}, H={h}, confidence={confidence:.1f}")

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

    print("Move above selected face block...")
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

    print("Ready for next command.")
    return current_pos


def check_face_camera():
    cap = open_camera()
    if cap is None:
        return

    detector = get_face_detector()
    if detector is None:
        cap.release()
        return

    recognizer = load_recognizer()
    if recognizer is None:
        cap.release()
        return

    print()
    print("Face camera check running.")
    print("Press Q in camera window to quit.")

    while True:
        ret, frame = cap.read()

        if not ret or frame is None:
            print("Camera read failed. Retrying...")
            time.sleep(0.2)
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        faces = detector.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(50, 50)
        )

        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]
            face_img = cv2.resize(face_img, (200, 200))

            label, confidence = recognizer.predict(face_img)
            name = PEOPLE.get(label, "Unknown")

            if confidence > 80:
                name = "Unknown"

            cx = x + w // 2
            cy = y + h // 2

            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 255, 255), 2)
            cv2.circle(frame, (cx, cy), 5, (255, 255, 255), -1)

            cv2.putText(frame, f"{name} conf={confidence:.1f}",
                        (x, y - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 255, 255),
                        2)

            cv2.putText(frame, f"X={cx} Y={cy}",
                        (x, y + h + 25),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.7,
                        (255, 255, 255),
                        2)

            print(f"{name:<8} X={cx:>4} Y={cy:>4} W={w:>4} H={h:>4} CONF={confidence:.1f}")

        cv2.imshow("Face Camera Check", frame)

        key = cv2.waitKey(150) & 0xFF
        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


def main():
    load_camera_settings()
    load_calibration()
    load_vision_home()
    show_calibration()

    print("Opening arm port...")
    arm = serial.Serial(ARM_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)

    current_pos = VISION_HOME[:]

    print("Sending Vision Home...")
    send_to_arm(arm, VISION_HOME)
    time.sleep(2)

    while True:
        print()
        print("===== 6DOF FACE PICKUP MENU =====")
        print("P = Pick PAM")
        print("J = Pick JAY")
        print("C = Check face camera / recognition")
        print("K = Update face calibration points")
        print("M = Adjust camera settings")
        print("S = Show current calibration")
        print("H = Move to Vision Home")
        print("V = Set Vision Home")
        print("Q = Quit")

        choice = input("Select option: ").strip().lower()

        if choice == "p":
            current_pos = pickup_person(arm, current_pos, "Pam")

        elif choice == "j":
            current_pos = pickup_person(arm, current_pos, "Jay")

        elif choice == "c":
            current_pos = move_slow(arm, current_pos, VISION_HOME)
            time.sleep(1)
            check_face_camera()

        elif choice == "k":
            update_calibration_from_menu()

        elif choice == "m":
            camera_adjust_menu()

        elif choice == "s":
            show_calibration()

        elif choice == "h":
            current_pos = move_slow(arm, current_pos, VISION_HOME)

        elif choice == "v":
            set_vision_home_from_menu()
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
