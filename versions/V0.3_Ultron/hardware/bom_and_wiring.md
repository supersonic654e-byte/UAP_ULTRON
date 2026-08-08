# Ultron_V0.3 — Hardware Base: BOM, Wiring & Power

> Contributed by **Student Researcher & Technical Expert** (hardware base).
> Companion to `../implementation_bible.md` §2.1–2.2 (authoritative).

## Bill of materials (V0.3)

| ID | Component | Qty | Spec |
|---|---|---|---|
| C1 | Jetson Nano Dev Kit | 1 | 4 GB, Tegra X1, 4×USB3, GbE |
| C2 | Arduino Mega 2560 R3 | 1 | GENUINE, ATmega16U2 (VID 2341) |
| C3 | Laptop / workstation | 1 | Ubuntu 22.04 (Nav2 + data sink) |
| C4 | microSD 64 GB | 1 | OS + kernel only |
| C5 | NVMe 128 GB + USB enclosure | 1 | /mnt/ssd (Docker + workspace) |
| C6 | Orico 7-port hub | 1 | 12 V/30 W powered |
| C7 | TL-WN727N WiFi dongle | 1 | USB2, power_save OFF |
| M1 | DK-37R gearmotor + encoder | 2 | 12 V, 18.75:1, 825 t/rev |
| D1 | IBT-2 (BTS7960) driver | 2 | two-PWM, 6–27 V |
| S1 | MPU6050 IMU | 1 | I2C 0x68 |
| S2 | RPLiDAR A1M8 | 1 | 5.5 Hz, 12 m, CP210x |
| S3 | Kinect 1414 | 1 | depth 640×480 → ROI |
| S4 | ACS712-30A | 2 | in series per motor |
| P1 | 3S LiPo 2200 mAh | 1 | 11.1 V nom, ≥20C |
| P2 | Buck 12 V→5 V | 1 | ≥5 A |
| P3 | 15 A fuse + holder | 1 | battery positive |
| P4 | Schottky >15 A | 1 | reverse polarity |
| P5 | 100 µF electrolytic | 2 | across each IBT-2 |
| R1–R3 | Resistors 4.7k/1k/330 | per §2.1 | pullups, driver logic, LEDs |
| X1–X6 | E-stop, LEDs, cables | 1 each | per §2.1 |

## Wiring summary (high level)

```
12 V rail (after fuse+Schottky)
   ├─ IBT-2 L  B+ ── ACS712 ── left motor
   ├─ IBT-2 R  B+ ── ACS712 ── right motor
   ├─ Kinect 1414 12 V input
   └─ Buck 12→5 V ──┬─ Arduino Vin
                    └─ Jetson barrel jack (≥4 A)
```

Arduino pin groups (see the Bible §2.2 for the full table):

- E-stop: D2 (INT4, active-low, port-register ISR).
- Left encoders: D18/D19 (INT3/INT2, change mode).
- Right encoders: D52/D51 (PCINT0, Port B) — fixed in B1.
- Motor PWM: Timer4 (D6/D7) left, Timer3 (D5/D3) right, EN D4/D8.
- I2C: D20/D21 + 4.7k pullups. IMU int: D22.
- ADC: A0 battery divider, A1/A2 ACS712 left/right.

## Power budget (typical)

| Load | W |
|---|---|
| motors (1.5 A each @12 V) | 36 |
| Jetson Nano (5 V @3 A) | 15 |
| Kinect | 12 |
| Arduino + RPLiDAR + misc | 5–7 |
| **total** | **~70 W** |

→ 24.4 Wh pack, ~80 % usable → **~15–20 min runtime**. Missions ≤ 12 min.
This is the platform's hard ceiling; the InsightV1.0 power redesign fixes it.

## Upgrade seams (hardware base → InsightV1.0)

Every swap is contained behind an interface:

1. Compute: Jetson Nano → Orin Nano Super (same containers).
2. Depth: Kinect → RealSense D455 (camera_info-driven depth→scan).
3. Motion bus: Mega + IBT-2 → Arduino Nano + MCP2515 CAN + AS5048B
   (`ultron_can_node`).
4. IMU: MPU6050 → BNO085 (new packet type, fused orientation).
5. LiDAR: A1M8 → A2M12 (config change; re-derive stop margins).
6. Storage: USB NVMe → M.2 NVMe (same mount layout).
7. Net: TL-WN727N → AX210 (needs Orin kernel).
8. Power: bigger pack + re-sized buck + enclosure.

Full matrix: `../../InsightV1.0_Ultron/hardware_upgrade_spec.md`.
