#!/bin/bash
set -e
source /opt/ros/humble/setup.bash
[ -f /ultron_ws/install/setup.bash ] && \
    source /ultron_ws/install/setup.bash
[ -e /dev/ultron_arduino ] && \
    setserial /dev/ultron_arduino low_latency 2>/dev/null || true
[ -e /dev/ultron_lidar ] && \
    setserial /dev/ultron_lidar low_latency 2>/dev/null || true
exec "$@"
