#!/usr/bin/env python3
"""Cross-verification of the serial protocol against an independent
reference implementation (byte-for-byte mirror of the C firmware).

Run standalone:  python3 protocol_test.py
Or via pytest:   pytest -q tests/scripts/protocol_test.py
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))


def _pkg_dir():
    """Locate the ultron_onboard python package dir (inner) in the repo."""
    root = _HERE
    while not os.path.isdir(os.path.join(root, 'versions')) and \
            os.path.dirname(root) != root:
        root = os.path.dirname(root)
    inner = os.path.join(root, 'versions', 'V0.3_Ultron', 'software', 'jetson',
                         'src', 'ultron_onboard', 'ultron_onboard')
    if not os.path.isdir(inner):
        raise RuntimeError('could not locate repo src tree from ' + _HERE)
    return inner


sys.path.insert(0, _pkg_dir())
import ultron_protocol as P  # noqa: E402


def reference_crc8(data):
    """Independent CRC-8-CCITT (poly 0x07, init 0x00) written differently."""
    crc = 0
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x80:
                crc = ((crc << 1) ^ 0x07) & 0xFF
            else:
                crc = (crc << 1) & 0xFF
    return crc


def reference_build(hdr, pkt_type, payload):
    """Independent frame builder (C firmware layout)."""
    body = bytes([hdr, pkt_type, len(payload)]) + bytes(payload)
    return body + bytes([reference_crc8(body[1:])])


def test_crc_matches_reference():
    vectors = [b'', b'\x00', b'\x01\x02\x03', bytes(range(16)),
               b'\x01\x08\x00\x00\x00\x00\x00\x00\x00\x00']
    for v in vectors:
        assert P.crc8(v) == reference_crc8(v), v


def test_velocity_packet_layout():
    # 0.1 m/s both wheels -> payload = BE floats of (0.1, 0.1)
    pkt = P.velocity_packet(0.1, 0.0)
    assert pkt[0] == P.HDR_IN
    assert pkt[1] == P.PKT_VELOCITY
    assert pkt[2] == 8
    assert len(pkt) == 12
    import struct
    vl, vr = struct.unpack('>ff', pkt[3:11])
    assert abs(vl - 0.1) < 1e-6 and abs(vr - 0.1) < 1e-6
    # CRC covers TYPE+LEN+PAYLOAD (indices 1..10)
    assert pkt[11] == reference_crc8(pkt[1:11])


def test_twist_to_wheel_speeds():
    vl, vr = P.twist_to_wheel_speeds(0.2, 0.0)
    assert abs(vl - 0.2) < 1e-9 and abs(vr - 0.2) < 1e-9
    # Pure rotation: opposite wheel speeds.
    vl, vr = P.twist_to_wheel_speeds(0.0, 1.0)
    assert abs(vl + P.WHEEL_SEP_M / 2.0) < 1e-9
    assert abs(vr - P.WHEEL_SEP_M / 2.0) < 1e-9
    # Clamp to MAX_SPEED_MPS.
    vl, vr = P.twist_to_wheel_speeds(10.0, 0.0)
    assert vl == P.MAX_SPEED_MPS and vr == P.MAX_SPEED_MPS


def test_parser_roundtrip_encoder():
    # Build an encoder frame exactly as the C firmware would.
    l, r, ts = 12345, -6789, 543210
    payload = ((l).to_bytes(4, 'big', signed=True) +
               (r).to_bytes(4, 'big', signed=True) +
               (ts).to_bytes(4, 'big'))
    frame = reference_build(P.HDR_OUT, P.PKT_ENCODER, payload)
    parser = P.FrameParser()
    got = None
    for b in frame:
        got = parser.push(b)
    assert got == (P.PKT_ENCODER, payload)
    assert P.unpack_encoder(payload) == (l, r, ts)


def test_parser_rejects_bad_crc_and_resyncs():
    parser = P.FrameParser()
    bad = reference_build(P.HDR_OUT, P.PKT_BATTERY, b'\x00\x00\x00\x00')
    corrupted = bad[:-1] + bytes([bad[-1] ^ 0xFF])
    got = None
    for b in corrupted:
        got = parser.push(b)
    assert got is None
    # A valid frame immediately after must be parsed (resync works).
    good = reference_build(P.HDR_OUT, P.PKT_BATTERY, b'\x3f\x99\x99\x9a')
    for b in good:
        got = parser.push(b)
    assert got == (P.PKT_BATTERY, b'\x3f\x99\x99\x9a')


def test_clear_faults_packet():
    pkt = P.build_pkt(P.PKT_CLEAR_FAULTS, b'')
    assert pkt == bytes([P.HDR_IN, 0x07, 0x00, reference_crc8([0x07, 0x00])])


def test_esTOP_packet():
    pkt = P.build_pkt(P.PKT_ESTOP, b'')
    assert pkt == bytes([P.HDR_IN, 0x02, 0x00, reference_crc8([0x02, 0x00])])


if __name__ == '__main__':
    import pytest
    sys.exit(pytest.main([__file__, '-v']))
