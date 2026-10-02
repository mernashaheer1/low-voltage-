#!/usr/bin/env python3
"""Fake vehicle telemetry PUBLISHER - sends one JSON packet over UDP at 10 Hz.

Run:  python publisher.py            (sends to 127.0.0.1:5005)
"""
import argparse, json, math, random, socket, time

FAULT_NAMES = {0: "NONE", 1: "CAN_TIMEOUT", 2: "LOW_LV_BATTERY", 3: "OVER_TEMP", 4: "THROTTLE_INVALID"}

def make_packet(seq, t0):
    t = time.time() - t0
    speed = 30 + 20 * math.sin(0.3 * t)                      # km/h, smooth drive cycle
    motor_current = max(0.0, 8 + 0.9 * speed + random.gauss(0, 1.0))   # A, grows with speed
    soc = max(0.0, 95 - 0.02 * t)                            # %, slow discharge
    lv_voltage = 13.6 - 0.005 * t + random.gauss(0, 0.03)    # V
    # rare fake fault, lasts ~1 s so it is easy to see in the CSV
    fault = 0
    if 20 < (t % 30) < 21: fault = 3                         # OVER_TEMP once every 30 s
    return {"seq": seq, "t": round(time.time(), 3),
            "speed_kmh": round(speed, 1), "lv_voltage_v": round(lv_voltage, 2),
            "soc_pct": round(soc, 1), "motor_current_a": round(motor_current, 1),
            "fault": fault}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=5005)
    ap.add_argument("--rate", type=float, default=10.0, help="Hz (default 10)")
    ap.add_argument("--count", type=int, default=0, help="stop after N packets (0 = forever)")
    a = ap.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    period = 1.0 / a.rate
    t0 = time.time()
    next_t = time.perf_counter()
    seq = 0
    print(f"Publishing to {a.host}:{a.port} at {a.rate} Hz  (Ctrl+C to stop)")
    try:
        while a.count == 0 or seq < a.count:
            pkt = make_packet(seq, t0)
            sock.sendto(json.dumps(pkt).encode(), (a.host, a.port))
            seq += 1
            next_t += period                                  # fixed schedule -> no drift
            time.sleep(max(0.0, next_t - time.perf_counter()))
    except KeyboardInterrupt:
        pass
    print(f"Stopped after {seq} packets")

if __name__ == "__main__":
    main()
