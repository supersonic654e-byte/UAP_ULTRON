#!/bin/bash
# Run all offline (no-hardware) unit tests.
# Hardware harnesses (motor_test/encoder_test/estop_test/overcurrent_test)
# need the robot and are run manually per tests/procedures/.
set -euo pipefail
cd "$(dirname "$0")"

echo "== firmware/ROS offline tests =="
python3 protocol_test.py
python3 test_safety_node.py
python3 test_depth_scan.py

echo "== web control system tests (needs fastapi+pytest) =="
if python3 -c "import fastapi, httpx" 2>/dev/null; then
    python3 -m pytest -q ../../software/web/tests
else
    echo "  SKIPPED — install web deps first: pip install -r ../../software/web/requirements.txt pytest httpx"
fi

echo "All offline tests PASSED"
