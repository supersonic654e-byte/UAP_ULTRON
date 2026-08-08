#!/usr/bin/env python3
"""Encoder verification (Bible §13.1 — v4.2 B1).

Robot lifted. Rotate ONE wheel by hand for exactly N revolutions; this script
reads the encoder count and checks it equals 825 +/- 10 per revolution.

Usage:
  python3 encoder_verify.py --port /dev/ultron_arduino --wheel left --revs 1
"""

import argparse
import time

from serial_tools import Parser, build_pkt, open_serial, read_for, PKT_RESET_ENC


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', default='/dev/ultron_arduino')
    ap.add_argument('--baud', type=int, default=115200)
    ap.add_argument('--wheel', choices=['left', 'right'], default='left')
    ap.add_argument('--revs', type=float, default=1.0)
    ap.add_argument('--timeout', type=float, default=30.0)
    args = ap.parse_args()

    ser = open_serial(args.port, args.baud)
    parser = Parser()
    ser.reset_input_buffer()
    ser.write(build_pkt(PKT_RESET_ENC))
    time.sleep(0.3)

    print(f'Rotate the {args.wheel} wheel by hand, exactly {args.revs} '
          f'revolutions ({args.revs*825:.0f} +/- 10 ticks).')
    print('Recording (do not move the wheel until timeouts stop)...')

    target = args.revs * 825
    last = (0, 0, 0)
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        r = read_for(ser, parser, 0.3)
        if r['encoder']:
            last = r['encoder']
        if (abs(last[0]) + abs(last[1])) >= target and time.time() > (
                deadline - 2.0):
            break

    l, r, _ = last
    val = abs(l) if args.wheel == 'left' else abs(r)
    ok = abs(val - target) <= 10 * args.revs
    print(f'{args.wheel} encoder = {val} (target {target:.0f}) '
          f'-> {"PASS" if ok else "FAIL"}')
    ser.close()
    raise SystemExit(0 if ok else 1)


if __name__ == '__main__':
    main()
