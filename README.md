# LV Telemetry Demo (Low Voltage Solo Mission - Q26)

Two small Python 3 scripts (standard library only, no installs needed):

| File | Role |
|---|---|
| `publisher.py`  | Sends fake vehicle data (speed, LV voltage, SOC, motor current, fault) as JSON over UDP at **10 Hz** |
| `subscriber.py` | Receives it, parses into separate variables, prints a clean table, logs to `telemetry_log.csv`, warns on stale data / lost packets |

## Run (two terminals)
```
python subscriber.py
python publisher.py
```
Stop with Ctrl+C. Options: `--port`, `--rate`, `--csv`, `--count` (see `-h`).

## Design notes
- UDP + JSON keeps the demo simple. On the real car the same fields would come from CAN frames (see CAN table in the report).
- `seq` lets the receiver detect lost packets; a 0.5 s receive timeout flags **stale data** (same idea as the dashboard timeout in Q10).
- Fixed-schedule loop in the publisher -> no timing drift at 10 Hz.
- `firmware/` has the STM32 HAL code for Q13 (indicators) and Q14 (throttle ADC).
