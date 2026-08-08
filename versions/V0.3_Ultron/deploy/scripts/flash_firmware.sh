#!/bin/bash
# Flash the Ultron_V0.3 firmware to the Arduino (Bible §11.4).
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SKETCH="$HERE/firmware/ultron_firmware"
PORT="${1:-/dev/ultron_arduino}"
FQBN="arduino:avr:mega:cpu=atmega2560"

arduino-cli upload -p "$PORT" --fqbn "$FQBN" "$SKETCH"
echo "Flashed. Verify boot message with: minicom -D $PORT -b 115200"
