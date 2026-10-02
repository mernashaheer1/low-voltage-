#!/usr/bin/env python3
"""Telemetry SUBSCRIBER - receives packets, parses them into variables, prints them
clearly and logs every packet to a CSV file. Also detects stale data / lost packets.

Run:  python subscriber.py           (listens on 0.0.0.0:5005, writes telemetry_log.csv)
"""
import argparse, csv, json, socket, time

FAULT_NAMES = {0: "NONE", 1: "CAN_TIMEOUT", 2: "LOW_LV_BATTERY", 3: "OVER_TEMP", 4: "THROTTLE_INVALID"}
STALE_AFTER_S = 0.5      # 5 missed packets at 10 Hz -> data considered stale

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=5005)
    ap.add_argument("--csv", default="telemetry_log.csv")
    ap.add_argument("--count", type=int, default=0, help="stop after N packets (0 = forever)")
    a = ap.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("0.0.0.0", a.port))
    sock.settimeout(STALE_AFTER_S)

    header = ["pc_time", "seq", "speed_kmh", "lv_voltage_v", "soc_pct",
              "motor_current_a", "fault_code", "fault_name"]
    last_seq, lost, n = None, 0, 0
    print(f"Listening on UDP port {a.port}, logging to {a.csv}  (Ctrl+C to stop)")
    print(f"{'seq':>5} | {'speed km/h':>10} | {'LV V':>6} | {'SOC %':>6} | {'I motor A':>9} | fault")
    with open(a.csv, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        try:
            while a.count == 0 or n < a.count:
                try:
                    data, _ = sock.recvfrom(1024)
                except socket.timeout:
                    print("   !! NO DATA for >0.5 s - values are STALE !!")
                    continue
                try:
                    pkt = json.loads(data.decode())
                    seq = int(pkt["seq"])                      # ---- parse into separate variables ----
                    speed = float(pkt["speed_kmh"])
                    lv_v = float(pkt["lv_voltage_v"])
                    soc = float(pkt["soc_pct"])
                    i_motor = float(pkt["motor_current_a"])
                    fault = int(pkt["fault"])
                except (ValueError, KeyError, json.JSONDecodeError):
                    print("   !! bad packet ignored")          # never crash on corrupted data
                    continue

                if last_seq is not None and seq != last_seq + 1:
                    lost += max(0, seq - last_seq - 1)
                    print(f"   !! lost {seq - last_seq - 1} packet(s) (total {lost})")
                last_seq = seq

                fname = FAULT_NAMES.get(fault, "UNKNOWN")
                print(f"{seq:5d} | {speed:10.1f} | {lv_v:6.2f} | {soc:6.1f} | {i_motor:9.1f} | {fname}")
                w.writerow([f"{time.time():.3f}", seq, speed, lv_v, soc, i_motor, fault, fname])
                f.flush()                                      # data safe even if power is lost
                n += 1
        except KeyboardInterrupt:
            pass
    print(f"Done: {n} packets logged, {lost} lost")

if __name__ == "__main__":
    main()
