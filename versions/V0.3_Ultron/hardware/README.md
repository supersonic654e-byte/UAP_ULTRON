# V0.3 — Hardware Base

> Maintained by **Sadnan Sajid355** (hardware base).
> Reviewed: 2026-08-08. Authoritative detail: `implementation_bible.md` §2.

This is the hardware foundation the robot is built on. It is deliberately
conservative: proven parts, safe margins, and a layout that can be swapped
piece-by-piece toward the deployment version.

## Base layout

```
┌──────────────────────────────────────────────────┐
│  top deck:  RPLiDAR A1M8 (center-forward, ~120 mm)│
│  mid deck:  Jetson Nano + Orico hub + SSD         │
│  front:     Kinect 1414 (-10° tilt, 300 mm)       │
│  base board:  Arduino Mega + IBT-2 (x2) + buck    │
│  under:     DK-37R motors + 3S LiPo               │
│  chassis:   457.2 × 304.8 mm wood board, 25.4 mm  │
│             ground clearance                      │
└──────────────────────────────────────────────────┘
```

## Compute & power

- **Jetson Nano 4 GB** on the 5 V buck (barrel jack, ≥4 A); headless mode.
- **3S 2200 mAh LiPo** → 15 A fuse → Schottky → 12 V rail → IBT-2s + buck.
- ADC divider for battery (10 k / 3.9 k), ACS712-30A per motor for current.

## Motion

- 2× DK-37R (18.75:1) motors, 2× IBT-2 (BTS7960) two-PWM drive @ 20 kHz.
- Quadrature encoders: left D18/D19 (INT3/INT2), right D52/D51 (PCINT0).

## Sensors

| Sensor | Role | Bus |
|---|---|---|
| RPLiDAR A1M8 | LiDAR /scan | USB (CP210x) |
| Kinect 1414 | depth → /kinect/scan | USB2 direct port |
| MPU6050 | IMU | I2C (0x68) |
| ACS712 ×2 | motor current | ADC A1/A2 |
| battery divider | voltage | ADC A0 |

## Wiring rules we follow

1. Motors never powered from the 5 V rail.
2. Kinect on a **direct** USB port (never the shared hub).
3. All grounds common; encoder pullups 4.7 kΩ to 5 V.
4. E-stop on D2/INT4, active-low, port-register handling.
5. 15 A fuse on battery positive; software 7 A/motor trip fires first.

## Upgrade seams (hardware base → InsightV1.0)

The base is laid out so each swap is contained:

- Jetson Nano → **Orin Nano Super** (same power rail concept, re-sized buck).
- Kinect → **RealSense D455** (same `/kinect/scan` interface, camera_info-driven).
- Mega + IBT-2 → **Arduino Nano + MCP2515 CAN + AS5048B** (same ROS interface,
  new `ultron_can_node`).
- 3S 2200 mAh → larger pack + power redesign (runtime is the hard ceiling).

Full matrix: `../InsightV1.0_Ultron/hardware_upgrade_spec.md`.
