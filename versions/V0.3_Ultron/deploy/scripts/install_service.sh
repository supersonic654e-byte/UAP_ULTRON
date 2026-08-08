#!/bin/bash
# Install the optional auto-start systemd unit (Bible §16.3).
# Run on the Jetson. Adjust WorkingDirectory/User in the unit if needed.
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
sudo cp "$HERE/systemd/ultron-v03.service" /etc/systemd/system/
sudo mkdir -p /etc/systemd/system/docker.service.d
sudo cp "$HERE/systemd/docker-ssd-wait.conf" \
     /etc/systemd/system/docker.service.d/
sudo systemctl daemon-reload
sudo systemctl enable ultron-v03.service
echo "ultron-v03.service enabled (starts the compose stack at boot)."
