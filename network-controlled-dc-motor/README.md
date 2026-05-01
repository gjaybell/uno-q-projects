
<img width="1386" height="922" alt="image" src="https://github.com/user-attachments/assets/203aff0a-2bf9-44c5-9770-63c6cd111831" />

# Network Controlled DC Motor (UNO Q + Python + PC Server)

![System Diagram](./system-diagram.png)

This project demonstrates how to control a DC motor over a local network using:

* A **PC-based Python web server**
* An **Arduino UNO Q running App Lab (Python + Arduino sketch)**
* A **TA6586 motor driver**
* A standard **DC motor**

The system allows you to control the motor from a web browser using simple commands: **Forward**, **Reverse**, and **Stop**.

---

## 🧠 How It Works

```text
Browser → PC Python Server → UNO Q Python → Bridge → Arduino Sketch → Motor
```

* The **browser** sends commands (Forward/Reverse/Stop)
* The **PC server** hosts the control interface
* The **UNO Q Python program** polls the server for commands
* The **Bridge** passes commands to the Arduino sketch
* The **Arduino sketch** drives the motor

---

## 📁 Project Structure

```text
network-controlled-dc-motor/
│
├── pc/
│   └── motor_server.py
│
├── python/
│   └── main.py
│
├── sketch/
│   └── sketch.ino
│
└── README.md
```

---

## 🔌 Hardware Setup

Connections:

* UNO Q D3 → TA6586 IN1

* UNO Q D5 → TA6586 IN2

* Battery + → TA6586 V+

* Battery – → TA6586 GND

* UNO Q GND → TA6586 GND

Motor connects to TA6586 output terminals.

### ⚠️ Important

Do **not** connect the motor directly to the battery.
Always use the motor driver.

### 🔋 Stability

Add a capacitor across motor power:

* 100µF–470µF electrolytic
* * → V+
* – → GND

---

## 💻 PC Setup (Control Server)

1. Open Command Prompt / Terminal
2. Navigate to the `pc` folder
3. Run:

```bash
python motor_server.py
```

You should see:

```text
Control server running on port 5000
```

---

## 🧠 UNO Q Setup

### 1. Arduino Sketch

Load:

```text
sketch/sketch.ino
```

Make sure it includes:

```cpp
Bridge.begin();
Bridge.provide_safe("set_motor", set_motor);
```

---

### 2. Python (App Lab)

Load:

```text
python/main.py
```

Update this line with your PC IP:

```python
URL = "http://<PC-IP>:5000/cmd"
```

Example:

```python
URL = "http://192.168.1.242:5000/cmd"
```

Click **Run** in App Lab.

---

## 🌐 Using the System

Open a browser on any device on the same network:

```text
http://<PC-IP>:5000
```

Example:

```text
http://192.168.1.242:5000
```

Click:

* Forward
* Reverse
* Stop

The motor should respond immediately.

---

## ⚠️ Important Notes

* Use **http://**, not **https://**
* PC and UNO Q must be on the **same network**
* Ensure all grounds are connected

---

## 🔧 Troubleshooting

### Motor does not move

* Verify Arduino sketch is loaded
* Confirm Bridge is initialized
* Test motor directly in `setup()`

---

### Server works but motor does not respond

Check App Lab console for:

```text
Received: forward
```

If missing:

* UNO Q is not polling correctly
* Check IP address

---

### Browser cannot connect

* Verify correct IP address
* Ensure server is running
* Use `http://`

---

## 💡 Learning Goals

* Network-based control
* Python + embedded integration
* System-level debugging
* Hardware/software interaction

---

## 🚀 Next Steps

* Add speed control (PWM)
* Improve UI (mobile-friendly)
* Expand to multiple devices

---

## 📌 Summary

This project demonstrates how a simple web interface can control physical hardware, forming the foundation for IoT-style systems.
