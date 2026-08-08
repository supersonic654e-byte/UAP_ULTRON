#!/bin/bash
# Install Ultron_V0.3 udev rules on the Jetson (Bible §5.4).
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
sudo cp "$HERE/udev"/*.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules && sudo udevadm trigger
sudo usermod -aG dialout "$USER"
sudo usermod -aG plugdev "$USER"
echo "udev rules installed. Re-plug devices. Verify:"
echo "  ls -la /dev/ultron_arduino /dev/ultron_lidar"
echo "  lsusb | grep -E '2341|1a86|10c4|045e'"
