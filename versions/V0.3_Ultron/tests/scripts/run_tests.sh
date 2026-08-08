#!/bin/bash
# Run all offline (no-hardware) unit tests.
# Hardware harnesses (motor_test/encoder_test/estop_test/overcurrent_test)
# need the robot and are run manually per tests/procedures/.
set -euo pipefail
cd "$(dirname "$0")"
python3 protocol_test.py
python3 test_safety_node.py
python3 test_depth_scan.py
echo "All offline tests PASSED"
