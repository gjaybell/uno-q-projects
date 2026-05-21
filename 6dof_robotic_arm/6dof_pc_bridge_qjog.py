import serial
import time
 
CONTROLLER_PORT = "COM8"
ARM_PORT = "COM4"
BAUD_RATE = 115200
 
# Final arm output safety limits based on your calibration chart
SAFE_LOW  = [0, 40, 0, 70, 0, 70]
SAFE_HIGH = [170, 130, 85, 180, 180, 120]
HOME_POS  = [75, 85, 42, 125, 90, 97]
 
# --- Jog tuning ---
# How many degrees per loop iteration a joystick moves the servo at full deflection
JOG_SPEED = 1.0
 
# Joystick dead zone: raw values within this range of center (0) are treated as idle
JOG_DEADZONE = 15
 
# Joystick raw input range coming from your controller for JS1-JS4
JS_MIN = -90
JS_MAX = 89      # center is ~0, full deflection reported as +/-90
 
last_sent = None
 
# Current jog positions for S1–S4 (indices 1–4)
# S0 (base) and S5 (claw) stay on direct/piecewise mapping
jog_pos = [
    float(HOME_POS[1]),   # S1
    float(HOME_POS[2]),   # S2
    float(HOME_POS[3]),   # S3
    float(HOME_POS[4]),   # S4
]
 
 
def clamp(value, low, high):
    return max(low, min(high, value))
 
 
def map_range(x, in_min, in_max, out_min, out_max):
    return int((x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min)
 
 
def map_piecewise(x, in_a, out_a, in_b, out_b, in_c, out_c):
    if x <= in_b:
        return map_range(x, in_a, in_b, out_a, out_b)
    else:
        return map_range(x, in_b, in_c, out_b, out_c)
 
 
def clamp_positions(values):
    return [
        clamp(values[i], SAFE_LOW[i], SAFE_HIGH[i])
        for i in range(6)
    ]
 
 
def send_to_arm(arm, values):
    global last_sent
    values = clamp_positions(values)
    if values == last_sent:
        return
    command = ",".join(str(v) for v in values)
    arm.write((command + "\n").encode())
    print("Sent to arm:", command)
    last_sent = values.copy()
 
 
def js_to_jog_delta(raw_value):
    """
    Convert a raw joystick value to a jog delta (degrees per loop tick).
    - Values inside the dead zone produce 0 movement.
    - Outside the dead zone, delta scales linearly with deflection magnitude.
    - Positive raw  → positive delta (increase servo angle)
    - Negative raw  → negative delta (decrease servo angle)
    """
    if abs(raw_value) <= JOG_DEADZONE:
        return 0.0
 
    # Normalise deflection to 0.0–1.0 outside dead zone
    if raw_value > 0:
        normalised = (raw_value - JOG_DEADZONE) / (JS_MAX - JOG_DEADZONE)
        return JOG_SPEED * normalised
    else:
        normalised = (raw_value + JOG_DEADZONE) / (JS_MIN + JOG_DEADZONE)
        return -JOG_SPEED * normalised
 
 
def main():
    global jog_pos
 
    print("Starting 6DOF PC Bridge (with jog on S1–S4)...")
    print("Controller:", CONTROLLER_PORT)
    print("Arm:", ARM_PORT)
    print(f"Jog speed: {JOG_SPEED} deg/tick  |  Dead zone: ±{JOG_DEADZONE}")
 
    controller = serial.Serial(CONTROLLER_PORT, BAUD_RATE, timeout=1)
    arm = serial.Serial(ARM_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
 
    print("Sending HOME position...")
    send_to_arm(arm, HOME_POS)
    print("Bridge running.")
    print("JS1/JS2/JS3/JS4 now jog S1/S2/S3/S4 incrementally.")
    print("PS0 still directly controls S0 (base); PS5 still directly controls S5 (claw).")
    print("Press Ctrl+C to stop.")
 
    while True:
        try:
            line = controller.readline().decode(errors="ignore").strip()
            if not line:
                continue
 
            parts = line.split(",")
            if len(parts) != 6:
                print("Ignored bad line:", line)
                continue
 
            raw = [int(p) for p in parts]
 
            # Controller raw order:
            # raw[0] = JS1  → jog S1
            # raw[1] = JS2  → jog S2
            # raw[2] = JS3  → jog S3
            # raw[3] = JS4  → jog S4
            # raw[4] = PS0  → direct S0 (base)
            # raw[5] = PS5  → direct S5 (claw)
 
            # --- Update jog positions for S1–S4 ---
            js_axes = [raw[0], raw[1], raw[2], raw[3]]
            servo_limits = [(1, SAFE_LOW[1], SAFE_HIGH[1]),   # S1
                            (2, SAFE_LOW[2], SAFE_HIGH[2]),   # S2
                            (3, SAFE_LOW[3], SAFE_HIGH[3]),   # S3
                            (4, SAFE_LOW[4], SAFE_HIGH[4])]   # S4
 
            for i, (servo_idx, lo, hi) in enumerate(servo_limits):
                delta = js_to_jog_delta(js_axes[i])
                jog_pos[i] = clamp(jog_pos[i] + delta, lo, hi)
 
            # --- Direct mapping for S0 (base) and S5 (claw) ---
            s0 = map_piecewise(raw[4], 0, 170, 91, 75, 178, 0)
            s5 = map_piecewise(raw[5], 0, 70, 96, 97, 179, 120)
 
            values = [
                s0,
                int(round(jog_pos[0])),   # S1
                int(round(jog_pos[1])),   # S2
                int(round(jog_pos[2])),   # S3
                int(round(jog_pos[3])),   # S4
                s5,
            ]
 
            safe_values = clamp_positions(values)
            print(
                f"Raw: {raw} | "
                f"Jog: S1={jog_pos[0]:.1f} S2={jog_pos[1]:.1f} "
                f"S3={jog_pos[2]:.1f} S4={jog_pos[3]:.1f} | "
                f"Safe: {safe_values}"
            )
            send_to_arm(arm, safe_values)
 
        except KeyboardInterrupt:
            print("\nStopping bridge. Returning to HOME.")
            send_to_arm(arm, HOME_POS)
            time.sleep(1)
            break
        except Exception as e:
            print("Error:", e)
 
 
if __name__ == "__main__":
    main()
