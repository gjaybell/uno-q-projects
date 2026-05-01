# Network-Controlled DC Motor (Slider)

Control a DC motor over your local network using a web-based slider.
This project upgrades button-based control to smooth, variable speed and direction using values from **−255 to +255**.

---

## 📸 System Diagram



---

## 🧠 Overview

This project uses three software layers:

1. **PC Python Server (UI)**
   Hosts a web page with a slider and sends speed values

2. **UNO Q Python (Logic Layer)**
   Polls the server and forwards values via Bridge

3. **Arduino Sketch (Hardware Control)**
   Drives the motor using PWM through a TA6586 motor driver

---

## 🔁 System Flow

```text
Browser → PC Server → UNO Q (Python) → Bridge → Arduino → Motor
```

---

## ⚙️ Features

* Real-time motor control
* Variable speed (−255 to +255)
* Forward and reverse direction
* Web-based interface (no app required)
* Simple, expandable architecture

---

## 🔌 Hardware Setup

### Connections

* UNO Q D3 → TA6586 IN1

* UNO Q D5 → TA6586 IN2

* Battery + → TA6586 V+

* Battery − → TA6586 GND

* UNO Q GND → TA6586 GND

* Motor → TA6586 outputs

---

### Stability (Recommended)

Add a capacitor across motor power:

* 100µF–470µF electrolytic
* * → V+
* − → GND

---

### ⚠️ Important

Do NOT connect the motor directly to the battery.
Always use the motor driver.

---

## 💻 Software Setup

### 1. PC Server (`pc/motor_server.py`)

Run:

```bash
python motor_server.py
```

Open in browser:

```text
http://<PC-IP>:5000
```

---

### 2. UNO Q Python (`python/main.py`)

Update the server address:

```python
URL = "http://<PC-IP>:5000/cmd"
```

Run the project in App Lab.

---

### 3. Arduino Sketch (`sketch/sketch.ino`)

Upload the sketch and ensure:

```cpp
Bridge.begin();
Bridge.provide_safe("set_motor", set_motor);
```

---

## ▶️ Usage

1. Start the PC server
2. Run the UNO Q App Lab project
3. Open the browser interface
4. Move the slider

The motor will respond instantly.

---

## 🧪 How It Works

* Slider sends:

  ```text
  /set?speed=value
  ```
* UNO Q reads:

  ```text
  /cmd
  ```
* Value is sent to:

  ```cpp
  set_motor(speed)
  ```

---

## 🔧 Tips

* Add a dead zone to prevent jitter:

  ```cpp
  if (abs(speed) < 20) speed = 0;
  ```

* Adjust slider responsiveness in JavaScript delay (50–150 ms)

---

## 🐞 Troubleshooting

### No connection

* Check IP address
* Ensure same network
* Use `http://` (not https)

### Motor not moving

* Verify wiring
* Confirm Arduino sketch is loaded

### Slider works but motor is jumpy

* Increase delay
* Add dead zone

---

## 🚀 Next Steps

* Add dual motor control (tank drive)
* Improve mobile UI
* Add acceleration smoothing
* Control servos or other devices

---

## 📘 Related

* Project 1: Button-based motor control
* Project 2: Slider-based variable control (this project)

---

## 📌 Summary

This project demonstrates how to build a simple network-controlled system that bridges web interfaces, Python logic, and embedded hardware control.

---

**Author:** George J. Bell
