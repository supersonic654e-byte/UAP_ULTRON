#!/usr/bin/env python3
"""Battery ADC scale verification (Bible §13.1 / §2.2).

Compare the Arduino-reported voltage against a multimeter on the battery
terminals and print the corrected BATTERY_ADC_SCALE.

Usage:
  python3 battery_scale_verify.py --port /dev/ultron_arduino \
      --multimeter-v 12.34
"""

import argparse
import time

from serial_tools import Parser, open_serial, read_for


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', default='/dev/ultron_arduino')
    ap.add_argument('--baud', type=int, default=115200)
    ap.add_argument('--multimeter-v', type=float, required=True,
                    help='multimeter reading across the battery (V)')
    args = ap.parse_args()

    ser = open_serial(args.port, args.baud)
    parser = Parser()
    ser.reset_input_buffer()

    print('Sampling /battery packets for 3 s...')
    total = 0.0
    n = 0
    deadline = time.time() + 3.0
    while time.time() < deadline:
        r = read_for(ser, parser, 0.5)
        if r['battery']:
            total += r['battery']
            n += 1

    ser.close()
    if n == 0:
        print('ERROR: no battery packets received.')
        raise SystemExit(1)
    reported = total / n
    scale = 0.017418 * (args.multimeter_v / reported)
    print(f'Reported avg: {reported:.3f} V  (multimeter: '
          f'{args.multimeter_v:.3f} V)')
    print(f'Corrected BATTERY_ADC_SCALE = {scale:.6f}  (was 0.017418)')
    print('Reflash config.h if the scale changed by more than ~0.0005.')


if __name__ == '__main__':
    main()
