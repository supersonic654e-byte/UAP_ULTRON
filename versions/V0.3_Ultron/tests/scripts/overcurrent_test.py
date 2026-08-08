#!/usr/bin/env python3
"""OVERCURRENT TEST (Bible §13.1 / §2.4, v4.2 B8).

Lock BOTH wheels (palm-brake / stall), then command 0.3 m/s for > 500 ms.
Expected: FAULT_BIT_OVERCURRENT (bit 1) latches, motors stop, the 15 A fuse
does NOT blow.

Usage: python3 overcurrent_test.py --port /dev/ultron_arduino
"""

import argparse
import struct
import time

from serial_tools import (Parser, build_pkt, open_serial, send_stop,
                          PKT_VELOCITY, PKT_CLEAR_FAULTS)

FAULT_BIT_OVERCURRENT = 1 << 1


def scan_faults(ser, parser, seconds):
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
        if t == 0x04 and len(p) == 1:
            flags = p[0]
    return flags


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', default='/dev/ultron_arduino')
    ap.add_argument('--baud', type=int, default=115200)
    args = ap.parse_args()

    ser = open_serial(args.port, args.baud)
    parser = Parser()
    ser.reset_input_buffer()

    input('LOCK both wheels (stall) and keep them locked. Enter to go...')
    print('Commanding 0.3 m/s for 1.5 s (overcurrent window is 500 ms)...')
    ser.write(build_pkt(PKT_VELOCITY, struct.pack('>ff', 0.3, 0.3)))
    time.sleep(1.5)
    send_stop(ser)

    faults = scan_faults(ser, parser, 2.0)
    ok = bool(faults & FAULT_BIT_OVERCURRENT)
    print(f'FAULT_BIT_OVERCURRENT set: {"PASS" if ok else "FAIL"}')
    print(f'fault_flags=0x{faults:02X}')

    # Clear (button is released, so CLEAR_FAULTS unlatches).
    ser.write(build_pkt(PKT_CLEAR_FAULTS))
    time.sleep(0.3)
    ser.close()

    if not ok:
        print('Check: ACS712 series wiring (A1/A2), 7.0 A threshold, '
              '500 ms window.')
        raise SystemExit(1)


if __name__ == '__main__':
    main()
