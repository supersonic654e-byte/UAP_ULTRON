"""Shared serial/protocol helpers for calibration and bench harnesses.

Mirrors the firmware frame format byte-for-byte (see software/jetson/src/
ultron_onboard/ultron_protocol.py). Keep both in sync with config.h.
"""

import struct

import serial

HDR_IN = 0xBB            # Jetson -> Arduino
HDR_OUT = 0xAA           # Arduino -> Jetson
PKT_VELOCITY = 0x01
PKT_ESTOP = 0x02
PKT_RESET_ENC = 0x03
PKT_HEARTBEAT = 0x05
PKT_CLEAR_FAULTS = 0x07
PKT_ENCODER = 0x01
PKT_IMU = 0x02
PKT_BATTERY = 0x03
PKT_FAULT = 0x04

TICKS_PER_REV = 825
METERS_PER_TICK = 0.00029013


def crc8(data):
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) if (crc & 0x80) else (crc << 1)
            crc &= 0xFF
    return crc


def build_pkt(pkt_type, payload=b""):
    hdr = bytes([HDR_IN, pkt_type, len(payload)])
    body = hdr + payload
    return body + bytes([crc8(body[1:])])


def open_serial(port, baud=115200):
    return serial.Serial(port, baud, timeout=0.2)


class Parser:
    """Incremental frame parser for Arduino->Jetson (HDR 0xAA) frames."""

    def __init__(self):
        self._state = 'W'
        self._type = 0
        self._len = 0
        self._buf = bytearray()

    def push(self, b):
        b = int(b)
        if self._state == 'W':
            if b == HDR_OUT:
                self._state = 'T'
        elif self._state == 'T':
            self._type = b
            self._buf = bytearray([b])
            self._state = 'L'
        elif self._state == 'L':
            self._len = b
            self._buf.append(b)
            self._state = 'P' if self._len > 0 else 'C'
        elif self._state == 'P':
            self._buf.append(b)
            if len(self._buf) == 2 + self._len:
                self._state = 'C'
        elif self._state == 'C':
            valid = crc8(bytes(self._buf)) == b
            self._state = 'W'
            if valid:
                return (self._type, bytes(self._buf[2:]))
        return None


def read_for(ser, parser, seconds):
    """Read serial for `seconds`, returning the last encoder (l, r, ts) and
    imu (6-tuple) and battery (float) observed. Returns dict."""
    out = {'encoder': None, 'imu': None, 'battery': None}
    import time
    deadline = time.time() + seconds
    while time.time() < deadline:
        b = ser.read(1)
        if not b:
            continue
        frame = parser.push(b[0])
        if not frame:
            continue
        t, p = frame
        if t == PKT_ENCODER and len(p) == 12:
            out['encoder'] = struct.unpack('>iiI', p)
        elif t == PKT_IMU and len(p) == 24:
            out['imu'] = struct.unpack('>ffffff', p)
        elif t == PKT_BATTERY and len(p) == 4:
            out['battery'] = struct.unpack('>f', p)[0]
    return out


def send_stop(ser):
    ser.write(build_pkt(PKT_ESTOP))
