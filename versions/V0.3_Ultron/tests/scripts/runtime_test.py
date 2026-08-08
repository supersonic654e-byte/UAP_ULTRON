#!/usr/bin/env python3
"""BATTERY RUNTIME TEST (Bible §13.1 / §2.4).

Samples /battery/state via serial at a fixed rate and writes a CSV so the
voltage-vs-time curve can be plotted. Run on a full pack under typical load
until the 11.1 V warning appears (~15-20 min expected).

Usage: python3 runtime_test.py --port /dev/ultron_arduino \
        --out runtime_2026-08-08.csv --interval 10
"""

import argparse
import csv
import time

from serial_tools import Parser, open_serial, read_for


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', default='/dev/ultron_arduino')
    ap.add_argument('--baud', type=int, default=115200)
    ap.add_argument('--out', required=True)
    ap.add_argument('--interval', type=float, default=10.0,
                    help='sample period (s)')
    args = ap.parse_args()

    ser = open_serial(args.port, args.baud)
    parser = Parser()
    ser.reset_input_buffer()

    with open(args.out, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['t_elapsed_s', 'battery_v'])
        start = time.time()
        print(f'Logging to {args.out} every {args.interval}s. Ctrl-C to stop.')
        while True:
            elapsed = time.time() - start
            r = read_for(ser, parser, 0.5)
            v = r.get('battery')
            if v is None:
                print(f'[{elapsed:6.0f}s] no battery packet')
            else:
                w.writerow([round(elapsed, 1), round(v, 3)])
                f.flush()
                flag = ' <-- WARNING 11.1V' if v <= 11.1 else ''
                print(f'[{elapsed:6.0f}s] {v:.3f} V{flag}')
            time.sleep(args.interval)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nStopped.')
