# Safety Architecture

Ultron_V0.3 has **three independent safety layers**. They are ordered by
response time and each works even if the layers above it fail.

| Layer | Response | Trigger | Action |
|---|---|---|---|
| 1 — Hardware (Arduino ISR) | < 5 ms | Physical E-stop button | Zero PWM, drop EN pins, latch fault |
| 2 — Embedded (MCU) | 500 ms | Lost heartbeat / no cmd_vel / overcurrent / battery / encoder | Zero velocity, set fault |
| 3 — Edge (Jetson safety_node) | ~55 ms | Obstacle in STOP/SLOW zone, stale sensors | Filter `/safe_cmd_vel` |

## Watchdogs

- **Heartbeat**: safety_node → `/ultron/heartbeat` at 10 Hz → Arduino; 500 ms
  without it → motors stop.
- **cmd_vel watchdog**: no fresh velocity command for 500 ms → motors stop.
- **Hardware WDT**: 8 s → Arduino resets only if the firmware itself hangs.

## E-stop

- Hardware latched: pressing it sets a fault and disables the motor drivers at
  the port-register level (no code can move the wheels).
- Recovery is **two-step and deliberate**: release the button, then publish
  `/ultron/clear_faults`. Motors only resume on a fresh valid `/safe_cmd_vel`.

## Safety zones (safety_node)

- STOP ≤ 0.35 m → zero velocity
- SLOW 0.35–0.70 m → velocity scaled linearly
- LiDAR governs below 1.0 m; Kinect contributes 1.0–3.0 m only
- Stale LiDAR > 1.0 s → stop; stale Kinect → degrade to LiDAR-only

## Speed limits

- Teleop clamp: 0.45 m/s (firmware + serial_node)
- Autonomous (Nav2): 0.35 m/s — keeps the stop margin positive (~23 mm)

## Network independence

The critical safety path is entirely local. If the laptop or network dies,
Nav2 stops publishing `/cmd_vel`, the Arduino cmd_vel watchdog fires within
500 ms, and the robot stops. The robot never resumes autonomously after a
network drop without human re-authorization.

## Testing (must pass before any field use)

See the Bible §13: E-stop test incl. release+clear, heartbeat timeout test,
overcurrent test, LiDAR disconnect test, battery-critical test, encoder fault
test. Add the closed-loop velocity check once P0/P1 land.

## Known margin to watch

The autonomous stop margin is thin (~23 mm) and depends on open-loop speed
accuracy. Verify at minimum battery voltage after the velocity-control work.
