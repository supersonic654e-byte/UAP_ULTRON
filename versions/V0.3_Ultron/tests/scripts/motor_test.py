#!/usr/bin/env python3
"""MOTOR TEST (Bible §13.1). Robot MUST be lifted off the ground.

  1. Commands both wheels forward at 0.1 m/s for 2 s -> both should spin
     forward (validates the two-PWM BTS7960 wiring, v4.2r2 D1).
  2. Commands 0.6 m/s -> wheels must cap at ~0.45 m/s (speed clamp test).
  3. Sends PKT_ESTOP -> motors must stop.

Usage: python3 motor_test.py --port /dev/ultron_arduino
"""

import argparse
import struct
import time

from serial_tools import (Parser, build_pkt, open_serial, send_stop,
                          PKT_VELOCITY, PKT_RESET_ENC, PKT_CLEAR_FAULTS)


def drive(ser, parser, l, r, seconds):
    vel = struct.pack('>ff', l, r)
    ser.write(build_pkt(PKT_VELOCITY, vel))
    time.sleep(seconds)
    ser.write(build_pkt(PKT_RESET_ENC))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--port', default='/dev/ultron_arduino')
    ap.add_argument('--baud', type=int, default=115200)
    args = ap.parse_args()

    ser = open_serial(args.port, args.baud)
    parser = Parser()
    ser.reset_input_buffer()

    input('Robot LIFTED and clear? Press Enter to run step 1 (0.1 m/s)...')
    print('Step 1: 0.1 m/s both wheels forward for 2 s')
    drive(ser, parser, 0.1, 0.1, 2.0)
    print('Both wheels should have rotated FORWARD. Check wiring D1 if not.')

    input('Press Enter to run step 2 (0.6 m/s clamp test)...')
    print('Step 2: 0.6 m/s both wheels — expect clamp at ~0.45 m/s')
    drive(ser, parser, 0.6, 0.6, 2.0)

    print('Step 3: sending PKT_ESTOP')
    send_stop(ser)
    time.sleep(0.5)
    print('Motors should be stopped and FAULT_LED solid (latched E-stop).')
    # Software E-stop is not a physical latch: the button pin is HIGH, so a
    # CLEAR_FAULTS unlatches the bench (B7 recovery path).
    ser.write(build_pkt(PKT_CLEAR_FAULTS))
    time.sleep(0.3)
    print('CLEAR_FAULTS sent — FAULT_LED should turn off.')
    ser.close()


if __name__ == '__main__':
    main()
