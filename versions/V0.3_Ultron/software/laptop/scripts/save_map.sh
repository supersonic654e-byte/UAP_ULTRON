#!/bin/bash
# Save the current SLAM map to the shared maps volume.
# Usage: ./save_map.sh [map_name]   (default: map)
set -euo pipefail
source /opt/ros/humble/setup.bash
MAP_NAME="${1:-map}"
ros2 run nav2_map_server map_saver_cli -f "/ultron_laptop/maps/$MAP_NAME"
echo "Map saved to /ultron_laptop/maps/$MAP_NAME.{pgm,yaml}"
