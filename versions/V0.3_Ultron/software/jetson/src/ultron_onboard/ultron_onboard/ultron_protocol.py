"""Ultron_V0.3 Arduino binary protocol (byte-for-byte mirror of the firmware).

Frame: [HDR 1B][TYPE 1B][LEN 1B][PAYLOAD 0-255B][CRC 1B]
  HDR:  0xAA Arduino->Jetson, 0xBB Jetson->Arduino
  CRC:  CRC-8-CCITT poly 0x07 init 0x00 over TYPE+LEN+PAYLOAD
  Byte order: BIG-ENDIAN

This module has NO ROS dependency so it can be unit-tested standalone and
reused verbatim by `serial_node` and the calibration/test harnesses.
"""

HDR_OUT = 0xAA          # Arduino -> Jetson
HDR_IN = 0xBB           # Jetson -> Arduino

PKT_ENCODER = 0x01      # -> out: int32 left, int32 right, uint32 ts_ms (12B)
PKT_IMU = 0x02          # -> out: float ax,ay,az,gx,gy,gz (24B)
PKT_BATTERY = 0x03      # -> out: float volts (4B)
PKT_FAULT = 0x04        # -> out: uint8 fault_flags (1B)
PKT_HEARTBEAT = 0x05    # -> in:  uint8 seq; -> out: same

PKT_VELOCITY = 0x01     # in: float vel_left, vel_right (8B, m/s)
PKT_ESTOP = 0x02        # in: no payload
PKT_RESET_ENC = 0x03    # in: no payload
PKT_CLEAR_FAULTS = 0x07  # in: no payload (v4.2 B7)

# Kinematics (must match config.h)
WHEEL_RADIUS_M = 0.0381
WHEEL_SEP_M = 0.3556
TICKS_PER_REV = 825
METERS_PER_TICK = 3.141592653589793 * (WHEEL_RADIUS_M * 2) / TICKS_PER_REV
MAX_SPEED_MPS = 0.45    # teleop clamp (autonomous capped at 0.35 by Nav2)

FAULT_BIT_ESTOP = 1 << 0
FAULT_BIT_OVERCURRENT = 1 << 1
FAULT_BIT_WATCHDOG = 1 << 2
FAULT_BIT_IMU = 1 << 3
FAULT_BIT_ENCODER = 1 << 4
FAULT_BIT_BATTERY = 1 << 5
FAULT_BIT_HEARTBEAT = 1 << 6


def crc8(data):
    """CRC-8-CCITT, poly 0x07, init 0x00. Must match firmware crc8()."""
    crc = 0
    for b in data:
        crc ^= b
        for _ in range(8):
            crc = ((crc << 1) ^ 0x07) if (crc & 0x80) else (crc << 1)
            crc &= 0xFF
    return crc


def build_pkt(pkt_type, payload=b""):
    """Build a Jetson->Arduino frame (HDR_IN)."""
    hdr = bytes([HDR_IN, pkt_type, len(payload)])
    body = hdr + payload
    return body + bytes([crc8(body[1:])])


class FrameParser:
    """Incremental state machine for Arduino->Jetson frames.

    Feed bytes one at a time with `.push(b)`; a complete valid frame returns
    a (pkt_type, payload) tuple, otherwise None. Corrupt frames are dropped
    and the machine resynchronizes on the next 0xAA.
    """

    def __init__(self):
        self.reset()

    def reset(self):
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


def unpack_encoder(payload):
    import struct
    if len(payload) != 12:
        raise ValueError('encoder payload must be 12 bytes')
    return struct.unpack('>iiI', payload)


def unpack_imu(payload):
    import struct
    if len(payload) != 24:
        raise ValueError('imu payload must be 24 bytes')
    return struct.unpack('>ffffff', payload)


def twist_to_wheel_speeds(linear_x, angular_z):
    """Differential-drive kinematics: (v_left, v_right) in m/s, clamped to
    MAX_SPEED_MPS. Pure function (mirrors serial_node.cmd_cb)."""
    vl = linear_x - (angular_z * WHEEL_SEP_M / 2.0)
    vr = linear_x + (angular_z * WHEEL_SEP_M / 2.0)
    vl = max(-MAX_SPEED_MPS, min(MAX_SPEED_MPS, vl))
    vr = max(-MAX_SPEED_MPS, min(MAX_SPEED_MPS, vr))
    return vl, vr


def velocity_packet(linear_x, angular_z):
    """Build the full PKT_VELOCITY frame (HDR_IN) for a Twist command."""
    import struct
    vl, vr = twist_to_wheel_speeds(linear_x, angular_z)
    payload = struct.pack('>ff', vl, vr)
    return build_pkt(PKT_VELOCITY, payload)
