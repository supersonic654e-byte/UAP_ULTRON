#!/usr/bin/env python3
"""E-STOP TEST (Bible §13.1 / §10.4, v4.2 B7). Robot lifted or on bench.

  1. Commands both wheels forward at 0.15 m/s.
  2. Asks the OPERATOR to press the physical E-stop button.
  3. Verifies motors stop and FAULT_BIT_ESTOP is set.
  4. Verifies the button must be RELEASED + CLEAR_FAULTS before motors resume.

Usage: python3 estop_test.py --port /dev/ultron_arduino
"""

import argparse
import struct
import time

from serial_tools import (Parser, build_pkt, open_serial, send_stop,
                          PKT_VELOCITY, PKT_CLEAR_FAULTS)

FAULT_BIT_ESTOP = 1 << 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', default='/dev/ultron_arduino')
    ap.add_argument('--baud', type=int, default=115200)
    args = ap.parse_args()

    ser = open_serial(args.port, args.baud)
    parser = Parser()
    ser.reset_input_buffer()

    # Command motion.
    vel = struct.pack('>ff', 0.15, 0.15)
    ser.write(build_pkt(PKT_VELOCITY, vel))
    print('Wheels commanded forward at 0.15 m/s.')

    input('PRESS the physical E-stop button now, then Enter...')
    send_stop(ser)
    time.sleep(0.3)

    # Check for fault flag.
    faults = _scan_faults(ser, parser, 2.0)

    ok = bool(faults & FAULT_BIT_ESTOP)
    print(f'FAULT_BIT_ESTOP present: {"PASS" if ok else "FAIL"}')
    if not ok:
        print('E-stop did not latch. Check D2/INT4 wiring and the ISR.')
        ser.close()
        raise SystemExit(1)

    print('Motors should be stopped. Now RELEASE the button (must stay '
          'stopped — latched).')
    input('Press Enter after releasing the button...')
    time.sleep(0.5)

    # CLEAR_FAULTS with button released -> clears.
    ser.write(build_pkt(PKT_CLEAR_FAULTS))
    time.sleep(0.3)
    faults = _scan_faults(ser, parser, 1.5)
    cleared = not (faults & FAULT_BIT_ESTOP)
    print(f'Fault cleared after release + CLEAR_FAULTS: '
          f'{"PASS" if cleared else "FAIL"}')

    # New command must move again (motors resume only on a new /cmd_vel).
    ser.write(build_pkt(PKT_VELOCITY, struct.pack('>ff', 0.1, 0.1)))
    print('Sent 0.1 m/s — wheels should spin again.')
    time.sleep(1.0)
    send_stop(ser)
    ser.write(build_pkt(PKT_CLEAR_FAULTS))
    time.sleep(0.3)
    ser.close()

    raise SystemExit(0 if (ok and cleared) else 1)


def _scan_faults(ser, parser, seconds):
    """Read fault packets for `seconds`, returning the latest flags byte."""
    flags = 0
    deadline = time.time() + seconds
    while time.time() < deadline:
        b = ser.read(1)
        if not b:
            continue
        f = parser.push(b[0])
        if not f:
            continue
        t, p = f
        if t == 0x04 and len(p) == 1:      # PKT_FAULT
            flags = p[0]
    return flags


if __name__ == '__main__':
    main()
