#!/usr/bin/env python3
"""Wheel geometry calibration (Bible §13/calibration).

Procedure:
  1. Robot on the bench or a clean straight 1 m strip.
  2. Mark a start line on the floor aligned with the front axle center.
  3. Drive the robot forward at a known speed for a measured time, OR until
     it crosses the 1.000 m mark. Measure the ACTUAL traveled distance with a
     tape measure (best effort).
  4. This script reads the true encoder tick delta from the Arduino and
     prints the corrected METERS_PER_TICK and WHEEL_RADIUS_M.

Usage:
  python3 wheel_geometry_calib.py --port /dev/ultron_arduino \
      --measured-m 1.000

Output constants are printed; reflash config.h with them and re-run
`encoder_verify.py` to confirm 825 +/- 10 ticks/rev.
"""

import argparse
import struct
import time

from serial_tools import (Parser, build_pkt, open_serial, read_for,
                          PKT_RESET_ENC, PKT_VELOCITY, TICKS_PER_REV)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', default='/dev/ultron_arduino')
    ap.add_argument('--baud', type=int, default=115200)
    ap.add_argument('--speed', type=float, default=0.2,
                    help='command speed (m/s) during the run')
    ap.add_argument('--duration', type=float, default=5.0,
                    help='drive time (s)')
    ap.add_argument('--measured-m', type=float, required=True,
                    help='actual distance traveled, tape-measured (m)')
    args = ap.parse_args()

    ser = open_serial(args.port, args.baud)
    parser = Parser()

    # Drain stale bytes and reset encoders.
    ser.reset_input_buffer()
    ser.write(build_pkt(PKT_RESET_ENC))
    time.sleep(0.5)

    print(f'Driving at {args.speed} m/s for {args.duration}s...')
    vel = struct.pack('>ff', args.speed, args.speed)
    ser.write(build_pkt(PKT_VELOCITY, vel))

    # Sample encoder deltas over the run.
    samples = []
    start = time.time()
    while time.time() - start < args.duration:
        r = read_for(ser, parser, 0.5)
        if r['encoder']:
            samples.append(r['encoder'])

    # Stop.
    ser.write(build_pkt(PKT_ESTOP))

    if len(samples) < 2:
        print('ERROR: not enough encoder packets received. Check wiring/B1.')
        ser.close()
        raise SystemExit(1)

    first = samples[0]
    last = samples[-1]
    dl = abs(last[0] - first[0])
    dr = abs(last[1] - first[1])
    ticks = (dl + dr) / 2.0
    if ticks <= 0:
        print('ERROR: zero encoder movement recorded.')
        ser.close()
        raise SystemExit(1)

    meters_per_tick = args.measured_m / ticks
    radius = meters_per_tick * TICKS_PER_REV / (6.28318530718)
    separation = args.measured_m / (args.speed * args.duration) * 0.3556

    print('--- RESULTS ---')
    print(f'encoder ticks (avg wheel): {ticks:.0f}')
    print(f'METERS_PER_TICK  = {meters_per_tick:.8f}  (was 0.00029013)')
    print(f'WHEEL_RADIUS_M   = {radius:.6f}  (was 0.0381)')
    print(f'WHEEL_SEP_M (est)= {separation:.6f}  (measure directly, do not '
          f'derive)')
    print('--- ACTION ---')
    print('Reflash config.h with the new constants, then run '
          'encoder_verify.py and the 1.0 m straight-line test.')
    ser.close()


if __name__ == '__main__':
    main()
