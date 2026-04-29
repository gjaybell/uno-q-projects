# Two-Phase: Motor Control

This project demonstrates full system control of a DC motor using the Arduino UNO Q.

It builds on the LED project and introduces real hardware control using a motor driver.

---

## What This Project Does

A Python program running on the Linux system controls a motor connected to the microcontroller.

The motor will:

- Spin forward slowly  
- Increase speed  
- Stop  
- Reverse direction  
- Stop  
- Repeat continuously  

---

## System Overview

This project uses the two-phase model:

### Phase 1 — Arduino (MCU)
The Arduino sketch directly controls the motor hardware.

### Phase 2 — Python (Linux)
The Python program sends commands to the Arduino using the Bridge.

---

## Control Flow
