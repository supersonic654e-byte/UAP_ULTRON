#!/usr/bin/env python3
"""IMU zero-offset verification (Bible §13.1 / calibration P1).

Place the robot level and stationary for ~3 s. Reads /imu/data via serial and
prints the mean gyro bias (rad/s) the firmware subtracts at init, plus the
current live reading so you can confirm it is near zero.

Note: the firmware already captures its own bias at boot (imu.cpp). This tool
is a verification harness, not a reflash step.

Usage:
  python3 imu_offset_calib.py --port /dev/ultron_arduino
"""

import argparse
import time

from serial_tools import Parser, open_serial, read_for


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', default='/dev/ultron_arduino')
    ap.add_argument('--baud', type=int, default=115200)
    ap.add_argument('--duration', type=float, default=3.0)
    args = ap.parse_args()

    ser = open_serial(args.port, args.baud)
    parser = Parser()
    ser.reset_input_buffer()

    print(f'Keep the robot STATIONARY and LEVEL for {args.duration:.0f}s...')
    sums = [0.0] * 6
    n = 0
    deadline = time.time() + args.duration
    while time.time() < deadline:
        r = read_for(ser, parser, 0.5)
        if r['imu']:
            for i, v in enumerate(r['imu']):
                sums[i] += v
            n += 1

    ser.close()
    if n == 0:
        print('ERROR: no IMU packets received (check MPU6050 wiring/S1).')
        raise SystemExit(1)
    mean = [s / n for s in sums]
    print('--- Stationary means ---')
    print(f'accel (m/s^2): ax={mean[0]:+.3f} ay={mean[1]:+.3f} '
          f'az={mean[2]:+.3f}  (expect az ~ +9.81)')
    print(f'gyro (rad/s):  gx={mean[3]:+.4f} gy={mean[4]:+.4f} '
          f'gz={mean[5]:+.4f}  (expect ~ 0.0000)')
    gyro_ok = all(abs(v) < 0.03 for v in mean[3:6])
    print('Gyro offset check:', 'PASS' if gyro_ok else 'FAIL (verify mounting '
          'and DLPF/offset calibration)')
    raise SystemExit(0 if gyro_ok else 1)


if __name__ == '__main__':
    main()
