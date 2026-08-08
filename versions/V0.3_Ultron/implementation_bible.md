# Ultron_V0.3 — Final Implementation Bible

*A Complete Build, Deploy, and Operations Reference.*

| Field | Value |
|---|---|
| This document | Ultron_V0.3 — final testing / pre-deployment prototype |
| Version | Ultron_V0.3 (builds on Bible v4.2 + r2/r3 fixes; |
| Date | 08 August 2026 |
| Status | Pre-Deployment Prototype (final testing) |
| Architecture | Two-Layer (Edge + Remote Compute) |
| ROS | ROS 2 Humble (inside Docker on Jetson, native on Laptop) |
| Network | Tailscale VPN + CycloneDDS (rmw_cyclonedds_cpp) |
| Storage | SD card (OS) + 128GB USB NVMe SSD (Docker + workspace) |
| Safety | Jetson Safety Node + Arduino Hardware Watchdog |
| Data | Pilot data collection (Section 17) — laptop = V0.3 "cloud" |

---

WHAT CHANGED IN v4.2 (all blockers B1-B12 + storage/hub hardening applied)
  1. (B1)  RIGHT ENCODER PIN FIX — D23/D24 (Port A) have NO pin-change interrupt
           on the ATmega2560. Right encoder now wired to D52 (PB1) / D51 (PB2)
           and the ISR reads PINB. Right-wheel odometry now works.
  2. (B2)  IBT-2/BTS7960 WIRING FIX — the old "tie RPWM=LPWM" wiring only
           braked. SUPERSEDED by v4.2r2 D1 below (native two-PWM per motor).
  3. (B3)  RMW SWITCHED Zenoh→CycloneDDS. rmw_cyclonedds_cpp ships in
           packages.ros.org for amd64 AND arm64 (no PPA, no Rust, no source
           build). One shared cyclonedds.xml with unicast Peers replaces the
           Zenoh router container and all Zenoh configs. Version-lock gone.
  4. (B4)  TF CONFLICT FIXED — serial_node publishes only /odom; the laptop
           EKF is the single publisher of odom→base_link.
   5. (B5)  FIELD-MODE CONTRADICTION FIXED — autonomous Nav2 always requires the
            laptop (the Jetson Nano has no Nav2 compute budget). "No laptop"
            field autonomy is NOT supported on Ultron_V0.3.
  6. (B6)  AUTONOMOUS SPEED CAP — Nav2 max_vel_x = 0.35 m/s (~23 mm stop margin).
           Teleop keeps the 0.45 m/s firmware clamp.
  7. (B7)  E-STOP RECOVERY ADDED — new inbound packet 0x07 CLEAR_FAULTS clears
           faults only when the E-stop button is released.
  8. (B8)  OVERCURRENT 7 A per motor (stall = 8 A → software fires before the
           15 A fuse). ACS712 series wiring documented.
  9. (B9)  SERIAL RX WINDOW raised 300→900 µs (one velocity packet per loop).
  10. (B10) GENUINE Mega 2560 R3 (ATmega16U2, cdc_acm, VID 2341) supported;
            CH340G udev rule kept as clone fallback.
  11. (B11) DOCKER BUILD MAKEFLAGS=-j2 (no OOM on 4 GB Nano).
   12. (B12) CHRONY TIME SYNC added (laptop NTP-serves the robot).
  NEW      STORAGE ARCHITECTURE — SD holds OS/kernel; Docker root + ROS
           workspace live on /mnt/ssd (mounted by UUID). Powered USB hub
           allocation documented (Kinect kept off the shared USB2 bus).
           Tailscale 1.68.2 PINNED (prevents kernel panic).

v4.2r2 — DEFECT FIXES (autonomous robot focus)
  D1 (B2)  IBT-2 now uses NATIVE TWO-PWM per motor (OC4A/OC4B left,
           OC3A/OC3C right; EN pins held high). The v4.2 "1-PWM+1-DIR"
           scheme was electrically wrong: with LPWM=1 the BTS7960 latches
           M− to B+, giving reverse with inverted duty — not clean
           bidirectional drive.
  D2 (B3)  ALL containers (Jetson onboard AND laptop Nav2/RViz2) use
           network_mode: host. CycloneDDS peer discovery is bidirectional
           unicast; Docker bridge/NAT drops the laptop's replies to the
           container, so discovery silently fails on bridge.
  D3 (B7)  STEP 6 now re-enables the motor EN pins after any fault clear.
           Previously the E-stop ISR dropped EN and nothing restored it —
           the robot stayed physically dead even after a successful clear.
  D4 (B9)  Serial RX window 900→1200 µs so a full 12-byte velocity packet
           (~1.04 ms at 115200) lands inside one loop.
  D5       Firewall rule (UDP 7400–7500) explicitly applied on BOTH machines.
  D6       Documented: a clean `docker compose restart` sends PKT_ESTOP and
           latches the E-stop; the operator must publish
           /ultron/clear_faults to resume motors.

---

## Section 0 — DOCUMENT CONTROL & META

---

### 0.1 DOCUMENT VERSION HISTORY (this implementation Bible)
```
```
| Version | Date | Summary |
|---|---|---|
| v1.0 | 2025 | Initial Implementation Bible. Single-machine ROS 2 Humble on Jetson. Arduino firmware baseline. |
| v2.0 | 2025 | Two-layer architecture. Zenoh VPN bridge. Docker containerization. Tailscale VPN. |
| v3.0 | 2026 | Full embedded system audit. ISR fixes. QoS mismatch fix. MOTOR_PWM_TOP unified. HW WDT 8s. Safety node. |
| v4.0 | 18-03-2026 | Full canonical rewrite. 16 sections. ZRAM/swap, Docker perf, deployment modes, troubleshooting. |
| v4.1 | 05-08-2026 | Corrected power budget/runtime (~15-20 min). Speed limit to 0.45 m/s. Odom twist real-dt. ADC scale 0.017418. |
| v4.2 | 05-08-2026 | B1-B12 applied. Minted for genuine Mega 2560 R3. Right-encoder PCINT fix, IBT-2 wiring fix, RMW switch to CycloneDDS, TF ownership, E-stop recovery, overcurrent 7A, serial RX 1200µs, udev for 16U2, MAKEFLAGS=-j2, chrony. SD+SSD storage + powered-hub allocation + Tailscale pin. |
| Ultron_V0.3 | 08-08-2026 | Ultron_V0.3 edition. Pre-deployment framing. Audit corrections. NEW Section 17 (data collection/ logging for the V0.3 pilot). |

### 0.2 COMPATIBILITY MATRIX
```
```
| Component | Version / Specification |
|---|---|
| Jetson Nano Host OS | Ubuntu 20.04 LTS (Focal Fossa) |
| Jetson JetPack | 4.6.2 (L4T R32.7.2) |
| Boot media (SD) | 64GB microSD (OS + kernel only) |
| Storage (SSD) | 128GB NVMe in USB enclosure @ /mnt/ssd - /mnt/ssd/docker   (Docker data-root) - /mnt/ssd/ultron (ROS workspace/config) |
| USB Hub | Orico 7-port (M3H7-V1) USB 3.0, 12V/30W powered |
| Docker CE on Jetson | Latest stable for Ubuntu 20.04 (≥ 24.x) |
| Jetson Container OS | Ubuntu 22.04 (inside ros:humble-ros-base) |
| ROS 2 (Jetson container) | Humble Hawksbill (ros-base) |
| ROS 2 (Laptop) | Humble Hawksbill (desktop-full) |
| Laptop OS | Ubuntu 22.04 LTS (Jammy Jellyfish) |
| Docker CE on Laptop | Latest stable for Ubuntu 22.04 |
| RMW (ALL nodes) | rmw_cyclonedds_cpp (Humble, amd64 + arm64) |
| Arduino Mega 2560 R3 | GENUINE (Made in Italy): ATmega2560, ATmega16U2 USB-serial, VID 2341 PID 0042/0242 |
| Arduino IDE / CLI | arduino-cli latest stable |
| libfreenect | 0.5.7-2 (Ubuntu 22.04 apt, ARM64) |
| python3-freenect | Ubuntu 22.04 apt package |
| Tailscale | 1.68.2 PINNED (auto-updates DISABLED) |
| RPLidar ROS 2 driver | ros-humble-rplidar-ros (apt binary) |
| robot_localization EKF | ros-humble-robot-localization |
| slam_toolbox | ros-humble-slam-toolbox |
| Nav2 | ros-humble-navigation2 |

### 0.3 CRITICAL CONSTRAINTS (non-negotiable)
```
SAFETY:
  STOP zone:              <= 0.35 m  (immediate zero velocity)
  SLOW zone:              0.35–0.70 m (linear interpolation, forward only)
  LiDAR priority:         < 1.0 m governs exclusively
  Kinect contribution:    1.0–3.0 m only
  Heartbeat timeout:      500 ms → motor stop
  Hardware WDT:           8 seconds → Arduino reset (firmware hang only)
  E-Stop latency:         < 5 ms (hardware ISR, direct port register)
  E-Stop recovery:        requires button RELEASE + CLEAR_FAULTS (0x07)
  MAX_SPEED_MPS:          0.45 m/s HARD LIMIT (teleop, firmware + serial_node)
  Autonomous Nav2 cap:    max_vel_x = 0.35 m/s (stop margin ≈ 23 mm)

RUNTIME (corrected; battery NOT upgraded):
  Continuous operation:   ~15–20 min per charge (3S 2200 mAh, 80% usable)
  Mission planning rule:  keep missions ≤ 12 min; recharge between missions.
  Battery critical:       10.5 V → motors stop (Arduino, hardware).
  Battery warning:        11.1 V → visible warning, plan return to base.

ROBOT DIMENSIONS:
  Base (L × W × H):       457.2 × 304.8 × 381 mm
  Ground clearance:       25.4 mm (1 inch)
  Center-of-rotation
  to front edge:          228.6 mm (0.2286 m)
  Physical safety note:   STOP zone (0.35 m) > front edge (0.229 m) ✅

DDS UNICAST (v4.2 — replaces the Zenoh version lock):
  RMW: rmw_cyclonedds_cpp on ALL nodes (amd64 + arm64 binaries).
  ROS_DOMAIN_ID = 42 on EVERY node and container.
  Both machines use the SAME cyclonedds.xml with unicast Peers (both
  Tailscale IPs). No multicast over VPN, no router required.

STORAGE:
  SD card must never hold Docker data or ROS builds (wear / boot issues).
  /mnt/ssd mounted by UUID with nofail (boot must not hang if SSD absent).
  tailscaled pinned at 1.68.2 and auto-restart enabled.

DATA & PRIVACY (V0.3 pilot — Section 17):
  Default is DATA MINIMIZATION: store anonymous motion features and derived
  data, NOT identifiable raw video, unless a consent/approval gate is met.
  All pilot data lives on the operator laptop (the V0.3 "cloud") and must be
  encrypted at rest with a defined retention/deletion policy.

```
---

## Section 1 — SYSTEM OVERVIEW

---

### 1.1 PROJECT GOAL
```
Ultron_V0.3 is an autonomous indoor mobile robot designed for navigation in
indoor flat-floor environments (corridors, rooms, mixed spaces with human
presence). It is the final testing / pre-deployment prototype of the project,
engineered as a modular, upgradeable, data-collection-enabled platform. It
operates on a two-layer architecture:

  LAYER 1 — ONBOARD EDGE LAYER (Jetson Nano + Arduino Mega):
    Handles all hardware-facing operations, sensor data acquisition,
    real-time motor control, and local safety enforcement.
    This layer must function correctly REGARDLESS of network connectivity.

  LAYER 2 — REMOTE COMPUTE LAYER (Laptop/Workstation):
    Handles all computationally expensive, non-real-time tasks:
    SLAM map building, autonomous navigation planning (Nav2),
    localization, and human supervision via RViz2.
    NOTE (B5): autonomous Nav2 REQUIRES the laptop on Ultron_V0.3.

1.2 ARCHITECTURE OVERVIEW
```
```

  ┌─────────────────────────────────────────────────────────────────┐
  │                    REMOTE COMPUTE LAYER                          │
  │                    Laptop / Ubuntu 22.04                         │
  │  ┌──────────────────┐  ┌────────────────────────────────────┐   │
  │  │  Nav2 + SLAM EKF │  │          RViz2 (monitoring)        │   │
  │  │    Container     │  │            Container               │   │
  │  └────────┬─────────┘  └─────────────────┬──────────────────┘   │
  │           └──────────────────────────────┘                       │
  │              CycloneDDS (ROS 2 middleware) over Tailscale        │
  └───────────────────────────────┬─────────────────────────────────┘
                                  │
                    Tailscale VPN (UDP 7400-7500, CycloneDDS unicast)
                                  │
  ┌───────────────────────────────┴─────────────────────────────────┐
  │                    ONBOARD EDGE LAYER                            │
  │              Jetson Nano / Ubuntu 20.04 host                     │
  │  ┌──────────────────────────────────────────────────────────┐   │
  │  │          Single Docker Container (ros:humble-ros-base)    │   │
   │  │  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │   │
   │  │  │RPLidar Node │  │ Kinect Driver│  │  Safety Node   │  │   │
   │  │  │   /scan     │  │/kinect/depth │  │/safe_cmd_vel   │  │   │
   │  │  └─────────────┘  └──────┬───────┘  └───────┬────────┘  │   │
   │  │                   ┌──────┴───────┐           │           │   │
   │  │                   │Depth→Scan    │    ┌───────┴────────┐ │   │
   │  │                   │/kinect/scan  │    │  Serial Node   │ │   │
   │  │                   └──────────────┘    │/odom /imu/data │ │   │
   │  └──────────────────────────────────────────────┬─────────┘ │   │
   └────────────────────────────────────────────────┼────────────┘
                                                    │ USB Serial
                                     ┌──────────────┴──────────────┐
                                     │   Arduino Mega 2560 R3       │
                                     │   Real-Time Control Layer    │
                                     │   Motors, Encoders, IMU,     │
                                     │   Safety Watchdog            │
                                     └─────────────────────────────┘

```
### 1.3 DATA FLOW
```
SENSOR DATA (upward):
  Encoders → Arduino → Serial → serial_node → /odom → Tailscale(DDS) → Laptop EKF
  IMU      → Arduino → Serial → serial_node → /imu/data → Tailscale → Laptop EKF
  LiDAR    → rplidar_node → /scan → Tailscale → Laptop Nav2 + Safety Node
  Kinect   → kinect_node → depth_to_scan → /kinect/scan → Safety Node

COMMAND DATA (downward):
  Laptop Nav2 → /cmd_vel → Tailscale → Safety Node
  Safety Node → /safe_cmd_vel → serial_node → Arduino → Motors
  Safety Node → /ultron/heartbeat → serial_node → Arduino watchdog
  Laptop/UI  → /ultron/clear_faults → serial_node → Arduino → clear E-stop
  Arduino → /ultron/fault → Tailscale → Laptop monitor

1.4 OPERATIONAL MODES
```
LOCAL LAB MODE:
  Both robot and laptop on same network.
  Used for: Development, tuning, SLAM map building, unit testing.
  Tailscale: Active (same account, may or may not be on same subnet).
  CycloneDDS: unicast Peers over Tailscale IPs; ROS_DOMAIN_ID=42.

REMOTE OPERATION MODE:
  Laptop and robot on different networks / internet.
  Used for: Remote supervision, teleop, monitoring.
  Tailscale: Essential — provides encrypted routed tunnel.
  Safety: Full local safety (Jetson + Arduino) operates independently.
  Acceptable command latency: < 200 ms round-trip for safe teleoperation.
  Teleop speed limit: 0.3 m/s maximum (see Section 16.2).

FIELD DEPLOYMENT MODE:
  Robot operates under supervision; Nav2 machine (laptop) is REQUIRED for
  autonomous navigation (see B5 / Section 16.3). The operator stays present
  for the whole supervised session.
  Safety: Onboard Jetson Safety Node + Arduino watchdog ONLY.
  Power: Same 3S LiPo battery. Runtime budget ~15–20 min.
  Network drop behavior: Robot stops within 500 ms (heartbeat timeout).
  Recovery: Robot waits for reconnection. Does NOT resume autonomously
            after network drop without human re-authorization.

FAILSAFE MODE (automatic, any mode):
  Triggered by: heartbeat timeout, cmd_vel timeout, LiDAR data loss,
                overcurrent (7 A/motor), battery critical, encoder fault,
                and E-stop.
  Behavior: Motors immediately commanded to zero.
  Recovery: Requires explicit human re-authorization via software.

---

## Section 2 — HARDWARE SPECIFICATION & ASSEMBLY

---

### 2.1 BILL OF MATERIALS (COMPLETE BOM)
```
```
| ID | Component | Qty | Specification |
|---|---|---|---|
| C1 | NVIDIA Jetson Nano Developer Kit 4GB | 1 | Tegra X1, Ubuntu 20.04 ARM64, 4× USB 3.0, GbE |
| C2 | Arduino Mega 2560 R3 (GENUINE, Italy) | 1 | ATmega2560, 16U2 USB-serial (cdc_acm) VID:2341 PID:0042/0242 |
| C3 | Laptop / Workstation | 1 | Ubuntu 22.04 LTS x86_64 |
| C4 | 64GB microSD (Class 10 / A1) | 1 | OS + kernel only |
| C5 | 128GB NVMe SSD + USB enclosure | 1 | /mnt/ssd (Docker+ROS) |
| C6 | Orico 7-port (M3H7-V1) USB 3.0 hub | 1 | 12V/30W external power |
| C7 | TL-WN727N WiFi USB (150Mbps) | 1 | USB 2.0; power_save OFF |
| M1 | DK-37R 37mm DC Gear Motor + Encoder | 2 | 12V, Hall-effect 11 CPR Ratio 18.75:1 TICKS_PER_REV = 825 |
| D1 | IBT-2 Motor Driver (BTS7960 H-Bridge) | 2 | 43A continuous, 6-27V |
| S1 | MPU6050 IMU Breakout Board | 1 | I2C addr 0x68 |
| S2 | RPLidar A1M8-R6 | 1 | USB-UART CP210x ~5.5 Hz, 12m range /dev/ultron_lidar |
| S3 | Microsoft Kinect Xbox 360 Model 1414 | 1 | USB 2.0, libfreenect Depth 640×480 → ROI (320×120) Tilt -10° |
| S4 | ACS712-30A Current Sensor | 2 | ±30A, 66mV/A, 2.5V@0A in series w/ each motor |
| P1 | 3S LiPo Battery | 1 | 11.1V nom, 12.6V full 10.5V critical (stop) 2200mAh, ≥ 20C Runtime ~15–20 min |
| P2 | Buck Converter 12V → 5V | 1 | ≥ 5A continuous |
| P3 | 15A Fast-Blow Fuse + Holder | 1 | Battery positive rail |
| P4 | Schottky Diode > 15A | 1 | Reverse polarity |
| P5 | 100µF Electrolytic Capacitors | 2 | Across each IBT-2 |
| R1 | 4.7kΩ Resistors | 6 | 4× encoder pullup 2× I2C pullup SDA/SCL |
| R2 | 1kΩ Resistors | 6 | Motor driver signals |
| R3 | 330Ω Resistors | 2 | LED current limiting |
| X1 | E-Stop Button (Normally Open) | 1 | D2=PE4=INT4, active low |
| X2 | Green LED (Heartbeat) | 1 | D13, 1Hz blink = alive |
| X3 | Red LED (Fault) | 1 | D12, solid = fault |
| X5 | USB-A to USB-B Cable | 1 | Arduino to Jetson |
| X6 | USB-A to Micro-USB Cable | 1 | RPLidar to Jetson |

COMPUTED CONSTANTS (confirmed, update after physical calibration):
  WHEEL_RADIUS_M   = 0.0381        (76.2mm / 2)   ← CALIBRATE
  WHEEL_SEP_M      = 0.3556        (355.6mm)       ← CALIBRATE
  TICKS_PER_REV    = 825           (11 × 4 × 18.75)
  METERS_PER_TICK  = 0.00029013    (π × 0.0762 / 825)
  MOTOR_PWM_TOP    = 99            (16MHz / (8 × 100) = 20kHz)
  MAX_SPEED_MPS    = 0.45          (teleop limit) / 0.35 (autonomous)

### 2.2 WIRING & CONNECTIONS
```
ARDUINO MEGA 2560 R3 PIN MAPPING (FINAL — v4.2, ATmega2560 verified):

```
| Arduino | ATmega2560 Port | Function | Notes |
|---|---|---|---|
| D2 | PE4 = INT4 | ESTOP_IN | Active low, falling edge ISR |
| D3 | PE5 = OC3C | RIGHT_LPWM | Timer3 rev PWM (v4.2r2 D1) |
| D4 | PG5 | LEFT_EN | HIGH=active, LOW=disabled |
| D5 | PE3 = OC3A | RIGHT_PWM | Timer3 fwd PWM, 20kHz |
| D6 | PH3 = OC4A | LEFT_PWM | Timer4 fwd PWM, 20kHz |
| D7 | PH4 = OC4B | LEFT_LPWM | Timer4 rev PWM (v4.2r2 D1) |
| D8 | PH5 | RIGHT_EN | HIGH=active, LOW=disabled |
| D12 | PB6 | FAULT_LED | Red, 330Ω series |
| D13 | PB7 | HEARTBEAT | Green, 330Ω, 1Hz blink |
| D18 | PD3 = INT3 | LEFT_ENC_A | CHANGE trigger, 4.7kΩ pullup |
| D19 | PD2 = INT2 | LEFT_ENC_B | CHANGE trigger, 4.7kΩ pullup |
| D20 | PD1 = SDA | IMU SDA | I2C only, 4.7kΩ pullup |
| D21 | PD0 = SCL | IMU SCL | I2C only, 4.7kΩ pullup |
| D22 | PA0 | IMU_INT | Data-ready from MPU6050 |
| D52 | PB1 = PCINT1 | RIGHT_ENC_A | PCIE0/PCMSK0 (v4.2 B1) |
| D51 | PB2 = PCINT2 | RIGHT_ENC_B | PCIE0/PCMSK0 (v4.2 B1) |
| A0 | PF0 = ADC0 | BATTERY_V | Divider 10kΩ/3.9kΩ |
| A1 | PF1 = ADC1 | CURRENT_L | ACS712-30A left motor (B8) |
| A2 | PF2 = ADC2 | CURRENT_R | ACS712-30A right motor (B8) |
| D0/D1 | PE0/PE1 Serial0 | USB Serial | 16U2 → /dev/ultron_ardu |

NOTE: Right encoder was D23/D24 (Port A) in v4.0/4.1 — WRONG (Port A has no
      pin-change interrupt on ATmega2560). v4.2 (B1) uses D52/D51 (Port B).
      Spare digital pins remaining for future sensors: D9, D22–D28 (Port A is
      polled-only), D23–D29 analog-capable pins, A3–A5, and the second serial
      (Serial1). No pins are pre-reserved for a removed payload.

IBT-2 MOTOR DRIVER WIRING (v4.2r2 D1 — native TWO-PWM per motor; repeat for both):
  BTS7960 is a two-PWM-input H-bridge (it has NO DIR input). Each motor uses
  TWO PWM pins (one per direction); both EN pins are held HIGH. Wire as:
| IBT-2 Terminal | Connection |
|---|---|
| RPWM (fwd) | Arduino PWM pin → 1kΩ → RPWM Left: D6 (OC4A) / Right: D5 (OC3A) |
| LPWM (rev) | Arduino PWM pin → 1kΩ → LPWM  (second channel) Left: D7 (OC4B) / Right: D3 (OC3C) |
| R_EN | Tie to Arduino 5V (HIGH) |
| L_EN | Tie to Arduino 5V (HIGH) |
| VCC (5V logic) | Arduino 5V rail |
| GND | Common system GND |
| B+ (motor power) | 12V rail (after fuse + Schottky diode) |
| B- (motor power) | System GND |
| M+ / M- | Motor terminals (swap ONCE if fwd/rev is inverted) |

WHY: The v4.2 1-PWM+1-DIR scheme (DIR→LPWM with R_EN=L_EN=1) was WRONG:
     with LPWM=1 the BTS7960 half-bridge latches M− to B+; the motor then
     only sees voltage during the PWM-OFF interval → reverse with inverted
     duty, not clean bidirectional drive. The native, correct control is
     TWO PWM inputs (v4.2r2 D1):
       forward:  RPWM = PWM, LPWM = 0   →  M+ toggles, M− = GND
       reverse:  RPWM = 0,   LPWM = PWM →  M+ = GND, M− toggles
     Direction is set by which channel is active; no DIR line, no M+/M−
     swapping needed (swap M+/M− only if a wheel runs the wrong way).
     EN pins (R_EN/L_EN) are tied HIGH; the E-stop ISR drops both EN pins
     for a hard stop and STEP 6 re-enables them after fault clear (D3).

DK-37R ENCODER WIRING (v4.2 B1):
  Red   → 12V motor positive
  Black → 12V motor negative / GND
  Blue  → Arduino 5V (encoder supply)
  White → Arduino GND
  Left wheel:
    Yellow (Ch A) → D18 (INT3) + 4.7kΩ to 5V
    Green  (Ch B) → D19 (INT2) + 4.7kΩ to 5V
  Right wheel:
    Yellow (Ch A) → D52 (PB1/PCINT1) + 4.7kΩ to 5V
    Green  (Ch B) → D51 (PB2/PCINT2) + 4.7kΩ to 5V

ACS712 CURRENT SENSOR WIRING (v4.2 B8 — in series with each motor):
  Left  motor:  ACS712 VCC=5V, GND=GND, OUT → A1 (PF1)
                I+ / I− in SERIES with the LEFT IBT-2 B+ feed (or motor lead)
  Right motor:  ACS712 VCC=5V, GND=GND, OUT → A2 (PF2)
                I+ / I− in SERIES with the RIGHT IBT-2 B+ feed
  Per-motor overcurrent threshold: 7.0 A sustained 500 ms → software E-stop.
  (Normal ~1.5 A/motor; single stall = 8 A engages the 7 A trip before the
   15 A fuse. Do NOT wire the sensors into a path that bypasses a motor.)

POWER TOPOLOGY:
  Battery(+) → Fuse(15A) → Schottky → 12V Rail

BATTERY MONITORING (voltage divider):
  12V ─── 10kΩ ─── A0 ─── 3.9kΩ ─── GND
  Scale: V_adc = V_batt × 3.9/(10+3.9) = V_batt × 0.2806
  ADC count = (V_adc / 5V) × 1023
  → V_batt = count × (5/1023) / 0.2806 = count × 0.017418
  ADC scale factor:  voltage = analogRead(A0) × 0.017418

JETSON USB PORT ALLOCATION (v4.2 — powered hub):
  USB 3.0 Port 1 (direct): Arduino Mega 2560 R3 (16U2 → ultron_arduino)
  USB 3.0 Port 2 (direct): Kinect 1414 (isochronous — KEEP OFF the hub)  [H1]
  USB 3.0 Port 3 (direct): NVMe SSD enclosure (Docker root)              [H1]
  USB 3.0 Port 4 (hub):    Orico 7-port powered hub →
                             RPLidar (CP210x), TL-WN727N WiFi, spares
  WHY (H1): the Kinect depth stream (~9 MB/s at 15 FPS ≈ 74 Mbps) + 150 Mbps
  WiFi share the hub's USB2 bus. On a shared bus they saturate → Kinect frame
  drops + WiFi/Tailscale stalls. Direct ports give the Kinect a quiet bus.
  If every device must stay on the hub, the Kinect MUST be on a hub port
  isolated from the WiFi adapter. Verify with `ros2 topic hz /kinect/...`.

### 2.3 MECHANICAL SETUP
```
CHASSIS:
  Type:             Solid wood board base (mezzanine / 2nd floor style)
  Dimensions:       457.2 mm (L) × 304.8 mm (W) × 381 mm (H)
  Ground clearance: 25.4 mm (1 inch)

SENSOR PLACEMENT:
  LiDAR (RPLidar A1M8):
    Position:        Top of chassis, center-forward
    Mount height:    ~120 mm above base board
    Orientation:     0° = forward, scan plane horizontal
    TF offset from base_link: x=0.10m, y=0.0m, z=0.12m (adjust to measure)
    Frame: laser_link

  Kinect (Model 1414):
    Position:        Front-center of chassis
    Mount height:    300 mm above floor (0.30 m)
    Tilt:            -10° (tilted downward to see floor-level obstacles)
    TF quaternion:   (x=0, y=-0.08716, z=0, w=0.99619)
                     Half-angle: y = sin(-10°/2) = sin(-5°) = -0.08716,
                     w = cos(-10°/2) = cos(-5°) = 0.99619.
    TF offset from base_link: x=0.05m, y=0.0m, z=0.30m
    Frame: kinect_depth_frame
    ROI: x=160, y=180, width=320, height=120 (87.5% pixel reduction, v4.2r3)

  IMU (MPU6050):
    Position:        Center of base board
    TF offset:       x=0.0m, y=0.0m, z=0.05m
    Frame: imu_link

MOUNTING NOTE:
  The center of rotation (differential drive pivot) is the midpoint
  between the two drive wheels. All TF offsets are measured from this
  point. Measure physically before deploying for autonomous navigation.

SAFETY MARGIN VALIDATION (v4.2 — B6 capping autonomous speed):
  Robot front edge from center:  0.2286 m
  STOP zone distance:            0.3500 m
  Clearance margin:              0.1214 m
  Worst-case stop latency:       247–280 ms (includes ~180 ms 5.5Hz LiDAR
                                 scan period + safety loop + serial + brake)

  At 0.50 m/s (OLD — UNSAFE):  0.50 × 0.28 = 0.140 m → −18.6 mm ✗
  At 0.45 m/s (teleop cap):    0.45 × 0.28 = 0.126 m → −4.6 mm  (operator supervises)
  At 0.35 m/s (AUTONOMOUS):    0.35 × 0.28 = 0.098 m → +23.4 mm ✅
  Nav2 autonomous max_vel_x = 0.35 m/s (set in nav2_params.yaml, B6).
  Teleop is capped at 0.45 m/s by firmware/serial_node (operator watches).

2.4 POWER BUDGET
```
| Component | Voltage | Current | Power |
|---|---|---|---|
| Left motor (typical) | 12V | 1.5A | 18.0 W |
| Right motor (typical) | 12V | 1.5A | 18.0 W |
| Kinect 1414 | 12V | 1.0A | 12.0 W |
| Jetson Nano | 5V | 3.0A | 15.0 W (via 5V buck) |
| Arduino Mega | 5V | 0.5A | 2.5 W (via 5V buck) |
| RPLidar A1M8 | 5V | 0.5A | 2.5 W (via 5V buck) |
| MPU6050 | 5V | 0.003A | ~0.0 W (negligible) |
| Buck converter loss | 12V | ~0.2A | ~2.2 W (@ ~90% efficiency) |
| TOTAL (typical) | 11.1V | ~6.2A | ~70 W |
| TOTAL (peak stall) | 11.1V | ~19.5A | ~217 W (both motors stalled) |

RUNTIME (corrected):
  Battery energy:  3S × 2200 mAh × 3.7V = 24.4 Wh (nominal)
  Usable:          80% — never discharge below 10.5 V → ≈ 19.5 Wh
  Runtime typical: 19.5 Wh ÷ 70 W ≈ 17 min
  →  PLAN FOR ~15–20 MINUTES CONTINUOUS OPERATION PER CHARGE.
    - Keep individual missions ≤ 12 min of run time.
    - Recharge between missions; keep spare packs charged.
    - Field mode: verify /battery/state ≥ 11.1 V before starting a mission.

FUSE RATING: 15A fast-blow on battery positive rail.
  Last-resort wiring protection. Normal motor stalls are caught first by the
  7 A-per-motor software overcurrent (B8), so the fuse should rarely blow.

OVERCURRENT FAULT (v4.2 B8): per-motor threshold 7.0 A sustained 500 ms
  → software E-stop. This triggers before the 15 A fuse under normal faults.
  (v4.0/4.1 used 20 A — two stalled motors were only 16 A, so the protection
   never fired and the fuse blew instead. Now corrected.)

---

## Section 3 — OPERATING SYSTEM SETUP (JETSON NANO)

---

### 3.1 FLASHING THE OS (SD CARD)
```
IMAGE SOURCE:
  Use the Qengineering Ubuntu 20.04 community image for Jetson Nano.
  URL: https://github.com/Qengineering/Jetson-Nano-Ubuntu-20-image

FLASH STEPS (on your LAPTOP — not the Jetson):
  lsblk                                   # identify /dev/sdX (verify size)
  xz -d JetsonNano-Ubuntu20-*.img.xz
  sudo dd if=JetsonNano-Ubuntu20-*.img of=/dev/sdX bs=4M status=progress conv=fsync
  sudo sync
  # Insert SD into Jetson, boot, complete first-time setup.

DEFAULT CREDENTIALS (change immediately):
  Username: jetson   Password: jetson

3.2 BASE SYSTEM CONFIGURATION
```
  sudo hostnamectl set-hostname ultron-v03
  sudo sed -i 's/127.0.1.1.*/127.0.1.1\tultron-v03/' /etc/hosts
  sudo timedatectl set-timezone Asia/Dhaka
  sudo locale-gen en_US.UTF-8 && sudo update-locale LANG=en_US.UTF-8
  sudo apt update && sudo apt upgrade -y
  sudo apt install -y \
      curl wget git vim htop net-tools ssh openssh-server \
      setserial minicom build-essential cmake python3-pip chrony
  sudo systemctl enable ssh && sudo systemctl start ssh

### 3.3 SYSTEM OPTIMIZATION FOR JETSON NANO
```
STEP 1: Install ZRAM (compressed in-memory swap):
  sudo apt install -y zram-config && sudo systemctl enable zram-config
  sudo systemctl start zram-config && cat /proc/swaps   # ~2GB /dev/zram0

STEP 2: Swap file (safety buffer):
  sudo fallocate -l 2G /swapfile; sudo chmod 600 /swapfile
  sudo mkswap /swapfile; sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf; sudo sysctl -p

STEP 3: Headless mode + disable unneeded services (v4.2r2 — jetson-headless-mode:
  safe, reversible user-space memory reclamation for a headless field robot).
  # Biggest win first: drop the graphical desktop target (reversible):
  #   robot boots to multi-user.target; no X/LXDE/GUI memory.
  sudo systemctl set-default multi-user.target
  # Display manager (if present, e.g. lightdm/gdm): disable it.
  sudo systemctl disable --now lightdm gdm gdm3 2>/dev/null || true
  # Optional user-space daemons not needed for this robot (all reversible):
  sudo systemctl disable --now pulseaudio 2>/dev/null || true      # audio
  sudo systemctl disable --now snapd 2>/dev/null || true           # snaps
  sudo systemctl disable --now whoopsie kerneloops 2>/dev/null || true   # crash reporters
  sudo systemctl disable --now unattended-upgrades packagekit 2>/dev/null || true
  sudo systemctl disable bluetooth cups cups-browsed avahi-daemon ModemManager
  sudo systemctl stop bluetooth cups cups-browsed avahi-daemon ModemManager 2>/dev/null || true
  # REVERT anytime with:
  #   sudo systemctl set-default graphical.target
  #   sudo systemctl enable --now <svc>

  # DO NOT disable (required on Jetson):
  #   nvargus-daemon (libargus camera), nvgetty (serial console/recovery),
  #   nvpmodel (power/clock), docker/containerd, nvfb/nvdisplay (boot display).
  # Verify what you reclaimed:  free -h  (expect more MemAvailable after reboot)

STEP 4: Power mode + low-latency serial:
  sudo nvpmodel -m 0 && sudo jetson_clocks
  cat << 'EOF' | sudo tee /etc/rc.local
  #!/bin/bash
  /usr/bin/jetson_clocks
  sleep 5
  [ -e /dev/ultron_arduino ] && setserial /dev/ultron_arduino low_latency
  [ -e /dev/ultron_lidar ]   && setserial /dev/ultron_lidar   low_latency
  exit 0
  EOF
  sudo chmod +x /etc/rc.local
  # NOTE (B10): on a genuine Mega 2560 R3 the port is /dev/ttyACM0 (cdc_acm).
  # setserial low_latency has no effect on cdc_acm and is harmless. On a
  # CH340G clone it is /dev/ttyUSB0 and low_latency DOES help.

STEP 5: Verify memory (headless, after reboot):  free -h
       # multi-user.target (STEP 3) frees GUI/desktop memory; expect
       # MemAvailable clearly above the old ~3.5G usable; Swap ~4G.

3.4 STORAGE ARCHITECTURE (v4.2 — SD + external NVMe SSD)
```
Purpose: keep the 64GB SD card for OS/kernel ONLY. Move all heavy I/O
(Docker images/containers, ROS workspace, maps, AI models) to the 128GB
NVMe SSD. This eliminates the SD wear / boot hangs and the OOM-from-full-SD
failure mode.

CREATE THE MOUNT:
  # Identify the SSD (verify it is the NVMe, NOT the SD!):
  lsblk
  # Yours shows as /dev/sda1 with ~117G (your df output confirmed).

  sudo mkfs.ext4 /dev/sda1            # once, first time
  sudo mkdir -p /mnt/ssd/docker /mnt/ssd/ultron

MOUNT BY UUID, NEVER /dev/sdaX  (USB device nodes shift when the hub
re-enumerates or a device is added → /dev/sda can become /dev/sdb):
  sudo blkid /dev/sda1                 # copy the UUID
  # add to /etc/fstab:
  UUID=<your-ssd-uuid> /mnt/ssd ext4 noatime,nofail,x-systemd.device-timeout=5 0 2
  sudo systemctl daemon-reload && sudo mount -a

MAKE DOCKER WAIT FOR THE MOUNT (prevents dockerd crash-loop at boot):
  sudo systemctl edit docker
  # add:
  [Unit]
  RequiresMountsFor=/mnt/ssd
  sudo systemctl daemon-reload

MOVE DOCKER DATA-ROOT AND ROS WORKSPACE TO THE SSD:
  # Docker (already done — verify):
  sudo tee /etc/docker/daemon.json << 'EOF'
  { "data-root": "/mnt/ssd/docker" }
  EOF
  sudo systemctl restart docker
  docker info | grep "Docker Root Dir"      # → /mnt/ssd/docker
  # ROS workspace (future builds live here):
  #   /mnt/ssd/ultron  instead of ~/ultron_jetson on the SD

VERIFY:
  df -h /mnt/ssd            # ~111G available
  # Pull power from the SSD → Jetson must still boot (nofail). Login and
  # see that docker is stopped but the system is up.

### 3.5 USB HUB & WIFI HARDENING (v4.2)
```
  # Disable WiFi powersave (TL-WN727N drops packets after sleep):
  iw dev wlan0 set power_save off
  # Prefer the Jetson's built-in Gigabit Ethernet for the DDS/Tailscale link
  # whenever tethered; WiFi is fallback for field use.
  # Pinned Tailscale — do NOT upgrade (prevents kernel panic):
  sudo apt-mark hold tailscale tailscaled     # after install of 1.68.2

3.6 STABILITY & RELIABILITY ON THE 4GB NANO (v4.2r3 — no workload increase)
```
Goal: eliminate boot issues and mid/heavy-load crashes WITHOUT adding any
load to the Nano. Crashes on a Nano under load have three root causes and
all three are fixed here by REDUCING work and hardening the platform.

ROOT CAUSE 1 — OOM killer / swap thrash (4GB RAM):
  # Larger safety net on the SSD (you have ~111GB free):
  sudo fallocate -l 4G /swapfile; sudo chmod 600 /swapfile
  sudo mkswap /swapfile; sudo swapon /swapfile
  echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
  # Keep the HOST alive: cap the container so the OOM killer eats the
  # container, never the host. Add to docker-compose.yml (ultron_onboard):
  #   deploy:
  #     resources:
  #       limits:
  #         memory: 2500M
  #   memswap_limit: 3500M
  #   healthcheck:
  #     test: ["CMD", "ros2", "node", "list"]
  #     interval: 30s
  #     timeout: 10s
  #     retries: 3
  #     start_period: 60s
  # restart: unless-stopped  (already set — restarts after an OOM kill)
  # Reduce the biggest onboard load: Kinect 15→8 FPS, ROI 320×120 (§9, §14.3).

ROOT CAUSE 2 — thermal throttling → shutdown:
  # Verify (repeat under full load for 20 min):
  cat /sys/devices/virtual/thermal/thermal_zone*/temp
  # Any zone ≥ 80°C sustained → add heatsink/fan; confirm jetson_clocks
  # persists (rc.local, §3.3 STEP 4). Do NOT run without active cooling.

ROOT CAUSE 3 — marginal 5V supply:
  # The Nano resets silently when the 5V rail sags during motor/USB surges.
  # REQUIREMENT: 5V / 4A+ quality PSU on the barrel jack (NOT micro-USB).
  # Verify with a DMM at the barrel jack while: boot + all sensors + a
  # commanded 0.45 m/s wheel burst — voltage must stay ≥ 4.9V, no brownout.

SD-CARD HYGIENE (boot reliability):
  # Keep the SD read-mostly: journal → SSD so the SD never wears/bloats:
  echo 'journald: Storage=volatile, RuntimeMaxUse=16M' | sudo tee /etc/systemd/journald.conf.d/sd-saving.conf
  sudo systemctl restart systemd-journald
  # fsck the root SD at boot:
  sudo tune2fs -c 20 /dev/mmcblk0p1     # check every 20 mounts

BOOT-STABILITY TEST (run after any change):
  1. Power cycle ×5; the JetSonn must boot to multi-user.target each time.
  2. Unplug the SSD → still boots (nofail, §3.4); docker stops, system alive.
  3. Full-load soak: docker up + SLAM/Nav2 on laptop + teleop 0.35 m/s for
     20 min → NO OOM, NO thermal shutdown, NO brownout reset.
  4. docker stats ultron_onboard — record CPU/RAM per stage (see budget).

MEASURED ONBOARD BUDGET (targets — pass/fail, v4.2r3):
  rplidar driver .......... ~2–5% CPU, ~30 MB
  serial_node ............. ~1–3% CPU, ~40 MB
  safety_node ............. ~1–3% CPU, ~40 MB
  kinect_driver (8 FPS) ... ~8–15% CPU, ~80 MB     ← biggest item; keep it lean
  depth_to_scan ........... ~1–2% CPU, ~40 MB
  TOTAL container ......... < 60% CPU, < 1500 MB   ← hard targets
  If exceeded: apply §14.3 (5 FPS / ROI 320×100) or merge nodes (§9 note).

---

## Section 4 — NETWORK SETUP

---

### 4.1 TAILSCALE INSTALLATION (pinned 1.68.2)
```
# On EACH machine (Jetson AND Laptop) independently:
curl -fsSL https://tailscale.com/install.sh | sh
# Install the PINNED version (default repo may be newer; pin to avoid the
# known kernel-panic bug on Jetson):
sudo apt install -y tailscale=1.68.2 tailscaled=1.68.2
sudo apt-mark hold tailscale tailscaled
sudo systemctl enable tailscaled --now
sudo tailscale up
# Authenticate with your Tailscale account (BOTH machines, SAME account).
tailscale ip -4
# Jetson example:  100.73.42.11   ← JETSON_TS_IP
# Laptop example:  100.73.42.22   ← LAPTOP_TS_IP

4.2 CONNECTIVITY VERIFICATION
```
tailscale ping 100.73.42.22     # from Jetson → "pong ... direct"
tailscale ping 100.73.42.11     # from Laptop → "pong ... direct"
tailscale status                # "relay" = NAT traversal failed (open UDP 41641)

### 4.3 FIREWALL CONFIGURATION  (v4.2r2 D5: run ALL of this on BOTH machines)
```
# Tailscale P2P:
sudo ufw allow 41641/udp
sudo ufw allow in on tailscale0
# CycloneDDS unicast (B3): default DDS port range — Jetson AND Laptop:
sudo ufw allow 7400:7500/udp
sudo ufw enable && sudo ufw status
# Verify after firewall changes:
tailscale ping <peer-ip>             # should show "direct"

4.4 NETWORK MODES REFERENCE
```
LOCAL LAB MODE:
  Connection:     Both on same WiFi/LAN
  Tailscale:      Active (same account), may establish direct over LAN
  Expected ping:  2–10 ms
  CycloneDDS:     unicast Peers over Tailscale IPs; ROS_DOMAIN_ID=42

REMOTE OPERATION MODE:
  Connection:     Different networks (home WiFi vs mobile hotspot etc.)
  Tailscale:      Essential for encrypted routed connection
  Expected ping:  20–100 ms (DERP relay may add 30-80 ms)
  Safe operation: Teleoperation acceptable up to ~200ms round-trip

FIELD DEPLOYMENT MODE:
  Connection:     Robot supervised; laptop present for Nav2
  Tailscale:      Active on robot for remote access
  Network drop:   Heartbeat timeout 500 ms → motors stop
  Recovery:       Human reconnects and re-authorizes via /cmd_vel

### 4.5 TIME SYNCHRONIZATION (v4.2 B12 — required for ROS TF/AMCL over the net)
```
ROS TF and AMCL are sensitive to clock skew between the Jetson and Laptop,
which over a VPN is otherwise uncontrolled.

LAPTOP (NTP server):
  sudo apt install -y chrony
  echo 'allow 100.64.0.0/10' | sudo tee -a /etc/chrony/chrony.conf
  sudo systemctl restart chrony

JETSON (NTP client → laptop):
  sudo apt install -y chrony
  # replace pool lines with:
  # server <LAPTOP_TS_IP> iburst
  sudo systemctl restart chrony

VERIFY:
  chronyc tracking    # on both; Jetson should show "Stratum 2-3", offset small

```
---

## Section 5 — DOCKER ENVIRONMENT SETUP (JETSON)

---

### 5.1 INSTALL DOCKER ON JETSON
```
sudo apt update && sudo apt install -y \
    apt-transport-https ca-certificates curl gnupg lsb-release
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | \
    sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) \
  signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo usermod -aG docker $USER
sudo systemctl enable docker && sudo systemctl start docker
# Ensure data-root is /mnt/ssd/docker (Section 3.4):
docker info | grep "Docker Root Dir"

5.2 DOCKER PERFORMANCE ANALYSIS (JETSON NANO)
```
CPU OVERHEAD: containers add <1–2% (native namespaces/cgroups, no hypervisor).
  MEASURE: docker stats ultron_onboard --no-stream
  TARGET:  CPU < 60%; if exceeded reduce Kinect FPS (8→5) or ROI (v4.2r3 §14.3).

RAM OVERHEAD: ~1.0–1.5 GB total. With ZRAM ~2GB + swap 2GB it is sufficient.
  MEASURE: free -h ; docker stats ultron_onboard

NETWORK OVERHEAD: the container uses network_mode: host (v4.2r2 D2), so the
  CycloneDDS session binds the Tailscale interface directly — no bridge
  veth/NAT hop at all. Ethernet path is 5–100ms round-trip over Tailscale
  anyway — acceptable.
  IF latency is unacceptable in future: run safety_node as a host process.

### 5.3 BASE IMAGE
```
  ros:humble-ros-base   (linux/arm64, Ubuntu 22.04 inside, host is 20.04)
  USB passthrough via --devices in docker-compose.yml.

5.4 UDEV RULES (JETSON HOST — before building container)
```
# Arduino Mega 2560 R3 GENUINE (ATmega16U2, cdc_acm) — v4.2 B10:
cat << 'EOF' | sudo tee /etc/udev/rules.d/99-ultron-v03-arduino.rules
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{idProduct}=="0042", SYMLINK+="ultron_arduino", MODE="0666"
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{idProduct}=="0242", SYMLINK+="ultron_arduino", MODE="0666"
# Clone fallback (CH340G), if you ever swap the board:
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="ultron_arduino", MODE="0666"
EOF

# RPLidar CP210x:
cat << 'EOF' | sudo tee /etc/udev/rules.d/99-ultron-v03-lidar.rules
SUBSYSTEM=="tty", ATTRS{idVendor}=="10c4", ATTRS{idProduct}=="ea60", SYMLINK+="ultron_lidar", MODE="0666"
EOF

# Kinect 1414:
cat << 'EOF' | sudo tee /etc/udev/rules.d/51-kinect.rules
SUBSYSTEM=="usb", ATTR{idVendor}=="045e", ATTR{idProduct}=="02b0", MODE="0666"
SUBSYSTEM=="usb", ATTR{idVendor}=="045e", ATTR{idProduct}=="02ad", MODE="0666"
SUBSYSTEM=="usb", ATTR{idVendor}=="045e", ATTR{idProduct}=="02ae", MODE="0666"
EOF

# CH340 serial latency — applies to CLONES only. The genuine 16U2 (cdc_acm)
# has no latency_timer; this rule is harmless on a genuine board.
cat << 'EOF' | sudo tee /etc/udev/rules.d/99-usb-serial-latency.rules
KERNEL=="ttyUSB*", ATTRS{idVendor}=="1a86", ATTR{latency_timer}="1"
EOF

sudo udevadm control --reload-rules && sudo udevadm trigger
sudo usermod -aG dialout $USER
sudo usermod -aG plugdev $USER

# Verify:
# GENUINE Mega → /dev/ttyACM0 (cdc_acm); symlink to ultron_arduino:
ls -la /dev/ultron_arduino
lsusb | grep -E "2341|1a86|10c4|045e"
#  2341 → genuine Arduino 16U2 ; 1a86 → CH340G clone

### 5.5 DOCKERFILE (v4.2 — CycloneDDS; no Zenoh, MAKEFLAGS=-j2)
```
File: /mnt/ssd/ultron/jetson/Dockerfile
```
FROM ros:humble-ros-base

# v4.2 B11: cap build parallelism so the 4GB Nano does not OOM.
ARG MAKEFLAGS=-j2

ENV DEBIAN_FRONTEND=noninteractive
ENV ROS_DISTRO=humble

RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-colcon-common-extensions \
    python3-rosdep \
    python3-serial \
    python3-numpy \
    python3-transforms3d \
    setserial \
    libfreenect-dev \
    python3-freenect \
    usbutils \
    build-essential cmake git wget curl \
    ros-humble-rplidar-ros \
    ros-humble-sensor-msgs \
    ros-humble-nav-msgs \
    ros-humble-geometry-msgs \
    ros-humble-tf2-ros \
    ros-humble-tf2-geometry-msgs \
    ros-humble-rmw-cyclonedds-cpp \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /ultron_ws
COPY src/ src/

RUN . /opt/ros/humble/setup.sh && \
    colcon build --symlink-install \
        --cmake-args -DCMAKE_BUILD_TYPE=Release \
    && rm -rf build log

COPY config/ config/
COPY launch/ launch/

# v4.2 B3: CycloneDDS over Tailscale (see Section 7).
ENV RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ENV CYCLONEDDS_URI=file:///ultron_ws/config/cyclonedds.xml
ENV ROS_DOMAIN_ID=42

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["ros2", "launch", "/ultron_ws/launch/jetson_bringup.launch.py"]
```

File: /mnt/ssd/ultron/jetson/entrypoint.sh
```
#!/bin/bash
set -e
source /opt/ros/humble/setup.bash
[ -f /ultron_ws/install/setup.bash ] && \
    source /ultron_ws/install/setup.bash
[ -e /dev/ultron_arduino ] && \
    setserial /dev/ultron_arduino low_latency 2>/dev/null || true
[ -e /dev/ultron_lidar ] && \
    setserial /dev/ultron_lidar low_latency 2>/dev/null || true
exec "$@"
```

File: /mnt/ssd/ultron/jetson/docker-compose.yml
```
version: "3.8"

services:
  ultron_onboard:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: ultron_onboard
    restart: unless-stopped
    network_mode: host           # v4.2r2 D2: REQUIRED for CycloneDDS P2P
                                 # (bridge/NAT breaks bidirectional discovery)
    devices:
      - /dev/ultron_arduino:/dev/ultron_arduino
      - /dev/ultron_lidar:/dev/ultron_lidar
      - /dev/bus/usb:/dev/bus/usb
    privileged: false
    group_add:
      - dialout
      - plugdev
    volumes:
      - /mnt/ssd/ultron/config/cyclonedds/cyclonedds.xml:\
/ultron_ws/config/cyclonedds.xml:ro
      - ultron_maps:/ultron_ws/maps
    environment:
      - RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
      - CYCLONEDDS_URI=file:///ultron_ws/config/cyclonedds.xml
      - ROS_DOMAIN_ID=42
    tmpfs:
      - /tmp

volumes:
  ultron_maps:
```

BUILD AND RUN (v4.2 B11):
  cd /mnt/ssd/ultron/jetson
  docker compose build --build-arg MAKEFLAGS=-j2   # first build 20–40 min
  docker compose up -d
  docker compose logs -f
  docker exec -it ultron_onboard bash

```
---

## Section 6 — ROS 2 ENVIRONMENT SETUP

---

### 6.1 ROS 2 HUMBLE — LAPTOP INSTALLATION (Ubuntu 22.04 native)
```
sudo apt install -y software-properties-common
sudo add-apt-repository universe -y
sudo curl -sSL \
    https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
    -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) \
    signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
    http://packages.ros.org/ros2/ubuntu \
    $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | \
    sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt install -y \
    ros-humble-desktop \
    ros-humble-navigation2 \
    ros-humble-nav2-bringup \
    ros-humble-robot-localization \
    ros-humble-slam-toolbox \
    ros-humble-rplidar-ros \
    ros-humble-rmw-cyclonedds-cpp \
    ros-humble-tf2-tools \
    ros-humble-teleop-twist-keyboard \
    ros-humble-rviz2 \
    python3-colcon-common-extensions \
    python3-rosdep
sudo rosdep init 2>/dev/null || true
rosdep update

6.2 WORKSPACE & STORAGE STRUCTURE (v4.2)
```
Both machines keep the SHARED CycloneDDS config so it is easy to keep
identical. On the Jetson, the build context lives on the SSD.

JETSON (build context on SSD):
/mnt/ssd/ultron/
```
├── jetson/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── entrypoint.sh
│   ├── config/
│   │   ├── cyclonedds.xml
│   │   └── params.yaml
│   ├── launch/
│   │   └── jetson_bringup.launch.py
│   └── src/
│       ├── ultron_onboard/
│       │   ├── package.xml
│       │   ├── setup.py
│       │   ├── setup.cfg
│       │   └── ultron_onboard/
│       │       ├── __init__.py
│       │       ├── kinect_driver_node.py
│       │       ├── depth_to_scan_node.py
│       │       ├── safety_node.py
   │       │       ├── serial_node.py        # v4.1 twist dt; v4.2 no TF, +clear
   │       │       └── data_logger_node.py   # Section 17 (pilot logging)
   ├── config/cyclonedds/cyclonedds.xml      # host copy for the container mount
└── maps/                                 # SLAM maps (persistent)

```
LAPTOP:
~/ultron_laptop/
```
├── container/
│   ├── Dockerfile            # nav2_slam + rviz2 (CycloneDDS)
│   ├── entrypoint.sh
│   ├── config/
│   │   ├── cyclonedds.xml    # SHARED — identical to Jetson
│   │   ├── nav2_params.yaml  # max_vel_x: 0.35 (B6) + amcl sensor_data_qos: 2
│   │   ├── ekf_params.yaml   # publish_tf: true; world/odom/base_link frames (B4)
│   │   └── slam_params.yaml
│   └── launch/
│       └── laptop_bringup.launch.py
└── rviz2/
    ├── Dockerfile
    ├── entrypoint.sh
    └── config/ultron.rviz

```
~/ultron_config/
```
└── cyclonedds/
    └── cyclonedds.xml        # ONE file, copied to both machines

```
NAV2 / EKF PARAMETERS (v4.2r3 — recommended starting values; tune on the bench):
  nav2_params.yaml:
    max_vel_x: 0.35        # autonomous cap (B6)
    min_vel_x: 0.0         # allow stop-in-place
    max_vel_theta: 0.5     # keep rotations modest — big yaw + 0.35 m/s can
                           # sweep the front edge into the STOP margin
    min_vel_theta: 0.0
    acc_lim_x: 0.5 ; acc_lim_y: 0.0 ; acc_lim_theta: 1.0
    inflation_radius: 0.35 # > robot radius (~0.2 m) so the costmap pads
    obstacle_layer/qos_policy_reliability: best_effort
    amcl/sensor_data_qos: 2
  ekf_params.yaml (robot_localization):
    publish_tf: true ; world_frame: odom ; odom_frame: odom
    base_link_frame: base_link
    odom0: odom ; imu0: imu/data          # fuse both
    two_d_mode: true
    # covariance guidance: odom0 pose ≈ 0.01 x/y, 0.05 yaw;
    # imu0 angular velocity ≈ 0.01. Tune from §14.2 Step-4 hz + drift tests.

### 6.3 ENVIRONMENT VARIABLES (v4.2 B3)
```
# Add to ~/.bashrc on LAPTOP:
source /opt/ros/humble/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=~/ultron_config/cyclonedds/cyclonedds.xml
export ROS_DOMAIN_ID=42

# JETSON CONTAINER: set via Dockerfile ENV + compose environment:
#   RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
#   CYCLONEDDS_URI=file:///ultron_ws/config/cyclonedds.xml
#   ROS_DOMAIN_ID=42

```
---

## Section 7 — CYCLONEDDS OVER TAILSCALE (v4.2, replaces Zenoh)

---

### 7.1 ARCHITECTURE EXPLANATION
```
Tailscale provides the encrypted network tunnel between machines.
CycloneDDS is the ROS 2 discovery + transport layer (a full DDS).

  Tailscale:  Layer 3 (IP routing, VPN transport, encryption)
  CycloneDDS: Layer 7 (application, ROS 2 message routing/discovery)

Without Tailscale: Cartesian IP routes across different networks.
Without unicast DDS Peers: default DDS multicast does NOT cross a VPN —
so we enumerate both machines as explicit unicast Peers. No extra router,
no message-broker to deploy, no version-lock (CycloneDDS is Tier-1 on
Humble for amd64 AND arm64).

7.2 THE SHARED CONFIG (identical on both machines)
```
#### ~/ultron_config/cyclonedds/cyclonedds.xml   (and on the Jetson)
```
<?xml version="1.0" encoding="UTF-8"?>
<CycloneDDS>
  <Domain id="42">
    <General>
      <AllowMulticast>false</AllowMulticast>
    </General>
    <Discovery>
      <Peers>
        <Peer address="100.73.42.22"/>   <!-- LAPTOP_TS_IP -->
        <Peer address="100.73.42.11"/>   <!-- JETSON_TS_IP -->
      </Peers>
    </Discovery>
  </Domain>
</CycloneDDS>
```
Note: replace the two IPs with your real Tailscale addresses. Keep the file
byte-identical on both the laptop and the container mount. ROS_DOMAIN_ID=42
must match the <Domain id="42">.

OFFLINE / LAN FALLBACK (v4.2r3): DDS depends on Tailscale being up (the
Peers are 100.x addresses). For a fully offline lab session (no Tailscale),
replace the two <Peer address> values with the machines' LAN IPs (e.g.
192.168.1.10 / 192.168.1.20) in BOTH copies. All other settings are
unchanged. Remember to swap back before field use.

### 7.3 NO ROUTER / NO BRIDGE NEEDED
```
- The old Zenoh router container is REMOVED (delete it from any compose).
- All three old .json5 Zenoh config files are unused (delete).
- No PPA, no Rust toolchain, no source build, no zenohd binary.
- rmw_cyclonedds_cpp installs from packages.ros.org on both platforms.
- REQUIRED (v4.2r2 D2): EVERY container — the Jetson onboard container AND
  the laptop Nav2/RViz2 containers — MUST use network_mode: host. Docker
  bridge/NAT breaks CycloneDDS bidirectional unicast discovery: the laptop's
  discovery replies to the container are dropped by the NAT, so `ros2 topic
  list` on the laptop sees nothing. With host networking the DDS session
  binds tailscale0 directly and discovery works both ways.

7.4 QoS STRATEGY
```
RULE: Publisher and subscriber reliability MUST match.
      BEST_EFFORT pub + RELIABLE sub = silent failure (no data, no error).
CycloneDDS fully supports RELIABLE and BEST_EFFORT.

| Topic | QoS | Rationale |
|---|---|---|
| /scan | BEST_EFFORT | High-freq sensor, drops OK |
| /kinect/depth/image_raw | BEST_EFFORT | High-freq, drops OK |
| /kinect/scan | BEST_EFFORT | Derived sensor |
| /odom | RELIABLE | EKF needs reliable |
| /imu/data | RELIABLE | Same reason as /odom |
| /cmd_vel | RELIABLE | Safety command |
| /safe_cmd_vel | RELIABLE | Safety command |
| /ultron/heartbeat | RELIABLE | Safety signal |
| /ultron/fault | RELIABLE | Fault signal |
| /battery/state | RELIABLE | Low-freq status |
| /ultron/clear_faults | RELIABLE | E-stop recovery (v4.2 B7) |

Nav2 /scan consumers — match the rplidar BEST_EFFORT publisher (v4.2r2):
  - obstacle_layer:     qos_policy_reliability: best_effort
  - AMCL:               sensor_data_qos: 2   (best_effort) ← REQUIRED,
                        Humble AMCL defaults to RELIABLE for /scan and
                        silently fails localization on a QoS mismatch.

EKF (robot_localization) — required parameters for correct TF ownership
(v4.2 B4): world_frame: odom, odom_frame: odom, base_link_frame: base_link,
publish_tf: true (EKF is the single publisher of odom→base_link).

### 7.5 CONNECTION TESTING
```
# Ensure both machines have CYCLONEDDS_URI + ROS_DOMAIN_ID set and reachable.
# From Laptop:
ros2 topic list
# Must show all Jetson topics: /scan, /odom, /imu/data, /kinect/scan, etc.
ros2 topic echo /odom --once    # data flows, not timeout
ros2 topic hz /odom             # ~30.0 Hz

```
---

## Section 8 — PROJECT FILE STRUCTURE (v4.2)

---

All heavy files live on the SSD (/mnt/ssd). The SD card keeps only the OS
and kernel.

JETSON — SSD:
/mnt/ssd/ultron/
```
├── jetson/                      ← Docker build context (on SSD)
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── entrypoint.sh
│   ├── config/
│   │   ├── cyclonedds.xml       ← SHARED CycloneDDS config
│   │   └── params.yaml
│   ├── launch/jetson_bringup.launch.py
│   └── src/ultron_onboard/...
├── config/cyclonedds/cyclonedds.xml   ← host copy for the container mount
└── maps/                        ← SLAM maps (persistent)

```
JETSON — SD (OS only; do NOT store Docker/ROS here):
  /home/jetson/.bashrc           ← env vars
  /home/jetson/ultron_firmware/   ← Arduino firmware (small, fine on SD)

LAPTOP:
~/ultron_laptop/
```
├── container/                   ← nav2_slam (+ EKF, SLAM, Nav2)
│   ├── Dockerfile, entrypoint.sh, config/, launch/
├── rviz2/
│   ├── Dockerfile, entrypoint.sh, config/ultron.rviz
└── docker-compose.yml
~/ultron_config/cyclonedds/cyclonedds.xml   ← shared DDS config
```

SHARED DDS CONFIG (must be identical):
  /mnt/ssd/ultron/config/cyclonedds/cyclonedds.xml   (Jetson)
  ~/ultron_config/cyclonedds/cyclonedds.xml          (Laptop)

---

## Section 9 — NODE-BY-NODE IMPLEMENTATION

---

ONBOARD PROCESS STRATEGY (v4.2r3 — REDUCE Nano load, do not add):
  The four Python nodes below are lightweight individually, but each is a
  separate process = its own Python interpreter + RMW/CycloneDDS session
  (~40–80 MB and one DDS participant each). For minimum footprint merge
  serial_node + safety_node + depth_to_scan_node into ONE process using
  `launch_ros` composition or one combined rclpy node; keep kinect_driver
  separate (its freenect thread must stay isolated). Expected saving:
  ~100–200 MB RAM and ~3 fewer DDS participants. Safety semantics are
  unchanged (single node still enforces STOP/HEARTBEAT exactly as written).
  Hard onboard targets: container CPU < 60%, RAM < 1500 MB (§3.6).

NODE 1: kinect_driver_node      (v4.2r3 — 8 FPS, ROI 320×120 to cut Nano load)
PURPOSE: Acquire depth frames from Kinect 1414, crop to ROI, publish.
TOPICS:  /kinect/depth/image_raw (BEST_EFFORT, ~8 Hz),
         /kinect/depth/camera_info (BEST_EFFORT, ~1 Hz)
PARAMS:  ROI 160,180,320,120; TARGET_FPS=8;
         Kinect FX=FY=574.0527954, CX=319.5, CY=239.5
EXPECTED: "Kinect depth stream active." ; hz ≈ 8.0
NOTE (v4.2r3): 8 FPS / 320×120 is the DEFAULT — it is the single biggest
  CPU/RAM saver on the Nano and only affects the 1–3 m mid-field fusion
  zone (LiDAR still owns <1 m). Drop to 5 FPS / 320×100 only if §3.6
  budget is exceeded.

NODE 2: depth_to_scan_node      (v4.2r3 — matches 8 FPS)
PURPOSE: Convert ROI depth middle row to LaserScan with tilt correction.
TOPICS:  SUB /kinect/depth/image_raw; PUB /kinect/scan (BEST_EFFORT, ~8 Hz)
PARAMS:  ROI_WIDTH=320, ROI_HEIGHT=120, KINECT_FX=574.05, CX_ROI=159.5,
         TILT=-10°, TARGET_FPS=8
EXPECTED: /kinect/scan hz ≈ 8.0 ; range_max=4.0

NODE 3: safety_node             (unchanged)
PURPOSE: Enforce safety zones, fuse sensors, publish safe velocity + heartbeat.
TOPICS:  SUB /cmd_vel /scan /kinect/scan; PUB /safe_cmd_vel /ultron/heartbeat
SAFETY ZONES: STOP=0.35m, SLOW=0.70m; 20 Hz enforce, 10 Hz heartbeat.
EXPECTED: heartbeat ~10 Hz, safe_cmd_vel ~20 Hz.

NODE 4: serial_node             (v4.2 — B4 no TF, B7 clear_faults)
PURPOSE: Bridge ROS 2 ↔ Arduino binary protocol over USB serial.
TOPICS:
  SUB: /safe_cmd_vel          RELIABLE → VELOCITY_COMMAND (0x01)
  SUB: /ultron/heartbeat       RELIABLE → HEARTBEAT (0x05)
  SUB: /ultron/clear_faults RELIABLE → CLEAR_FAULTS (0x07)  [B7]
  PUB: /odom                  RELIABLE ← ENCODER_TICKS (0x01)
  PUB: /imu/data              RELIABLE ← IMU_DATA (0x02)
  PUB: /battery/state         RELIABLE ← BATTERY_VOLTAGE (0x03)
  PUB: /ultron/fault       RELIABLE ← FAULT_STATUS (0x04)
PARAMETERS: serial_port=/dev/ultron_arduino, serial_baud=115200
EXPECTED: "Serial connected: ..." ; /odom ~30 Hz.

CHANGE NOTES (v4.2):
  - B4: THIS NODE NO LONGER PUBLISHES odom→base_link TF. The laptop EKF is
    the single source of that transform. (Both publishing it caused TF
    conflicts.) It still publishes the /odom message.
  - B7: new subscription /ultron/clear_faults sends CLEAR_FAULTS (0x07)
    to the Arduino; Arduino clears faults only when the E-stop is released.
  - v4.1: twist uses real dt; MAX_SPEED_MPS=0.45.

```
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu, BatteryState
from geometry_msgs.msg import Twist
from std_msgs.msg import UInt8, Empty
import serial, struct, math, threading

HDR_OUT=0xAA; HDR_IN=0xBB
PKT_ENCODER=0x01; PKT_IMU=0x02; PKT_BATTERY=0x03
PKT_FAULT=0x04; PKT_HEARTBEAT=0x05
PKT_VELOCITY=0x01; PKT_ESTOP=0x02; PKT_RESET_ENC=0x03
PKT_CLEAR_FAULTS=0x07            # v4.2 B7

WHEEL_RADIUS_M=0.0381; WHEEL_SEP_M=0.3556
TICKS_PER_REV=825
METERS_PER_TICK=math.pi*(WHEEL_RADIUS_M*2)/TICKS_PER_REV
MAX_SPEED_MPS=0.45          # teleop limit (autonomous is 0.35 via Nav2)

def crc8(data):
    crc=0
    for b in data:
        crc^=b
        for _ in range(8):
            crc=((crc<<1)^0x07) if (crc&0x80) else (crc<<1)
            crc&=0xFF
    return crc

def build_pkt(t,payload):
    h=bytes([HDR_IN,t,len(payload)]); p=h+payload
    return p+bytes([crc8(p[1:])])

class SerialNode(Node):
    def __init__(self):
        super().__init__('ultron_serial_node')
        self.declare_parameter('serial_port','/dev/ultron_arduino')
        self.declare_parameter('serial_baud',115200)
        port=self.get_parameter('serial_port').value
        baud=self.get_parameter('serial_baud').value
        self.ser=serial.Serial(port,baud,timeout=0.1)
        self.get_logger().info(f'Serial connected: {port} @ {baud}')
        rel=QoSProfile(reliability=ReliabilityPolicy.RELIABLE,
                       history=HistoryPolicy.KEEP_LAST,depth=10)
        self.create_subscription(Twist,'/safe_cmd_vel',self.cmd_cb,rel)
        self.create_subscription(UInt8,'/ultron/heartbeat',self.hb_cb,rel)
        self.create_subscription(Empty,'/ultron/clear_faults',
                                 self.clear_cb,rel)      # v4.2 B7
        self.odom_pub=self.create_publisher(Odometry,'/odom',rel)
        self.imu_pub=self.create_publisher(Imu,'/imu/data',rel)
        self.bat_pub=self.create_publisher(BatteryState,'/battery/state',rel)
        self.flt_pub=self.create_publisher(UInt8,'/ultron/fault',rel)
        # v4.2 B4: NO TransformBroadcaster here. EKF owns odom→base_link.
        self.x=self.y=self.theta=0.0
        self.pl=self.pr=None
        self.last_ms=None                # Arduino tick timestamp (ms)
        self.lock=threading.Lock(); self.running=True
        threading.Thread(target=self._rx,daemon=True).start()

    def cmd_cb(self,msg):
        vl=msg.linear.x-(msg.angular.z*WHEEL_SEP_M/2)
        vr=msg.linear.x+(msg.angular.z*WHEEL_SEP_M/2)
        vl=max(-MAX_SPEED_MPS,min(MAX_SPEED_MPS,vl))
        vr=max(-MAX_SPEED_MPS,min(MAX_SPEED_MPS,vr))
        p=build_pkt(PKT_VELOCITY,struct.pack('>ff',vl,vr))
        with self.lock: self.ser.write(p)

    def hb_cb(self,msg):
        with self.lock:
            self.ser.write(build_pkt(PKT_HEARTBEAT,bytes([msg.data&0xFF])))

    def clear_cb(self,msg):               # v4.2 B7
        with self.lock:
            self.ser.write(build_pkt(PKT_CLEAR_FAULTS,b''))

    def _rx(self):
        st='W'; pt=pl=0; buf=bytearray()
        while self.running:
            try:
                b=self.ser.read(1)
                if not b: continue
                b=b[0]
                if st=='W':
                    if b==HDR_OUT: st='T'; buf=bytearray()
                elif st=='T': pt=b; buf.append(b); st='L'
                elif st=='L':
                    pl=b; buf.append(b)
                    st='P' if pl>0 else 'C'
                elif st=='P':
                    buf.append(b)
                    if len(buf)==2+pl: st='C'
                elif st=='C':
                    if crc8(bytes(buf))==b:
                        self._dispatch(pt,bytes(buf[2:]))
                    else:
                        self.get_logger().warn('CRC error')
                    st='W'
            except serial.SerialException as e:
                self.get_logger().error(f'Serial: {e}'); break

    def _dispatch(self,t,p):
        now=self.get_clock().now().to_msg()
        if t==PKT_ENCODER and len(p)==12:
            lt,rt,ts=struct.unpack('>iiI',p)
            self._odom(lt,rt,ts,now)
        elif t==PKT_IMU and len(p)==24:
            self._imu(*struct.unpack('>ffffff',p),stamp=now)
        elif t==PKT_BATTERY and len(p)==4:
            v,=struct.unpack('>f',p)
            m=BatteryState(); m.header.stamp=now; m.voltage=v; m.present=True
            self.bat_pub.publish(m)
        elif t==PKT_FAULT and len(p)==1:
            m=UInt8(); m.data=p[0]; self.flt_pub.publish(m)
            self.get_logger().warn(
                f'Fault:0x{p[0]:02X} ESTOP={bool(p[0]&1)} HB={bool(p[0]&64)}')

    def _odom(self,lt,rt,arduino_ms,stamp):
        # real inter-packet dt from Arduino ts_ms (encoder ~33 Hz, not 100 Hz)
        if self.pl is None:
            self.pl=lt; self.pr=rt; self.last_ms=arduino_ms; return
        dt=(arduino_ms-self.last_ms)/1000.0
        self.last_ms=arduino_ms
        if dt<=0.0 or dt>0.5:              # rollover or spurious delta
            self.pl=lt; self.pr=rt; return
        dl=(lt-self.pl)*METERS_PER_TICK
        dr=(rt-self.pr)*METERS_PER_TICK
        self.pl=lt; self.pr=rt
        dc=(dl+dr)/2; dth=(dr-dl)/WHEEL_SEP_M
        self.x+=dc*math.cos(self.theta+dth/2)
        self.y+=dc*math.sin(self.theta+dth/2)
        self.theta+=dth
        qz=math.sin(self.theta/2); qw=math.cos(self.theta/2)
        o=Odometry(); o.header.stamp=stamp; o.header.frame_id='odom'
        o.child_frame_id='base_link'
        o.pose.pose.position.x=self.x; o.pose.pose.position.y=self.y
        o.pose.pose.orientation.z=qz; o.pose.pose.orientation.w=qw
        o.twist.twist.linear.x=dc/dt       # real dt
        o.twist.twist.angular.z=dth/dt
        o.pose.covariance[0]=0.01; o.pose.covariance[7]=0.01
        o.pose.covariance[35]=0.05
        self.odom_pub.publish(o)
        # v4.2 B4: do NOT publish odom→base_link TF here.

    def _imu(self,ax,ay,az,gx,gy,gz,stamp):
        m=Imu(); m.header.stamp=stamp; m.header.frame_id='imu_link'
        m.linear_acceleration.x=ax; m.linear_acceleration.y=ay
        m.linear_acceleration.z=az
        m.angular_velocity.x=gx; m.angular_velocity.y=gy
        m.angular_velocity.z=gz
        m.orientation_covariance[0]=-1
        m.angular_velocity_covariance[0]=0.01
        m.linear_acceleration_covariance[0]=0.1
        self.imu_pub.publish(m)

    def destroy_node(self):
        self.running=False
        with self.lock: self.ser.write(build_pkt(PKT_ESTOP,b''))
        self.ser.close(); super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node=SerialNode()
    try: rclpy.spin(node)
    except KeyboardInterrupt: pass
    finally: node.destroy_node(); rclpy.shutdown()

if __name__=='__main__': main()
```

---

## Section 10 — SAFETY SYSTEM

---

### 10.1 SAFETY ARCHITECTURE
```
THREE INDEPENDENT SAFETY LAYERS (ordered by response time):

  LAYER 1 — HARDWARE (< 5ms):
    Arduino E-Stop ISR (INT4_vect)
    Triggered by: Physical button press
    Action: OCR4A=0, OCR3A=0, disable EN pins via port register.

  LAYER 2 — EMBEDDED SOFTWARE (500ms):
    Arduino heartbeat watchdog + cmd_vel watchdog
    Triggered by: Lost communication with Jetson
    Action: target velocities → 0, FAULT_BIT_HEARTBEAT/WATCHDOG set

  LAYER 3 — JETSON SOFTWARE (20Hz loop):
    Safety node obstacle detection and velocity filtering
    Triggered by: Sensor data indicating proximity violations
    Action: /safe_cmd_vel zeroed or scaled before reaching Arduino

10.2 SAFETY ZONES
```
  STOP zone (≤ 0.35m):   zero velocity; LiDAR governs if obstacle < 1.0m
  SLOW zone (0.35–0.70m): scale = (d-0.35)/(0.70-0.35); turn-in-place rules
  FREE zone (> 0.70m):    command passes through
  LiDAR stale > 1.0s → STOP; Kinect stale > 1.0s → degrade to LiDAR-only
  MAX_SPEED_MPS=0.45 teleop; Nav2 max_vel_x=0.35 autonomous (v4.2 B6)

### 10.3 WATCHDOG BEHAVIOR
```
  HEARTBEAT: safety node 10 Hz → serial → Arduino; 500 ms loss → motors stop.
  RECOVERY: heartbeat resume clears FAULT_BIT_HEARTBEAT; motors resume only
            on a new /safe_cmd_vel.
  HARDWARE WDT: 8 s; only true firmware hangs; wdt_reset each 10 ms loop.

10.4 EMERGENCY STOP LOGIC
```
  HARDWARE ESTOP (physical button → D2/INT4):
    ISR(INT4_vect): OCR4A=0; OCR3A=0; EN(PG5,PH5)=LOW
    Latency: < 5 ms; FAULT_BIT_ESTOP (bit 0) set.

  RECOVERY (v4.2 B7 — two-step, deliberate):
    1. Release the physical E-stop button (pin reads HIGH).
    2. Publish CLEAR_FAULTS:
         ros2 topic pub /ultron/clear_faults std_msgs/msg/Empty "{}" --once
    The Arduino clears ALL fault bits ONLY when the button is released AND a
    CLEAR_FAULTS (0x07) packet is received. Motors resume on the next valid
    /safe_cmd_vel. (Power-cycling also clears, but releases the button.)

  SOFTWARE ESTOP (/ultron/heartbeat stops): 500 ms → FAULT_BIT_HEARTBEAT;
    recovery: heartbeat resumes → auto-clear.
  SOFTWARE ESTOP (packet 0x02 from Jetson): serial_node.destroy_node() sends
    PKT_ESTOP on shutdown → FAULT_BIT_ESTOP; recovery as above (B7).

  OPERATOR NOTE (v4.2r2 D6): a clean `docker compose restart` also sends
    PKT_ESTOP and latches the E-stop. After a restart (button released), the
    operator MUST publish /ultron/clear_faults before the motors will run:
      ros2 topic pub /ultron/clear_faults std_msgs/msg/Empty "{}" --once
    A crash / OOM restart does NOT latch — the heartbeat timeout (FAULT_BIT_
    HEARTBEAT) auto-clears on reconnect.

---

## Section 11 — ARDUINO FIRMWARE

---

### 11.1 ARCHITECTURE
```
EXECUTION MODEL:
  Main loop:    100 Hz (10ms period) — cooperative scheduling
  ISRs:         Hardware-preemptive (encoder, E-stop)
  WDT:          8s hardware timeout (AVR peripheral, independent)

PRIORITY (highest → lowest):
  1. ISR(INT4_vect)  — E-Stop          < 5 µs
  2. ISR(INT3_vect)  — Left Enc A      < 10 µs
  3. ISR(INT2_vect)  — Left Enc B      < 10 µs
  4. ISR(PCINT0_vect)— Right Enc       < 10 µs  (D52/D51, Port B — v4.2 B1)
  5. Main loop       — 100 Hz cooperative
  6. Background tasks— opportunistic

ISR RULES (never violate):
  NO Serial.print()/delay()/Wire inside ISR; keep ISR < 10 µs;
  shared variables volatile.

11.2 SERIAL PROTOCOL
```
PACKET FRAME:
  [ HDR 1B ][ TYPE 1B ][ LEN 1B ][ PAYLOAD 0-255B ][ CRC 1B ]
  HDR: 0xAA = Arduino→Jetson, 0xBB = Jetson→Arduino
  CRC: CRC-8-CCITT, poly 0x07, init 0x00, over TYPE+LEN+PAYLOAD
  Byte order: BIG-ENDIAN

OUTBOUND PACKETS (Arduino → Jetson, HDR=0xAA):
| 0x01 | ENCODER_TICKS | 12 | int32 left, int32 right, uint32 ts_ms |
|---|---|---|---|
| 0x02 | IMU_DATA | 24 | float ax,ay,az,gx,gy,gz (m/s², rad/s) |
| 0x03 | BATTERY_VOLTAGE | 4 | float voltage (Volts) |
| 0x04 | FAULT_STATUS | 1 | uint8 fault_flags bitmask |

INBOUND PACKETS (Jetson → Arduino, HDR=0xBB):
| 0x01 | VELOCITY_COMMAND | 8 | float vel_left, vel_right (m/s BE) |
|---|---|---|---|
| 0x02 | EMERGENCY_STOP | 0 | no payload |
| 0x03 | RESET_ENCODERS | 0 | no payload |
| 0x05 | HEARTBEAT | 1 | uint8 sequence_number |
| 0x07 | CLEAR_FAULTS | 0 | clears faults ONLY if E-stop released |
| (v4.2 B7) |  | (pin HIGH) |  |

FAULT BITS:
  bit 0: FAULT_BIT_ESTOP       (1 << 0) hardware button or SW command
  bit 1: FAULT_BIT_OVERCURRENT (1 << 1) > 7A/motor sustained 500ms (v4.2 B8)
  bit 2: FAULT_BIT_WATCHDOG    (1 << 2) no cmd_vel > 500ms
  bit 3: FAULT_BIT_IMU         (1 << 3) I2C failure > 10 reads
  bit 4: FAULT_BIT_ENCODER     (1 << 4) stuck encoder during motion
  bit 5: FAULT_BIT_BATTERY     (1 << 5) voltage < 10.5V
  bit 6: FAULT_BIT_HEARTBEAT   (1 << 6) no heartbeat > 500ms
  bit 7: (reserved, unused)

### 11.3 FULL FIRMWARE
```
FILE: ultron_firmware/config.h  (v4.2r2 — two-PWM pins, encoders, 7A, ADC)
```
#pragma once
#include <stdint.h>

// ── PINS (ATmega2560 R3 verified) ────────────────────────────────────────────
// v4.2r2 D1: native two-PWM BTS7960 control (one PWM per direction).
#define LEFT_MOTOR_PWM      6    // PH3 = Timer4 OC4A  (forward)
#define LEFT_MOTOR_LPWM     7    // PH4 = Timer4 OC4B  (reverse)
#define LEFT_MOTOR_EN       4    // PG5
#define RIGHT_MOTOR_PWM     5    // PE3 = Timer3 OC3A  (forward)
#define RIGHT_MOTOR_LPWM    3    // PE5 = Timer3 OC3C  (reverse)
#define RIGHT_MOTOR_EN      8    // PH5
// v4.2 B1: Right encoder moved from D23/D24 (Port A — NO PCINT on ATmega2560)
//          to D52/D51 (Port B). ISR reads PINB.
#define LEFT_ENC_A          18   // PD3 = INT3
#define LEFT_ENC_B          19   // PD2 = INT2
#define RIGHT_ENC_A         52   // PB1 = PCINT1 (PCIE0/PCMSK0)
#define RIGHT_ENC_B         51   // PB2 = PCINT2 (PCIE0/PCMSK0)
#define IMU_SDA             20   // PD1 = I2C SDA only
#define IMU_SCL             21   // PD0 = I2C SCL only
#define IMU_INT             22   // PA0
#define ESTOP_PIN           2    // PE4 = INT4 (EICRB register)
#define HEARTBEAT_LED       13   // PB7
#define FAULT_LED           12   // PB6
#define BATTERY_VOLTAGE_PIN A0   // PF0
#define CURRENT_SENSE_L_PIN A1   // PF1
#define CURRENT_SENSE_R_PIN A2   // PF2

// ── PWM ───────────────────────────────────────────────────────────────────────
#define MOTOR_PWM_TOP       99    // 16MHz/(8*(1+99)) = 20kHz, Timer3+4

// ── TIMING ────────────────────────────────────────────────────────────────────
#define LOOP_PERIOD_US          10000UL   // 10ms = 100Hz
#define CMD_VEL_TIMEOUT_MS      500UL
#define HEARTBEAT_TIMEOUT_MS    500UL
#define IMU_FAIL_THRESHOLD      10
#define OVERCURRENT_SAMPLES     5         // 5 × 100ms = 500ms
#define ENCODER_FAULT_MS        1000UL
#define TX_DECIMATION           3         // 100Hz/3 ≈ 33Hz publish
#define SERIAL_RX_WINDOW_US     1200UL    // v4.2r2 D4: full 12-byte vel pkt (1.04ms)

// ── KINEMATICS ────────────────────────────────────────────────────────────────
#define WHEEL_RADIUS_M      0.0381f       // TODO_CALIBRATE
#define WHEEL_SEP_M         0.3556f       // TODO_CALIBRATE
#define TICKS_PER_REV       825
#define METERS_PER_TICK     0.00029013f

// ── BATTERY ───────────────────────────────────────────────────────────────────
#define BATTERY_CRITICAL_V  10.5f
#define BATTERY_WARNING_V   11.1f
#define BATTERY_ADC_SCALE   0.017418f     // 5V/1023 / (3.9/13.9)

// ── CURRENT (v4.2 B8: per-motor 7.0A) ─────────────────────────────────────────
#define CURRENT_FAULT_AMPS  7.0f          // single stall (8A) triggers first
#define ACS712_ZERO_V       2.5f
#define ACS712_MV_PER_A     0.066f

// ── MOTOR ─────────────────────────────────────────────────────────────────────
#define MOTOR_LEFT          0
#define MOTOR_RIGHT         1
#define PWM_DEADZONE        25
#define MAX_SPEED_MPS       0.45f         // teleop clamp; Nav2 auto = 0.35

// ── PROTOCOL ──────────────────────────────────────────────────────────────────
#define SERIAL_BAUD         115200
#define HDR_OUT             0xAA
#define HDR_IN              0xBB
#define PKT_ENCODER         0x01
#define PKT_IMU             0x02
#define PKT_BATTERY         0x03
#define PKT_FAULT           0x04
#define PKT_HEARTBEAT       0x05
#define PKT_CLEAR_FAULTS    0x07    // v4.2 B7

// ── FAULT BITS ────────────────────────────────────────────────────────────────
#define FAULT_BIT_ESTOP       (1 << 0)
#define FAULT_BIT_OVERCURRENT (1 << 1)
#define FAULT_BIT_WATCHDOG    (1 << 2)
#define FAULT_BIT_IMU         (1 << 3)
#define FAULT_BIT_ENCODER     (1 << 4)
#define FAULT_BIT_BATTERY     (1 << 5)
#define FAULT_BIT_HEARTBEAT   (1 << 6)

#define SET_FAULT(b)    (fault_flags |=  (b))
#define CLEAR_FAULT(b)  (fault_flags &= ~(b))
#define IS_FAULT(b)     (fault_flags &   (b))
#define ANY_MOTOR_FAULT() \
    (fault_flags & (FAULT_BIT_ESTOP|FAULT_BIT_OVERCURRENT| \
                    FAULT_BIT_ENCODER|FAULT_BIT_BATTERY|FAULT_BIT_HEARTBEAT))

// E-stop button state (D2 = PE4). Active-low: LATCHED when pressed.
#define ESTOP_LATCHED()     (!(PINE & (1 << PE4)))

// ── TX QUEUE ──────────────────────────────────────────────────────────────────
#define TX_QUEUE_SLOTS    4
#define TX_MAX_PKT_SIZE   30

// ── FIXED POINT (Q16.16) ──────────────────────────────────────────────────────
typedef int32_t fixed16_t;
#define FLOAT_TO_FIXED(f) ((fixed16_t)((f)*65536.0f))
#define FIXED_TO_FLOAT(x) ((float)(x)/65536.0f)
#define FIXED_MUL(a,b)    ((fixed16_t)(((int64_t)(a)*(b))>>16))

// ── IMU ───────────────────────────────────────────────────────────────────────
#define IMU_I2C_ADDR    0x68

```
FILE: ultron_firmware/encoders.cpp  (v4.2 B1 — reads PINB)
```
#include "encoders.h"

volatile int32_t left_encoder_count  = 0;
volatile int32_t right_encoder_count = 0;
volatile bool    right_enc_a_prev    = false;
volatile bool    right_enc_b_prev    = false;

// Left: D18=PD3=INT3 (Ch A) + D19=PD2=INT2 (Ch B)
ISR(INT3_vect) {                        // Ch A changed
    bool a=(PIND&(1<<PD3))!=0;
    bool b=(PIND&(1<<PD2))!=0;
    left_encoder_count+=(a^b)?1:-1;
}
ISR(INT2_vect) {                        // Ch B changed
    bool a=(PIND&(1<<PD3))!=0;
    bool b=(PIND&(1<<PD2))!=0;
    left_encoder_count+=(a^b)?-1:1;
}

// v4.2 B1: Right: D52=PB1=PCINT1 + D51=PB2=PCINT2 (Group PCIE0, PCMSK0)
// Port B — correct for ATmega2560. WAS D23/D24 (Port A) → no PCINT → never
// counted. ISR now reads PINB.
ISR(PCINT0_vect) {
    bool a=(PINB&(1<<PB1))!=0;          // D52
    bool b=(PINB&(1<<PB2))!=0;          // D51
    if(a!=right_enc_a_prev)
        right_encoder_count+=(a^b)?1:-1;
    else if(b!=right_enc_b_prev)
        right_encoder_count+=(a^b)?-1:1;
    right_enc_a_prev=a; right_enc_b_prev=b;
}

void init_encoders() {
    pinMode(LEFT_ENC_A, INPUT_PULLUP);
    pinMode(LEFT_ENC_B, INPUT_PULLUP);
    // INT3 (D18/PD3) CHANGE: EICRA ISC3[1:0]=01
    EICRA|=(1<<ISC30); EICRA&=~(1<<ISC31);
    // INT2 (D19/PD2) CHANGE: EICRA ISC2[1:0]=01
    EICRA|=(1<<ISC20); EICRA&=~(1<<ISC21);
    EIMSK|=(1<<INT3)|(1<<INT2);

    pinMode(RIGHT_ENC_A, INPUT_PULLUP);   // D52 = PB1
    pinMode(RIGHT_ENC_B, INPUT_PULLUP);   // D51 = PB2
    // PCIE0 = Port B (PB0-PB7). D52=PB1=PCINT1, D51=PB2=PCINT2.
    PCICR|=(1<<PCIE0);
    PCMSK0|=(1<<PCINT1)|(1<<PCINT2);
    right_enc_a_prev=(PINB&(1<<PB1))!=0;
    right_enc_b_prev=(PINB&(1<<PB2))!=0;
}
```
FILE: ultron_firmware/motors.cpp   (v4.2r2 D1 — native two-PWM)
```
#include "motors.h"

void init_motor_pwm() {
    pinMode(LEFT_MOTOR_PWM,OUTPUT); pinMode(LEFT_MOTOR_LPWM,OUTPUT);
    pinMode(LEFT_MOTOR_EN,OUTPUT);  pinMode(RIGHT_MOTOR_PWM,OUTPUT);
    pinMode(RIGHT_MOTOR_LPWM,OUTPUT);pinMode(RIGHT_MOTOR_EN,OUTPUT);
    digitalWrite(LEFT_MOTOR_EN,LOW); digitalWrite(RIGHT_MOTOR_EN,LOW);

    // Timer4: LEFT motor, OC4A=D6 (fwd) + OC4B=D7 (rev), Fast PWM, prescaler=8
    TCCR4A=(1<<COM4A1)|(1<<COM4B1)|(1<<WGM41);
    TCCR4B=(1<<WGM43)|(1<<WGM42)|(1<<CS41);
    ICR4=MOTOR_PWM_TOP; OCR4A=0; OCR4B=0;

    // Timer3: RIGHT motor, OC3A=D5 (fwd) + OC3C=D3 (rev), Fast PWM, prescaler=8
    TCCR3A=(1<<COM3A1)|(1<<COM3C1)|(1<<WGM31);
    TCCR3B=(1<<WGM33)|(1<<WGM32)|(1<<CS31);
    ICR3=MOTOR_PWM_TOP; OCR3A=0; OCR3C=0;

    digitalWrite(LEFT_MOTOR_EN,HIGH); digitalWrite(RIGHT_MOTOR_EN,HIGH);
}

void set_motor_pwm(uint8_t motor, int16_t pwm) {
    // v4.2r2 D1: drive the forward or reverse channel, zero the other.
    if(motor==MOTOR_LEFT){
        if(pwm>=0){ OCR4A=map(pwm,0,255,0,MOTOR_PWM_TOP); OCR4B=0; }
        else      { OCR4A=0; OCR4B=map(-pwm,0,255,0,MOTOR_PWM_TOP); }
    } else {
        if(pwm>=0){ OCR3A=map(pwm,0,255,0,MOTOR_PWM_TOP); OCR3C=0; }
        else      { OCR3A=0; OCR3C=map(-pwm,0,255,0,MOTOR_PWM_TOP); }
    }
}

int16_t velocity_to_pwm(float v) {
    // teleop clamp 0.45 m/s; autonomous is limited earlier by Nav2 (0.35)
    float p=(v/MAX_SPEED_MPS)*255.0f;
    if(fabs(p)<PWM_DEADZONE&&fabs(p)>0.0f)
        p=(p>0)?PWM_DEADZONE:-PWM_DEADZONE;
    return (int16_t)constrain(p,-255,255);
}
```
FILE: ultron_firmware/ultron_firmware.ino   (v4.2r2 — EN re-enable, RX 1200µs)
```
#include <Wire.h>
#include <avr/wdt.h>
#include "config.h"
#include "encoders.h"
#include "motors.h"
#include "imu.h"
#include "protocol.h"
#include "faults.h"
#include "tx_queue.h"
#include "power.h"

volatile uint8_t fault_flags   = 0x00;
float  target_vel_left         = 0.0f;
float  target_vel_right        = 0.0f;
uint32_t last_cmd_vel_ms       = 0;
uint32_t last_heartbeat_ms     = 0;
bool     heartbeat_initialized = false;

uint8_t rx_buf[64]; uint8_t tx_tmp[TX_MAX_PKT_SIZE];
uint8_t rx_state=0, rx_type, rx_len, rx_idx;
uint8_t imu_fail_count=0, overcurrent_count=0, tx_decim=0;
uint32_t last_enc_ms=0, last_loop_us=0;
int32_t  last_total_ticks=0;

int freeRam(){extern int __heap_start,*__brkval;int v;
  return (int)&v-(__brkval==0?(int)&__heap_start:(int)__brkval);}

// E-Stop: D2=PE4=INT4, uses EICRB (not EICRA)
ISR(INT4_vect){
    SET_FAULT(FAULT_BIT_ESTOP);
    OCR4A=0; OCR4B=0; OCR3A=0; OCR3C=0; // Zero ALL PWM channels (v4.2r2 D1)
    PORTG&=~(1<<PG5);                   // D4=LEFT_EN=PG5  → LOW
    PORTH&=~(1<<PH5);                   // D8=RIGHT_EN=PH5 → LOW
}

bool parse_byte(uint8_t b){
    switch(rx_state){
    case 0: if(b==HDR_IN){rx_state=1;}break;
    case 1: rx_type=b;rx_buf[0]=b;rx_state=2;break;
    case 2: rx_len=b;rx_buf[1]=b;rx_idx=2;
            rx_state=(rx_len==0)?4:3;break;
    case 3: rx_buf[rx_idx++]=b;
            if(rx_idx>=2+rx_len)rx_state=4;break;
    case 4:{uint8_t c=crc8(rx_buf,rx_idx);rx_state=0;return(c==b);}
    } return false;
}

void process_packet(){
    uint8_t *p=&rx_buf[2];
    switch(rx_type){
    case 0x01:
        if(rx_len!=8)break;
        {float vl=ntoh_float(&p[0]),vr=ntoh_float(&p[4]);
         if(isnan(vl)||isinf(vl)||isnan(vr)||isinf(vr))break;
         target_vel_left=constrain(vl,-MAX_SPEED_MPS,MAX_SPEED_MPS);
         target_vel_right=constrain(vr,-MAX_SPEED_MPS,MAX_SPEED_MPS);
         last_cmd_vel_ms=millis(); CLEAR_FAULT(FAULT_BIT_WATCHDOG);}break;
    case 0x02:
        SET_FAULT(FAULT_BIT_ESTOP);
        OCR4A=0;OCR4B=0;OCR3A=0;OCR3C=0;
        PORTG&=~(1<<PG5);PORTH&=~(1<<PH5);
        break;
    case 0x03:
        noInterrupts();
        left_encoder_count=right_encoder_count=0;
        interrupts();break;
    case 0x05:
        last_heartbeat_ms=millis();
        heartbeat_initialized=true;
        CLEAR_FAULT(FAULT_BIT_HEARTBEAT);break;
    // v4.2 B7: clear faults ONLY after the E-stop button is physically
    // released. Keeps latching for safety, adds a deliberate 2-step recovery.
    case 0x07:
        if(!ESTOP_LATCHED()){ fault_flags = 0; }
        break;
    }
}

void setup(){
    uint8_t m=MCUSR; MCUSR=0; wdt_disable();
    Serial.begin(SERIAL_BAUD);
    Wire.begin(); Wire.setClock(400000);
    init_encoders(); init_motor_pwm(); init_imu(); init_tx_queue();

    // E-Stop INT4: EICRB register, falling edge
    pinMode(ESTOP_PIN,INPUT_PULLUP);
    EICRB|=(1<<ISC41); EICRB&=~(1<<ISC40);
    EIMSK|=(1<<INT4);

    pinMode(HEARTBEAT_LED,OUTPUT); pinMode(FAULT_LED,OUTPUT);
    digitalWrite(HEARTBEAT_LED,LOW); digitalWrite(FAULT_LED,LOW);
    last_cmd_vel_ms=last_heartbeat_ms=millis();

    if(m&(1<<WDRF))
        Serial.println(F("WARN: Previous reset was HW WDT"));
    Serial.print(F("ultron ready. RAM:"));
    Serial.println(freeRam());

    wdt_enable(WDTO_8S);  // HW WDT: 8s
}

void loop(){
    uint32_t now_us=micros();
    if((now_us-last_loop_us)<LOOP_PERIOD_US){
        background_tasks(); return;
    }
    last_loop_us=now_us; wdt_reset();

    // STEP 1: Atomic encoder read
    noInterrupts();
    int32_t lc=left_encoder_count;
    int32_t rc=right_encoder_count;
    interrupts();

    // STEP 2: Fixed-point odometry (host does final pose; here harmless)
    static int32_t plc=0,prc=0;
    static fixed16_t MPT=FLOAT_TO_FIXED(METERS_PER_TICK);
    static fixed16_t IWS=FLOAT_TO_FIXED(1.0f/WHEEL_SEP_M);
    int32_t dl=lc-plc, dr=rc-prc; plc=lc; prc=rc;
    fixed16_t dl_m=FIXED_MUL(MPT,(fixed16_t)dl<<16);
    fixed16_t dr_m=FIXED_MUL(MPT,(fixed16_t)dr<<16);

    // STEP 3: IMU
    ImuData imu; bool imu_ok=read_imu(&imu);
    if(!imu_ok){if(++imu_fail_count>=IMU_FAIL_THRESHOLD)SET_FAULT(FAULT_BIT_IMU);}
    else{imu_fail_count=0; CLEAR_FAULT(FAULT_BIT_IMU);}

    // STEP 4: Serial RX (v4.2r2 D4: 1200µs window → full 12-byte velocity pkt)
    while(Serial.available()&&(micros()-now_us)<SERIAL_RX_WINDOW_US){
        if(parse_byte((uint8_t)Serial.read()))process_packet();
    }

    // STEP 5: Software watchdogs
    uint32_t now_ms=millis();
    if((now_ms-last_cmd_vel_ms)>CMD_VEL_TIMEOUT_MS){
        SET_FAULT(FAULT_BIT_WATCHDOG);
        target_vel_left=target_vel_right=0.0f;
    }
    if(heartbeat_initialized){
        if((now_ms-last_heartbeat_ms)>HEARTBEAT_TIMEOUT_MS){
            SET_FAULT(FAULT_BIT_HEARTBEAT);
            target_vel_left=target_vel_right=0.0f;
        }
    } else if((now_ms-last_heartbeat_ms)>5000UL){
        heartbeat_initialized=true; // 5s boot grace
    }

    // STEP 6: Motor output (v4.2r2 D3: re-enable EN pins after fault clear —
    //         the E-stop ISR drops them and nothing else restored them, so
    //         the robot stayed dead after recovery).
    if(ANY_MOTOR_FAULT()){
        OCR4A=0;OCR4B=0;OCR3A=0;OCR3C=0;
        PORTG&=~(1<<PG5);PORTH&=~(1<<PH5);   // keep EN low while faulted
    } else {
        PORTG|=(1<<PG5);PORTH|=(1<<PH5);     // re-enable drivers
        set_motor_pwm(MOTOR_LEFT, velocity_to_pwm(target_vel_left));
        set_motor_pwm(MOTOR_RIGHT,velocity_to_pwm(target_vel_right));
    }

    // STEP 7: Encoder fault check (both wheels now count — v4.2 B1)
    int32_t tot=abs(lc)+abs(rc);
    if(tot!=last_total_ticks){last_total_ticks=tot;last_enc_ms=now_ms;}
    if((fabs(target_vel_left)>0.05f||fabs(target_vel_right)>0.05f)&&
       (now_ms-last_enc_ms)>ENCODER_FAULT_MS)
        SET_FAULT(FAULT_BIT_ENCODER);

    // STEP 8: Enqueue TX
    if(++tx_decim>=TX_DECIMATION){
        tx_decim=0;
        uint8_t n=build_encoder_packet(tx_tmp,lc,rc,now_ms);
        tx_enqueue(tx_tmp,n);
        if(imu_ok){n=build_imu_packet(tx_tmp,&imu);tx_enqueue(tx_tmp,n);}
    }
    if(fault_flags){
        uint8_t n=build_fault_packet(tx_tmp,fault_flags);
        tx_enqueue(tx_tmp,n);
    }

    // STEP 9: Drain TX
    tx_drain();
    digitalWrite(FAULT_LED,fault_flags?HIGH:LOW);
}
```

FULL SUPPORTING FIRMWARE (v4.2r3 — completes the buildable set; matches the
config.h and .ino above. Files: encoders.h, motors.h, imu.h/.cpp,
protocol.h/.cpp, tx_queue.h/.cpp, power.h/.cpp, faults.h/.cpp)

FILE: ultron_firmware/encoders.h
```
#pragma once
#include <stdint.h>
void init_encoders();
extern volatile int32_t left_encoder_count;
extern volatile int32_t right_encoder_count;

#### ultron_firmware/motors.h
```
#pragma once
#include <stdint.h>
#include "config.h"
void init_motor_pwm();
void set_motor_pwm(uint8_t motor, int16_t pwm);
int16_t velocity_to_pwm(float v);

FILE: ultron_firmware/imu.h
```
#pragma once
#include <stdint.h>
typedef struct { float ax, ay, az, gx, gy, gz; } ImuData;
void init_imu();
bool read_imu(ImuData* out);

#### ultron_firmware/imu.cpp
```
#include "imu.h"
#include <Wire.h>
#include "config.h"

#define MPU_WHOAMI   0x75
#define MPU_PWR      0x6B
#define MPU_ACCEL_XH 0x3B
#define ACCEL_SCALE  16384.0f      // +-2g full scale
#define GYRO_SCALE   131.0f        // +-250 deg/s full scale -> dps

void init_imu(){
    Wire.beginTransmission(IMU_I2C_ADDR);
    Wire.write(MPU_PWR); Wire.write(0x00);      // wake from sleep
    Wire.endTransmission();
}

bool read_imu(ImuData* out){
    if(!out) return false;
    Wire.beginTransmission(IMU_I2C_ADDR);
    Wire.write(MPU_ACCEL_XH);
    if(Wire.endTransmission()!=0) return false; // NACK = IMU absent/fault
    Wire.requestFrom((uint8_t)IMU_I2C_ADDR, (uint8_t)14);
    if(Wire.available()<14) return false;
    uint8_t b[14]; for(uint8_t i=0;i<14;i++) b[i]=Wire.read();
    int16_t ax=((int16_t)b[0]<<8)|b[1];
    int16_t ay=((int16_t)b[2]<<8)|b[3];
    int16_t az=((int16_t)b[4]<<8)|b[5];
    int16_t gx=((int16_t)b[8]<<8)|b[9];
    int16_t gy=((int16_t)b[10]<<8)|b[11];
    int16_t gz=((int16_t)b[12]<<8)|b[13];
    out->ax=ax/ACCEL_SCALE;   out->ay=ay/ACCEL_SCALE;   out->az=az/ACCEL_SCALE;
    out->gx=gx/GYRO_SCALE*0.0174533f;                   // deg/s -> rad/s
    out->gy=gy/GYRO_SCALE*0.0174533f;
    out->gz=gz/GYRO_SCALE*0.0174533f;
    return true;
}

FILE: ultron_firmware/protocol.h
```
#pragma once
#include <stdint.h>
#include "imu.h"
uint8_t crc8(const uint8_t* data, uint8_t len);
uint8_t build_encoder_packet(uint8_t* out, int32_t l, int32_t r, uint32_t ts);
uint8_t build_imu_packet(uint8_t* out, const ImuData* imu);
uint8_t build_battery_packet(uint8_t* out, float v);
uint8_t build_fault_packet(uint8_t* out, uint8_t flags);
float ntoh_float(const uint8_t* p);

#### ultron_firmware/protocol.cpp
```
#include "protocol.h"
#include "config.h"

uint8_t crc8(const uint8_t* data, uint8_t len){
    uint8_t crc=0;
    for(uint8_t i=0;i<len;i++){
        crc^=data[i];
        for(uint8_t b=0;b<8;b++)
            crc=(crc&0x80)?(uint8_t)((crc<<1)^0x07):(uint8_t)(crc<<1);
    }
    return crc;
}

float ntoh_float(const uint8_t* p){
    union { uint32_t u; float f; } x;
    x.u=((uint32_t)p[0]<<24)|((uint32_t)p[1]<<16)|((uint32_t)p[2]<<8)|p[3];
    return x.f;
}

// finalize: HDR, TYPE, LEN, payload[0..len-1], CRC over TYPE+LEN+payload
static uint8_t pkt_finish(uint8_t* out, uint8_t type, uint8_t len){
    out[0]=HDR_OUT; out[1]=type; out[2]=len;
    out[3+len]=crc8(&out[1], (uint8_t)(len+2));
    return (uint8_t)(len+4);
}

uint8_t build_encoder_packet(uint8_t* out, int32_t l, int32_t r, uint32_t ts){
    out[3]=(uint8_t)(l>>24); out[4]=(uint8_t)(l>>16); out[5]=(uint8_t)(l>>8); out[6]=(uint8_t)l;
    out[7]=(uint8_t)(r>>24); out[8]=(uint8_t)(r>>16); out[9]=(uint8_t)(r>>8); out[10]=(uint8_t)r;
    out[11]=(uint8_t)(ts>>24);out[12]=(uint8_t)(ts>>16);out[13]=(uint8_t)(ts>>8);out[14]=(uint8_t)ts;
    return pkt_finish(out, PKT_ENCODER, 12);
}

uint8_t build_imu_packet(uint8_t* out, const ImuData* imu){
    const float v[6]={imu->ax,imu->ay,imu->az,imu->gx,imu->gy,imu->gz};
    for(uint8_t i=0;i<6;i++){
        union { uint32_t u; float f; } x; x.f=v[i];
        out[3+i*4]=(uint8_t)(x.u>>24); out[4+i*4]=(uint8_t)(x.u>>16);
        out[5+i*4]=(uint8_t)(x.u>>8);  out[6+i*4]=(uint8_t)x.u;
    }
    return pkt_finish(out, PKT_IMU, 24);
}

uint8_t build_battery_packet(uint8_t* out, float v){
    union { uint32_t u; float f; } x; x.f=v;
    out[3]=(uint8_t)(x.u>>24); out[4]=(uint8_t)(x.u>>16);
    out[5]=(uint8_t)(x.u>>8);  out[6]=(uint8_t)x.u;
    return pkt_finish(out, PKT_BATTERY, 4);
}

uint8_t build_fault_packet(uint8_t* out, uint8_t flags){
    out[3]=flags;
    return pkt_finish(out, PKT_FAULT, 1);
}

FILE: ultron_firmware/tx_queue.h
```
#pragma once
#include <stdint.h>
void init_tx_queue();
bool tx_enqueue(const uint8_t* data, uint8_t len);
void tx_drain();

#### ultron_firmware/tx_queue.cpp
```
#include "tx_queue.h"
#include "config.h"

struct Slot { uint8_t buf[TX_MAX_PKT_SIZE]; uint8_t len; };
static Slot q[TX_QUEUE_SLOTS];
static uint8_t head=0, count=0;

void init_tx_queue(){ head=0; count=0; }

bool tx_enqueue(const uint8_t* data, uint8_t len){
    if(len==0 || len>TX_MAX_PKT_SIZE) return false;
    if(count>=TX_QUEUE_SLOTS) return false;          // queue full: drop new
    uint8_t idx=(uint8_t)((head+count)%TX_QUEUE_SLOTS);
    memcpy(q[idx].buf, data, len);
    q[idx].len=len; count++;
    return true;
}

void tx_drain(){
    while(count>0 && Serial.availableForWrite()>=q[head].len){
        Serial.write(q[head].buf, q[head].len);
        head=(uint8_t)((head+1)%TX_QUEUE_SLOTS); count--;
    }
}

FILE: ultron_firmware/power.h
```
#pragma once
#include <stdint.h>
void background_tasks();
float read_battery_voltage();

#### ultron_firmware/power.cpp
```
#include "power.h"
#include "config.h"
#include "tx_queue.h"
#include "protocol.h"

extern volatile uint8_t fault_flags;   // defined in the .ino

static float read_current(uint8_t pin){
    float v=analogRead(pin)*(5.0f/1023.0f);
    return (v-ACS712_ZERO_V)/ACS712_MV_PER_A;        // Amps
}

float read_battery_voltage(){
    return analogRead(BATTERY_VOLTAGE_PIN)*BATTERY_ADC_SCALE;
}

void background_tasks(){
    uint32_t now=millis();
    static uint32_t last_batt_ms=0, last_curr_ms=0;
    static uint8_t ci=0, filled=0;
    static float curr_l[OVERCURRENT_SAMPLES], curr_r[OVERCURRENT_SAMPLES];

    // Battery: publish ~1 Hz; latch critical fault at < 10.5 V.
    if(now-last_batt_ms>=1000){
        last_batt_ms=now;
        float v=read_battery_voltage();
        if(v<BATTERY_CRITICAL_V) SET_FAULT(FAULT_BIT_BATTERY);
        uint8_t tmp[TX_MAX_PKT_SIZE];
        tx_enqueue(tmp, build_battery_packet(tmp, v));
    }
    // Current: sample every 100 ms; 5-sample window = 500 ms sustained.
    if(now-last_curr_ms>=100){
        last_curr_ms=now;
        curr_l[ci]=read_current(CURRENT_SENSE_L_PIN);
        curr_r[ci]=read_current(CURRENT_SENSE_R_PIN);
        ci=(uint8_t)((ci+1)%OVERCURRENT_SAMPLES);
        if(filled<OVERCURRENT_SAMPLES) filled++;
        if(filled==OVERCURRENT_SAMPLES){
            float sl=0, sr=0;
            for(uint8_t i=0;i<OVERCURRENT_SAMPLES;i++){ sl+=curr_l[i]; sr+=curr_r[i]; }
            if((sl/OVERCURRENT_SAMPLES)>CURRENT_FAULT_AMPS ||
               (sr/OVERCURRENT_SAMPLES)>CURRENT_FAULT_AMPS)
                SET_FAULT(FAULT_BIT_OVERCURRENT);
        }
    }
}

FILE: ultron_firmware/faults.h
```
#pragma once
#include <stdint.h>
const char* fault_name(uint8_t bit);

#### ultron_firmware/faults.cpp  (debug helper only)
```
#include "faults.h"
const char* fault_name(uint8_t bit){
    switch(bit){
        case 0: return "ESTOP";
        case 1: return "OVERCURRENT";
        case 2: return "WATCHDOG";
        case 3: return "IMU";
        case 4: return "ENCODER";
        case 5: return "BATTERY";
        case 6: return "HEARTBEAT";
        case 7: return "RESERVED";
    }
    return "?";
}

11.4 FLASH INSTRUCTIONS
```
curl -fsSL https://raw.githubusercontent.com/arduino/arduino-cli/master/install.sh | sh -s -- --bindir /usr/local/bin
arduino-cli core update-index
arduino-cli core install arduino:avr
arduino-cli lib install "Wire"

arduino-cli board list
# GENUINE Mega 2560 R3 → /dev/ultron_arduino  arduino:avr:mega

arduino-cli compile --fqbn arduino:avr:mega:cpu=atmega2560 ~/ultron_firmware/
arduino-cli upload -p /dev/ultron_arduino --fqbn arduino:avr:mega:cpu=atmega2560 ~/ultron_firmware/

minicom -D /dev/ultron_arduino -b 115200
# Expected: "ultron ready. RAM: XXXX" (RAM > 5500)

---

## Section 12 — LAUNCH SYSTEM

---

### 12.1 LAUNCH FILE HIERARCHY
```
JETSON CONTAINER:
  entrypoint.sh
```

LAPTOP (docker compose):
  nav2_slam container       (EKF + SLAM + Nav2)   ← required
  rviz2 container           (visualization — on demand)
  (No Zenoh router — removed in v4.2 B3)

```
FILE: /mnt/ssd/ultron/jetson/launch/jetson_bringup.launch.py
```
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([

        Node(package='rplidar_ros',
             executable='rplidar_composition',
             name='rplidar', output='screen',
             parameters=[{'serial_port':'/dev/ultron_lidar',
                          'serial_baudrate':115200,
                          'frame_id':'laser_link',
                          'inverted':False,
                          'angle_compensate':True,
                          'scan_mode':'Standard'}]),

        Node(package='ultron_onboard',
             executable='kinect_driver_node', name='kinect_driver', output='screen'),

        Node(package='ultron_onboard',
             executable='depth_to_scan_node', name='depth_to_scan', output='screen'),

        Node(package='ultron_onboard',
             executable='safety_node', name='ultron_safety_node', output='screen'),

        Node(package='ultron_onboard',
             executable='serial_node', name='ultron_serial_node', output='screen',
             parameters=[{'serial_port':'/dev/ultron_arduino',
                          'serial_baud':115200}]),

        # Static TFs — adjust xyz to physical measurements
        Node(package='tf2_ros', executable='static_transform_publisher',
             name='base_to_laser',
             arguments=['0.10','0.0','0.12','0','0','0','1','base_link','laser_link']),

        Node(package='tf2_ros', executable='static_transform_publisher',
             name='base_to_kinect',
             # -10° pitch, half-angle: y=sin(-5°)=-0.08716, w=cos(-5°)=0.99619
             arguments=['0.05','0.0','0.30','0','-0.08716','0','0.99619',
                        'base_link','kinect_depth_frame']),

        Node(package='tf2_ros', executable='static_transform_publisher',
             name='base_to_imu',
             arguments=['0','0','0.05','0','0','0','1','base_link','imu_link']),

        # Optional pilot logging (Section 17) — disabled by default
        Node(package='ultron_onboard', executable='data_logger_node',
             name='ultron_data_logger', output='screen',
             parameters=[{'log_dir':'/mnt/ssd/ultron/logs',
                          'enabled':False}]),
    ])
```

12.2 MANDATORY STARTUP ORDER (v4.2 B3 — no router needed)
```
STEP 1 — JETSON: Flash Arduino (only if firmware changed)
  arduino-cli upload -p /dev/ultron_arduino \
      --fqbn arduino:avr:mega:cpu=atmega2560 ~/ultron_firmware/

STEP 2 — JETSON: Start onboard container
  cd /mnt/ssd/ultron/jetson
  docker compose up
  # Wait for: "Kinect depth stream active", "Serial connected ...",
  #           "Safety node active: STOP<=0.35m SLOW<=0.70m"

STEP 3 — LAPTOP: Start Nav2 + SLAM
  cd ~/ultron_laptop && docker compose up nav2_slam

STEP 4 — LAPTOP: Start RViz2 (when ready to visualize)
  xhost +local:docker && docker compose run --rm rviz2

IF RUNNING HEADLESS (field): tmux new-session -s ultron; docker compose up

---

## Section 13 — TESTING & VERIFICATION

---

### 13.1 HARDWARE TESTS (before any software)
```
MOTOR TEST (robot lifted off ground — ALWAYS first):
  1. Flash firmware, open minicom on Arduino serial → boot message RAM>5500
  2. Send a velocity packet via Python:
     python3 -c "
     import serial,struct,time
     def crc8(d):
         c=0
         for b in d:
             c^=b
             for _ in range(8): c=((c<<1)^7)if(c&128)else(c<<1);c&=255
         return c
     s=serial.Serial('/dev/ultron_arduino',115200,timeout=1)
     p=struct.pack('>ff',0.1,0.1)
     h=bytes([0xBB,0x01,0x08])
     pkt=h+p+bytes([crc8((h+p)[1:])])
     s.write(pkt); time.sleep(2)
     s.write(bytes([0xBB,0x02,0x00,crc8([0x02,0x00])]))"
     Expected: BOTH wheels rotate forward ~0.1 m/s (validates the two-PWM
               wiring D1 — swap M+/M− on that driver only if the wheel runs
               backwards).
  3. Speed-limit test: send 0.6,0.6 → wheels cap at ~0.45 m/s.

ENCODER TEST (v4.2 B1 — RIGHT WHEEL NOW COUNTS):
  1. Robot lifted. Rotate LEFT wheel one revolution by hand →
     left_encoder_count = 825 ± 10.
  2. Rotate RIGHT wheel one revolution by hand →
     right_encoder_count = 825 ± 10.   ← was 0 before B1 fix.
  3. Forward → positive; reverse → negative.

ESTOP TEST (v4.2 B7):
  1. Send velocity command (wheels spinning).
  2. Press E-stop → motors stop < 5ms, FAULT_LED solid.
  3. RELEASE the button. Motors STAY stopped (latched).
  4. Publish a clear:
     ros2 topic pub /ultron/clear_faults std_msgs/msg/Empty "{}" --once
  5. Send a new valid /cmd_vel → motors resume.

IMU TEST: tilt forward → ax up; rotate left → gz > 0.

BATTERY TEST: full 3S shows 12.x V ± 0.1 on /battery/state (scale 0.017418).

OVERCURRENT TEST (v4.2 B8):
  Lock both wheels (e.g., palm-brake), command 0.3 m/s for > 500 ms →
  FAULT_BIT_OVERCURRENT set, motors stop, fuse NOT blown.

BATTERY RUNTIME TEST: full pack, typical load → warning 11.1 V after
  ~15–20 min (matches the corrected budget).

13.2 COMMUNICATION TESTS
```
SERIAL TEST:
  minicom -D /dev/ultron_arduino -b 115200 → binary streaming ~30 Hz.
  On a GENUINE Mega R3 the device is /dev/ttyACM0 (cdc_acm); the udev
  symlink /dev/ultron_arduino must exist.

DDS OVER TAILSCALE TEST (v4.2 B3 — no router):
  # Both machines: RMW + CYCLONEDDS_URI + ROS_DOMAIN_ID set (Section 6.3/7).
  tailscale ping <peer-ip>        # direct (not relay)
  ros2 topic list                 # all topics visible (laptop)
  ros2 topic echo /odom --once    # data flows
  ros2 topic hz /ultron/heartbeat  # ~10 Hz

TF TEST:
  ros2 run tf2_tools view_frames
  # Chain: map → odom → base_link → laser_link / kinect_depth_frame / imu_link
  # odom→base_link is SINGLE-sourced by the laptop EKF (B4).

### 13.3 SYSTEM TESTS
```
TELEOP TEST: teleop_twist_keyboard (remap cmd_vel) → 4-direction drive + /odom.

ODOMETRY TWIST TEST: command 0.30 m/s → twist ≈ 0.30 (± 10%), NOT 0.9.

SAFETY ZONE TEST: hand 0.20 m in front while commanding 0.3 → /safe_cmd_vel=0.

SLAM TEST: drive full area → map builds; save with map_saver_cli.

NAVIGATION TEST (v4.2 B6): with saved map, Nav2 goal → moves at ≤ 0.35 m/s.

13.4 FAILURE TESTS
```
TEST: Kill WiFi → within 500 ms FAULT_BIT_HEARTBEAT, FAULT_LED solid, stops.
TEST: Kill Jetson container → Arduino stops motors within 500 ms.
TEST: Kill laptop Nav2 → cmd_vel stops → FAULT_BIT_WATCHDOG, motors stop.
TEST: LiDAR disconnect during motion → safety_node "LiDAR timeout — STOP".
TEST: Battery 10.4 V (bench PSU) → FAULT_BIT_BATTERY, motors zero.
TEST: Encoder disconnect during motion → FAULT_BIT_ENCODER within 1 s.

---

## Section 14 — PERFORMANCE & OPTIMIZATION

---

### 14.1 PERFORMANCE TARGETS
```
```
| Metric | Target | If exceeded |
|---|---|---|
| Arduino loop period | 10ms ± 0.5ms | Reduce I2C clock |
| Arduino ISR duration | < 10 µs | Simplify ISR body |
| Safety node latency | < 55ms | Reduce to 15Hz |
| E-Stop hardware latency | < 5ms | Check ISR registration |
| Heartbeat timeout action | < 510ms | Check serial throughput |
| /odom publish rate | ~30 Hz | Check TX queue overflow |
| /odom twist accuracy | ±10% of command | Re-check dt handling |
| Max commanded speed | 0.45 teleop / 0.35 auto |  |
| /scan publish rate | ~5.5 Hz | LiDAR hardware issue |
| /kinect/scan publish rate | ~8 Hz | Reduce to 5 Hz (v4.2r3) |
| DDS round-trip (local) | < 20ms | Check WiFi/Tailscale |
| DDS round-trip (remote) | < 100ms | Expected, not an error |
| Jetson container CPU | < 80% | Reduce Kinect FPS |
| Jetson container RAM | < 2.5GB | Check for memory leaks |
| Laptop Nav2 CPU | < 70% | Reduce costmap rate |
| Battery runtime | ~15–20 min | Plan missions shorter |

### 14.2 PROFILING METHODOLOGY
```
STEP 1: docker stats ultron_onboard --format \
        "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
STEP 2: top -b -n 5 -d 2 | grep -E "Cpu|Mem"          # host load
STEP 3: ros2 topic pub /latency_test std_msgs/msg/Header "{stamp: {sec: 0, nanosec: 0}}" --rate 10
        # compare publish vs receive timestamps across DDS (Section 7)
STEP 4: ros2 topic hz /odom /scan /kinect/scan /ultron/heartbeat /imu/data
STEP 5: Arduino timing via scope on a debug pin (pulse < 2ms)
STEP 6: watch -n 5 'free -h && cat /proc/meminfo | grep -E "MemAvailable|SwapFree"'

14.3 FPS TUNING (v4.2r3 — DEFAULT is already 8 FPS / 320×120; tune only if
§3.6 budget exceeded, and never raise the safety-node rate without checking
the stop margin below)
  STAGE 1 — TARGET_FPS 8 → 5 (kinect_driver_node.py + depth_to_scan_node.py)
  STAGE 2 — ROI_HEIGHT 120 → 100 (recenter ROI_Y = 190 to keep the row)
  STAGE 3 — SAFETY RATE: do NOT drop to 10 Hz by default. At 0.35 m/s the
            20 Hz loop keeps the stop margin ≈ 23 mm; at 10 Hz it shrinks to
            ≈ 5–16 mm (LiDAR 180 ms + 100 ms loop + serial + brake). Only
            drop to 10 Hz AND cap Nav2 max_vel_x to 0.25 as a last resort.

```
---

## Section 15 — TROUBLESHOOTING GUIDE (CONSOLIDATED)

---

### 15.1 ARDUINO / SERIAL
```
SYMPTOM: /dev/ultron_arduino not found after plugging in
  CHECK: lsusb | grep -E "2341|1a86"
  FIX 1: Genuine Mega R3 → 2341 (16U2, ttyACM0). Clone → 1a86 (CH340G).
  FIX 2: Verify udev rule: cat /etc/udev/rules.d/99-ultron-v03-arduino.rules
  FIX 3: sudo udevadm control --reload-rules && sudo udevadm trigger
  FIX 4: Unplug and replug the Arduino

SYMPTOM: Permission denied on /dev/ultron_arduino
  FIX: sudo usermod -aG dialout $USER ; log out and back in.
  VERIFY: ls -la /dev/ultron_arduino → crw-rw-rw-

SYMPTOM: Upload fails "programmer not responding"
  FIX 1: Press reset on the Arduino just before upload completes
  FIX 2: arduino-cli board list → arduino:avr:mega
  FIX 3: Check USB cable (data, not charge-only)

SYMPTOM: Serial data garbage / CRC errors
  FIX 1: Baud 115200 both sides
  FIX 2: Check USB cable quality
  FIX 3: On a CH340G clone: setserial low_latency + latency_timer=1.
         On a genuine 16U2 (cdc_acm): none of that applies — check ttyACM.

SYMPTOM: Encoder counts wrong direction
  FIX: Swap encoder A/B wires, or swap motor M+/M− on that driver (two-PWM
       wiring, v4.2r2 D1).

SYMPTOM: Encoder count = 0 always  (v4.2 — right wheel)
  FIX 1: Verify RIGHT encoder is on D52/D51 (v4.2 B1), NOT D23/D24.
  FIX 2: Verify 4.7kΩ pullups and 5V encoder supply.
  FIX 3: PCICR must have PCIE0 set; PCMSK0 bits 1,2 (PB1/PB2).

SYMPTOM: FAULT_LED solid at boot (heartbeat fault)
  CAUSE: Heartbeat watchdog activated before container connects
  FIX: 5s grace period in firmware; start container promptly.

SYMPTOM: "WARN: Previous reset was HW WDT"
  CAUSE: firmware hung; 8s WDT fired. Investigate loops/ISRs. Robot is safe.

15.2 KINECT / DEPTH CAMERA
```
SYMPTOM: "No Kinect found"
  FIX 1: lsusb | grep 045e (on Jetson HOST)
  FIX 2: Verify /dev/bus/usb in compose devices
  FIX 3: Verify 51-kinect.rules applied
  FIX 4: python3 -c "import freenect; ctx=freenect.init(); print(freenect.num_devices(ctx))"

SYMPTOM: /kinect/depth/image_raw publishing but data wrong
  FIX: DEPTH_11BIT mode; ROI within 640×480.

SYMPTOM: /kinect/scan empty or all inf
  FIX: Reduce KINECT_MIN_M (dead zone ~0.5m); tilt calibration.

SYMPTOM (v4.2 H1): /kinect hz drops when WiFi is busy
  CAUSE: Kinect sharing the hub's USB2 bus with the WiFi adapter
  FIX: Move the Kinect to a DIRECT Jetson USB port.

### 15.3 DDS / NETWORK
```
SYMPTOM: ros2 topic list on Laptop shows nothing
  FIX 1: tailscale ping <peer> — must succeed (direct or relay)
  FIX 2: CYCLONEDDS_URI set on BOTH machines (Section 6.3/7)
  FIX 3: ROS_DOMAIN_ID=42 everywhere
  FIX 4: Both IPs present in cyclonedds.xml Peers
  FIX 5: sudo ufw allow 7400:7500/udp + allow in on tailscale0

SYMPTOM: Topics listed but no data flows (silent failure)
  CAUSE: QoS mismatch (reliability differs pub vs sub)
  FIX: Match reliability per Section 7.4; /scan best_effort in Nav2.

SYMPTOM: Tailscale shows "relay" instead of "direct"
  FIX 1: sudo ufw allow 41641/udp on BOTH machines
  FIX 2: Wait 60 s for direct-path negotiation
  FIX 3: Check ISP CGNAT — a relay may be unavoidable (adds latency)

SYMPTOM: High latency (> 200ms) remote
  FIX 1: Force direct (UDP 41641); use 5 GHz WiFi
  FIX 2: Prefer Jetson's Gigabit Ethernet when tethered

SYMPTOM (v4.2 B12): TF/AMCL jumps on the laptop
  CAUSE: Clock skew between Jetson and Laptop
  FIX: chrony running on both (Section 4.5); check chronyc tracking.

15.4 ROS 2 / NAVIGATION
```
SYMPTOM: /scan not appearing
  FIX 1: ls -la /dev/ultron_lidar
  FIX 2: rplidar node started in launch file; baud 115200
  FIX 3: docker exec into container: ros2 topic list

SYMPTOM: /odom drifts or jumps
  FIX 1: Calibrate WHEEL_RADIUS_M / WHEEL_SEP_M
  FIX 2: Drive 1.0m straight → 1.0m ± 0.02m
  FIX 3: Encoder wiring loose; IMU zero-offset

SYMPTOM: /odom twist reads ~3x commanded
  FIX: running old serial_node with hardcoded 0.01s. Use v4.2 node.

SYMPTOM: Nav2 fails "waiting for costmap"
  FIX: /scan QoS best_effort; TF chain map→odom→base_link→laser_link.

SYMPTOM (v4.2r2): Nav2 starts but AMCL localization never locks / no /map update
  CAUSE: AMCL subscribed to /scan with RELIABLE but rplidar publishes
         BEST_EFFORT → silent QoS mismatch, AMCL sees no laser.
  FIX: set amcl param sensor_data_qos: 2 (best_effort) in nav2_params.yaml,
       restart Nav2. Verify: ros2 topic hz /scan on the laptop, and AMCL
       pose in RViz2 tracks the robot.

SYMPTOM: Navigation oscillates / fails to reach goal
  FIX 1: Recalibrate wheel params (most common)
  FIX 2: Tune EKF covariance, DWA params
  FIX 3: inflation_radius > robot_radius

SYMPTOM: Safety node stops robot with no obstacle
  FIX 1: /scan > 4 Hz
  FIX 2: LIDAR_FRONT_ARC_DEG too wide (robot body reflecting) → 60°
  FIX 3: Kinect ROI alignment

### 15.5 DOCKER / SYSTEM
```
SYMPTOM: Docker build fails on Jetson (OOM)
  FIX 1: free -h → Swap > 2G (Section 3.3)
  FIX 2: docker compose build --build-arg MAKEFLAGS=-j2  (v4.2 B11)
  FIX 3: Close other apps during build

SYMPTOM: Container exits immediately / crash loop
  FIX: docker compose logs ultron_onboard --tail 50
  FIX: ls -la /dev/ultron_arduino /dev/ultron_lidar

SYMPTOM: Jetson hangs at boot after USB changes
  CAUSE: /mnt/ssd mounted by node name (/dev/sda1) that shifted
  FIX: mount by UUID with nofail (Section 3.4)

SYMPTOM: High CPU after several hours
  FIX 1: docker stats (memory leak check)
  FIX 2: docker compose restart
  FIX 3: Kinect FRAME_INTERVAL limiting working

SYMPTOM: Jetson thermally throttling
  CHECK: cat /sys/devices/virtual/thermal/thermal_zone*/temp
  FIX 1: sudo jetson_clocks; FIX 2: heatsink/fan; FIX 3: reduce Kinect FPS

SYMPTOM: Battery reports too high (13.5V on full pack)
  FIX: config.h BATTERY_ADC_SCALE must be 0.017418 (reflash)

15.6 DATA COLLECTION / LOGGING (Section 17)
```
SYMPTOM: No log file is written on the laptop
  FIX 1: verify ros2 bag record is running on the laptop (Section 17.4)
  FIX 2: check disk space on the laptop (bags are large)
  FIX 3: data_logger_node enabled=true (jetson_bringup.launch.py)

SYMPTOM: Onboard /mnt/ssd/ultron/logs empty
  FIX 1: check the container mounted /mnt/ssd/ultron (docker inspect)
  FIX 2: verify log_dir exists and is writable by the container user
  FIX 3: mission_id not set — the logger requires a mission_id parameter

---

## Section 16 — DEPLOYMENT MODES

---

### 16.1 LOCAL LAB MODE
```
USE CASE: Development, tuning, SLAM mapping, unit testing.
CHECKLIST:
  ☐ Both machines on same WiFi or Ethernet
  ☐ Tailscale active, direct connection
  ☐ CYCLONEDDS_URI + ROS_DOMAIN_ID set on both (Section 6.3/7)
  ☐ Jetson container running
  ☐ All topics visible: ros2 topic list on Laptop

WORKFLOW:
  1. Start Jetson container (Step 2 of 12.2)
  2. Verify topics flowing
  3. Start nav2_slam (Laptop)
  4. Drive manually with teleop_twist_keyboard
  5. Monitor in RViz2
  6. Save map when environment mapped

TIPS: tmux on Jetson; docker stats in a separate terminal; minicom open.

16.2 REMOTE OPERATION MODE
```
USE CASE: Internet-based supervision and teleoperation.
ADDITIONAL SETUP STEPS:
  tailscale ping <jetson-tailscale-ip>
  ping -c 10 <jetson-tailscale-ip>   # >100ms → caution; >200ms → no teleop
  # Safety validation:
  ros2 topic hz /ultron/heartbeat     # ~10 Hz from Laptop
  ros2 topic echo /safe_cmd_vel      # filtering active

SAFETY RULES FOR REMOTE OPERATION:
  1. NEVER operate remotely without verifying heartbeat is active
  2. NEVER exceed 0.3 m/s during teleoperation over remote network
  3. STOP zone (0.35m) is enforced locally — does NOT depend on network
  4. If RViz2 lags > 2 seconds: stop robot, do not continue

BANDWIDTH ESTIMATION:
  /odom (RELIABLE, 30 Hz, ~200 B):      ~6 KB/s
  /scan (BE, 5.5 Hz, ~2000 B):          ~11 KB/s
  /kinect/scan (BE, 8 Hz, ~3000 B):    ~24 KB/s
  Total minimum: ~41 KB/s ≈ 330 kbps uplink from Jetson. OK on 4G/LTE.

### 16.3 FIELD DEPLOYMENT MODE  (v4.2 B5 — contradiction fixed)
```
USE CASE: Fully autonomous indoor operation in a target room.
  IMPORTANT: Autonomous navigation (Nav2/SLAM/localization) REQUIRES the
  Nav2 machine (laptop) to be on the loop — the Jetson edge layer does NOT
  run Nav2. The operator stays present for the whole supervised session.
  "No-laptop field autonomy" is NOT supported on Ultron_V0.3.

FIELD DEPLOYMENT PROCEDURE:
  1. Pre-deploy: build a SLAM map of the target environment (Local Lab Mode).
  2. Save map to /mnt/ssd/ultron/maps/
  3. Configure nav2_params.yaml (saved-map localization, max_vel_x: 0.35).
  4. Start all containers in order (Section 12.2).
  5. Verify localization: AMCL pose in RViz2 matches physical location.
  6. Set initial pose (2D Pose Estimate in RViz2).
  7. Send initial Nav Goal and verify before releasing.
  8. Keep the laptop/monitor connected for the whole supervised session.

MISSION TIMING (v4.2):
  - Verify /battery/state ≥ 11.1 V before every mission.
  - Keep missions ≤ 12 min of run time.
  - Recharge between missions; keep a spare charged pack.
  - Pilot data missions: start the laptop rosbag + mission_id BEFORE moving
    (Section 17), so the collected data is attributable to the mission.

NETWORK DROP BEHAVIOR:
  Jetson heartbeat to Arduino: continues until Jetson node fails.
  If Jetson node fails: Arduino watchdog 500ms → motors stop.
  If network to laptop drops: Nav2 loses control → cmd_vel stops →
  watchdog 500ms → motors stop. Robot waits for reconnection.
  Recovery: Reconnect laptop, re-authorize, re-send Nav Goal.

AUTO-START ON JETSON BOOT (optional for field):
  # systemd unit for the container stack (RequiresMountsFor handled by
  # the docker drop-in in Section 3.4):
  cat << 'EOF' | sudo tee /etc/systemd/system/ultron-v03.service
  [Unit]
  Description=ultron Docker Stack
  After=docker.service tailscaled.service
  Requires=docker.service

  [Service]
  Type=oneshot
  RemainAfterExit=yes
  WorkingDirectory=/mnt/ssd/ultron/jetson
  ExecStartPre=/bin/sleep 10
  ExecStart=/usr/bin/docker compose up -d
  ExecStop=/usr/bin/docker compose down
  User=jetson

  [Install]
  WantedBy=multi-user.target
  EOF
  sudo systemctl daemon-reload && sudo systemctl enable ultron-v03.service

BATTERY MANAGEMENT IN FIELD:
  Critical 10.5V → Arduino stops motors; Warning 11.1V → battery topic.
  Monitor: ros2 topic echo /battery/state on remote laptop.

PRE-FIELD CHECKLIST:
  ☐ Battery fully charged (12.4–12.6V) and mission fits the 15–20 min budget
  ☐ All nodes verified in lab; map + localization tested on-site
  ☐ E-Stop tested incl. release + clear-faults recovery (B7)
  ☐ Right encoder counts 825/rev (B1)
  ☐ Kinect on a direct USB port (H1), verified hz
  ☐ Overcurrent trip verified (B8)
  ☐ SSD mounted by UUID; boot survives SSD unplug (H2)
  ☐ chrony tracking healthy on both (B12)
  ☐ Headless mode set (multi-user.target); GUI daemons off (3.3)
  ☐ Data collection: laptop rosbag + mission_id verified working (17.4)

```
---

## Section 17 — DATA COLLECTION & LOGGING (V0.3 PILOT)

```

17.1 OBJECTIVE
```
Ultron_V0.3 is the FIRST data-collection pilot of the project. The goal is to
prove the full data pipeline EARLY:
  Collect → Store → (later) Analyze

  ROBOT side:   sensor streams + mission metadata, logged onboard to the SSD.
  LAPTOP side:  rosbag2 of the mission-critical topics (the V0.3 "cloud"),
                plus the derived, anonymized feature files.
  WHY NOW:      prove collection + privacy on V0.3 before any platform changes,
                so the data architecture stays stable.

### 17.2 PRIVACY-BY-DESIGN (NON-NEGOTIABLE — matches AI_Architecture_SHORT.txt)
```
Default is DATA MINIMIZATION:
  WE STORE:   anonymous motion features (counts, flow, dwell), environment
              signals, odometry/SLAM trajectories, logistics timestamps,
              aggregated analytics, fault/battery telemetry.
  WE DO NOT:  store identifiable raw video/faces/names unless an explicit
              consent + ethical-approval gate is met and documented.
  EVERY dataset needs: mission_id, site_id, sensor manifest, start/end time,
              and a retention period. Data is encrypted at rest on the laptop
              (LUKS volume or equivalent) and on the SSD.
  Never upload raw depth/video off-site by default. The robot is a collector;
              the operator laptop is the pilot "cloud".

17.3 WHAT WE COLLECT (V0.3 sensor set)
```
  Telemetry topics (all existing): /odom, /imu/data, /battery/state,
              /ultron/fault, /ultron/heartbeat, /cmd_vel, /safe_cmd_vel.
  Perception: /scan (LiDAR), /kinect/scan (mid-field depth-derived),
              /kinect/depth/image_raw (optional, privacy-gated).
  Derived (laptop, after each mission): anonymous motion features extracted
              from /scan + /kinect/scan (occupancy grid deltas, count/flow/
              dwell estimates). Raw depth is NOT retained by default.
  Mission metadata: mission_id, date, site_id, operator_id, waypoints,
              start/end UTC (chrony-synced), mission result.

### 17.4 IMPLEMENTATION
```
LAPTOP — rosbag record (start BEFORE the mission, stop after):
  cd ~/ultron_laptop && ros2 bag record -s mcap \
      -o ~/ultron_data/<mission_id>/ \
      /odom /imu/data /scan /kinect/scan /battery/state \
      /ultron/fault /ultron/heartbeat /cmd_vel /safe_cmd_vel
  NOTE: mcap format (ros-humble-rosbag2-storage-mcap) is compact and
  indexed — the default .db3 is fine too for pilot scale.

ONBOARD — data_logger_node (new, in ultron_onboard):
  PURPOSE: write a JSONL mission log to /mnt/ssd/ultron/logs/<mission_id>.jsonl
           (battery, faults, mission phase changes, heartbeat health) and keep
           a rolling environment snapshot for post-mission reconciliation.
  PARAMS:  mission_id (required), log_dir (default /mnt/ssd/ultron/logs),
           enabled (default false; enable only during pilot missions).
  The node does NOT write raw depth/video — that stays privacy-gated.

DERIVED FEATURE EXTRACTION (laptop, post-mission):
  A small Python script (analysis/feature_extract.py on the laptop) converts a
  mission bag into anonymous motion features:
    occupancy_deltas, flow_counts, dwell_maps, hot_zone_timestamps
  These feed the "find patterns → predict" loop described in
  AI_Architecture_SHORT.txt. This script runs OFFLINE on the laptop; no
  hospital network is needed for V0.3.

17.5 DIAGNOSTICS (remote-monitoring readiness)
```
Run ros2 diagnostics on the laptop so the remote-monitoring story is proven
on V0.3:
  - ros2 run diagnostic_updater ... / use ros-humble-diagnostic-updater
  - Publish /diagnostics: battery state, node CPU/RAM, topic rates,
    sensor presence, network latency.

### 17.6 OPERATIONAL PROCEDURE (pilot)
```
  1. Check /battery/state ≥ 11.1 V; mission fits the ≤ 12 min rule.
  2. On the laptop: create mission dir, start rosbag record (17.4).
  3. On the Jetson: enable data_logger_node with mission_id, restart launch.
  4. Run the mission (teleop or supervised Nav2). Operator supervises.
  5. Stop the rosbag; stop the logger.
  6. Post-mission: run feature_extract.py; verify the JSONL + bag checksums.
  7. Archive under the site's retention policy; keep the bag off the robot.
  8. Review the run and update the procedure for the next mission.


FINAL VERIFICATION CHECKLIST (Complete System — v4.2)
```
---

NETWORK / DDS (v4.2 B3):
  ☐ tailscale status: "Direct" for both peers (not relay)
  ☐ tailscale ping < 20ms local, < 100ms remote
  ☐ CYCLONEDDS_URI + ROS_DOMAIN_ID=42 set on BOTH machines
  ☐ cyclonedds.xml identical on both; both IPs in Peers
  ☐ ros2 topic list on Laptop shows all 10+ topics (no router)
  ☐ chronyc tracking healthy on both (B12)

STORAGE (v4.2):
  ☐ /mnt/ssd mounted by UUID, nofail (boot survives SSD unplug)
  ☐ docker info → Docker Root Dir: /mnt/ssd/docker
  ☐ ROS workspace on SSD; SD holds OS only
  ☐ Tailscale pinned 1.68.2 (apt-mark hold)
  ☐ Headless multi-user.target; GUI daemons disabled (3.3, reversible)

ARDUINO (v4.2):
  ☐ Boot message: "ultron ready. RAM: > 5500"
  ☐ Heartbeat LED blinks 1 Hz (after container connects); Fault LED OFF
  ☐ Left encoder 825 ± 10 / rev
  ☐ RIGHT encoder 825 ± 10 / rev   (B1 — was 0 before)
  ☐ E-Stop < 5ms; RELEASE + /ultron/clear_faults resumes motors (B7)
  ☐ Heartbeat timeout: FAULT_LED within 500ms of container stop
  ☐ HW WDT (8s): not triggering during normal operation
  ☐ Speed clamp: 0.6 m/s command → ≤ 0.45 m/s
  ☐ Overcurrent: locked wheels → fault bit 1, fuse intact (B8)
  ☐ Battery full pack reads 12.x V (scale 0.017418)

JETSON CONTAINER:
  ☐ /dev/ultron_arduino present (genuine → ttyACM0/cdc_acm)
  ☐ Kinect found (045e:02ae); /kinect/depth ~8 Hz on a DIRECT port (H1)
  ☐ /scan ~5.5 Hz ; /kinect/scan ~8 Hz ; /odom ~30 Hz ; /imu ~30 Hz
  ☐ /ultron/heartbeat ~10 Hz
  ☐ TF: map → odom → base_link → laser_link / kinect_depth_frame / imu_link
  ☐ odom→base_link SINGLE-sourced by laptop EKF (B4)

ODOMETRY:
  ☐ Command 0.30 m/s → twist ≈ 0.30 ± 10%
  ☐ Drive 1.0m straight → 1.0m ± 0.02m
  ☐ Full 360° rotation → theta ≈ 6.28 ± 0.1 rad

QoS:
  ☐ /odom /imu/data /scan echo data flows on Laptop (no timeout)

SAFETY:
  ☐ STOP zone (≤0.35m): safe_cmd_vel = 0
  ☐ SLOW zone (0.50m): ~43% of commanded
  ☐ Turn-in-place side/frontal behavior correct
  ☐ LiDAR timeout → stop within 1.0s
  ☐ Heartbeat timeout → Arduino stop within 500ms
  ☐ Autonomous Nav2 ≤ 0.35 m/s (B6)

NAVIGATION:
  ☐ Teleop all 4 directions; SLAM map builds; map saved
  ☐ Localization active; 2D Nav Goal navigates (laptop present — B5)

POWER:
  ☐ Full charge 12.4–12.6V; warning 11.1V after ~15–20 min typical
  ☐ Missions within the 12-min rule

DATA COLLECTION (Section 17):
  ☐ Laptop rosbag records all pilot topics (mcap); no identifiable video by default
  ☐ data_logger_node writes /mnt/ssd/ultron/logs/<mission_id>.jsonl
  ☐ feature_extract.py produces anonymous motion features per mission
  ☐ /diagnostics present on the laptop (remote-monitoring readiness, 17.5)
  ☐ Privacy checklist signed: consent/approval gate documented for any raw video

CALIBRATION (required before final deployment):
  ☐ WHEEL_RADIUS_M / WHEEL_SEP_M measured + reflashed
  ☐ Static TF xyz measured + updated
  ☐ Drive 1.0m straight: /odom 1.0m ± 0.02m
  ☐ 360°: theta 6.28 ± 0.1 rad
  ☐ Kinect camera calibration (ros2 run camera_calibration)
  ☐ IMU zero-offset verified at startup (stationary 1 s)

## Section 18 — END-USER DEPLOYMENT (TWO-BUNDLE INSTALL)

The complete autonomous system is delivered to an end user as **two install
bundles** (one per machine) plus one **firmware flash**. Install both bundles,
connect the machines with **Tailscale**, and the system runs as one robot.
Transport is **Tailscale + CycloneDDS** — Zenoh was removed in v4.2 (B3).

### 18.1 The two bundles

| Bundle | Runs on | Provides |
|---|---|---|
| **Jetson bundle** | Jetson Nano (Ubuntu 20.04 host, Docker) | serial, safety, kinect, depth-to-scan, data-logger nodes + static TFs |
| **Laptop bundle** | Laptop (Ubuntu 22.04, Docker) | EKF, SLAM / AMCL, Nav2, RViz2, teleop, bag recording |
| **Firmware** (flash) | Arduino Mega 2560 R3 | motor drive, encoders, IMU, E-stop, watchdogs, protocol |

The bundles are the `software/jetson/` and `software/laptop/` folders in this
repo, distributed as zips. No ROS installation is required on either host —
Docker only.

### 18.2 Prerequisites (outside the bundles)

1. Robot assembled per §2 (BOM, wiring, power; B1/D1/H1 notes).
2. Firmware flashed (§11.4); calibration done (§13).
3. One Tailscale account, both machines logged in (§4.1).
4. Jetson host prep: SSD at `/mnt/ssd` by UUID (nofail), Docker data-root on
   SSD (§3.4), udev rules (§5.4), Tailscale pinned 1.68.2, chrony (§4.5).
5. Laptop: Docker, Tailscale, chrony server (§4.5).

### 18.3 The only per-user config

Edit the SHARED `cyclonedds.xml` on both machines with the two Tailscale IPs
(`tailscale ip -4`); use LAN IPs for offline lab sessions (§7.2). Keep the
file byte-identical on both machines.

### 18.4 Build & install

Jetson:
```
./deploy/scripts/install_udev.sh
./deploy/scripts/install_chrony.sh jetson <LAPTOP_TS_IP>
sudo ufw allow 7400:7500/udp && sudo ufw allow 41641/udp
cd software/jetson && docker compose build --build-arg MAKEFLAGS=-j2
docker compose up -d
```
Laptop:
```
sudo ufw allow 7400:7500/udp && sudo ufw allow 41641/udp
./deploy/scripts/install_chrony.sh laptop
cd software/laptop && docker compose build
docker compose up -d nav2_slam
```

### 18.5 Startup order

1. Jetson: `docker compose up -d` → confirm `Serial connected ...`,
   `Kinect depth stream active.`, `Safety node active ...`.
2. Laptop: `nav2_slam`; RViz2 on demand.
3. Verify from the laptop (§7.5): `ros2 topic list`, `ros2 topic hz`.
4. Teleop or 2D Nav Goal (autonomous ≤ 0.35 m/s, laptop present — B5).

### 18.6 First-run failures

90% of first-run failures are: wrong `cyclonedds.xml` IPs / firewall ports
not opened on BOTH machines; AMCL `/scan` QoS mismatch (`sensor_data_qos: 2`
— already default in the bundle); missing `/dev/ultron_*` symlinks (udev);
a latched software E-stop after a clean restart (`clear_faults`). Full
troubleshooting: Section 15.

---

END OF FINAL IMPLEMENTATION BIBLE — Ultron_V0.3
Ultron_V0.3 | Two-Layer | ROS 2 Humble | Docker | Tailscale + CycloneDDS
Version Ultron_V0.3 | 08 August 2026
Corrected canonical reference — Ultron_V0.3 final testing / pre-deployment prototype.
---

