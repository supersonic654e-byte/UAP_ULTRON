#!/bin/bash
# Compile the Ultron_V0.3 firmware (Bible §11.4).
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
SKETCH="$HERE/firmware/ultron_firmware"
FQBN="arduino:avr:mega:cpu=atmega2560"

arduino-cli compile --fqbn "$FQBN" "$SKETCH"
echo "Firmware compiled OK."
