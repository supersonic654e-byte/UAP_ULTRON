#!/bin/bash
# Keyboard teleop for Ultron_V0.3. Remaps twist to the Nav2/teleop topic.
# Usage: ./start_teleop.sh   (within the laptop container or sourced env)
set -euo pipefail
source /opt/ros/humble/setup.bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard \
    --ros-args -r /cmd_vel:=/cmd_vel
