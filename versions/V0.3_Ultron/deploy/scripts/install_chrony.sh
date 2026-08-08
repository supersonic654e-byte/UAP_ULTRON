#!/bin/bash
# Install chrony time sync (Bible §4.5 B12).
# Usage:
#   ./install_chrony.sh jetson <LAPTOP_TS_IP>
#   ./install_chrony.sh laptop
set -euo pipefail
HERE="$(cd "$(dirname "$0")/.." && pwd)"
MODE="${1:?usage: install_chrony.sh <jetson|laptop> [laptop_ts_ip]}"

sudo apt-get install -y chrony

case "$MODE" in
  jetson)
    IP="${2:?usage: install_chrony.sh jetson <laptop_ts_ip>}"
    sed "s#<LAPTOP_TS_IP>#$IP#" "$HERE/chrony/jetson-chrony.conf" \
        | sudo tee /etc/chrony/chrony.conf > /dev/null
    ;;
  laptop)
    sudo cp "$HERE/chrony/laptop-chrony.conf" /etc/chrony/chrony.conf
    ;;
  *) echo "mode must be jetson|laptop"; exit 1 ;;
esac

sudo systemctl restart chrony
echo "chrony installed. Verify with: chronyc tracking"
