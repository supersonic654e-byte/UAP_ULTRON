# V0.3 — Firmware (Arduino Mega 2560)

Full buildable sketch in `ultron_firmware/`. Canonical behavior is the
implementation Bible §11; the sketch adds the P0/P1 open work from the
firmware roadmap (wheel velocity PID + IMU DLPF/zero-offset).

## Layout

```
firmware/
├── ultron_firmware/
│   ├── ultron_firmware.ino   # 100 Hz loop, E-stop ISR, watchdogs, PID loop
│   ├── config.h              # pins, timing, kinematics, protocol, fault bits
│   ├── encoders.h/.cpp       # quadrature ISRs (INT3/INT2 left, PCINT0 right)
│   ├── motors.h/.cpp         # Timer3/Timer4 two-PWM 20 kHz drive
│   ├── pid.h/.cpp            # wheel velocity PID (P0)
│   ├── imu.h/.cpp            # MPU6050 I2C, DLPF 42 Hz + gyro zero-offset (P1)
│   ├── protocol.h/.cpp       # CRC-8 binary framing (0xAA/0xBB)
│   ├── tx_queue.h/.cpp       # 4-slot TX queue
│   ├── power.h/.cpp          # battery ADC + overcurrent sampling
│   └── faults.h/.cpp         # fault bit names (debug)
└── README.md
```

> Every `.cpp` includes `<Arduino.h>` explicitly so the split files compile
> under `arduino-cli` (a missing Arduino.h include is the classic sketch-split
> compile failure).

## Build & flash (Bible §11.4)

```bash
arduino-cli compile --fqbn arduino:avr:mega:cpu=atmega2560 ~/ultron_firmware/
arduino-cli upload -p /dev/ultron_arduino --fqbn arduino:avr:mega:cpu=atmega2560 ~/ultron_firmware/
```

or use the helpers: `deploy/scripts/build_firmware.sh`, `flash_firmware.sh`.

## Closed-loop velocity control (P0)

`WHEEL_PID_ENABLED=1` (default) closes the loop on measured wheel speed
(encoder deltas at 100 Hz, low-pass filtered). PID output is PWM in
[-255, 255] with velocity feed-forward, derivative-on-measurement, and
conditional integration. To revert to the Bible's open-loop PWM mapping, set
`WHEEL_PID_ENABLED 0` in `config.h` and reflash.

Tuning knobs in `config.h`: `PID_KP`, `PID_KI`, `PID_KD`,
`PID_FEEDFORWARD`, `PID_INTEGRAL_LIMIT`, `PID_OUTPUT_LIMIT`,
`PID_SPEED_LPF_ALPHA`.

## IMU (P1)

`init_imu()` now sets the 42 Hz DLPF and captures a stationary gyro
zero-offset (rad/s) at boot which is subtracted from every reading. Keep the
robot still ~0.3 s on power-on.

## Protocol summary

- Frame: `[HDR 1B][TYPE 1B][LEN 1B][PAYLOAD][CRC 1B]`, CRC-8 over TYPE+LEN+PAYLOAD.
- Out (0xAA): encoder(0x01), imu(0x02), battery(0x03), fault(0x04).
- In (0xBB): velocity(0x01), estop(0x02), reset_enc(0x03), heartbeat(0x05),
  clear_faults(0x07).
