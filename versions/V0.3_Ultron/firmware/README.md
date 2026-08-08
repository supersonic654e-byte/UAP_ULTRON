# V0.3 — Firmware

Arduino Mega 2560 firmware. Full source and protocol are embedded in the
implementation Bible §11; when we split it into real files they land here.

## Planned layout

```
firmware/
├── ultron_firmware/
│   ├── ultron_firmware.ino
│   ├── config.h          # pins, timing, kinematics, protocol, fault bits
│   ├── encoders.h/.cpp   # quadrature ISRs (INT3/INT2 left, PCINT0 right)
│   ├── motors.h/.cpp     # Timer3/Timer4 two-PWM 20 kHz drive
│   ├── imu.h/.cpp        # MPU6050 I2C read (DLPF + offset cal pending)
│   ├── protocol.h/.cpp   # CRC-8 binary framing (0xAA/0xBB)
│   ├── tx_queue.h/.cpp   # 4-slot TX queue
│   ├── power.h/.cpp      # battery ADC + overcurrent sampling
│   └── faults.h/.cpp     # fault bit names (debug)
└── README.md
```

## Build & flash (from the Bible §11.4)

```bash
arduino-cli compile --fqbn arduino:avr:mega:cpu=atmega2560 ~/ultron_firmware/
arduino-cli upload -p /dev/ultron_arduino --fqbn arduino:avr:mega:cpu=atmega2560 ~/ultron_firmware/
```

## Open work (P0/P1)

- **Wheel velocity PID** (P0) — closes the open-loop gap before Nav2 reliance.
- **IMU DLPF + offset calibration** (P1).
- Migration to PlatformIO for CI-able builds (recommended).

## Protocol summary

- Frame: `[HDR 1B][TYPE 1B][LEN 1B][PAYLOAD][CRC 1B]`, CRC-8 over TYPE+LEN+PAYLOAD.
- Out: encoder(0x01), imu(0x02), battery(0x03), fault(0x04), heartbeat(0x05).
- In: velocity(0x01), estop(0x02), reset_enc(0x03), heartbeat(0x05),
  clear_faults(0x07).
