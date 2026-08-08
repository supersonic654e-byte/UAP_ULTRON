#!/bin/bash
# Environment verification for Ultron_V0.3 (Bible §7.5, §16 final checklist).
# Run on the JETSON host (or in the container) after bring-up.
set -uo pipefail

echo "== /dev symlinks =="
ls -la /dev/ultron_arduino /dev/ultron_lidar 2>&1 | grep -E 'ultron_|No such'

echo "== Tailscale =="
tailscale status 2>/dev/null | head -5 || echo "tailscale not up"

echo "== DDS env =="
echo "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION:-<unset>}"
echo "ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-<unset>}"
echo "CYCLONEDDS_URI=${CYCLONEDDS_URI:-<unset>}"

echo "== Topic rates (10 s) =="
for t in /odom /scan /kinect/scan /ultron/heartbeat /imu/data /battery/state; do
  printf '%-22s ' "$t"
  timeout 10 ros2 topic hz "$t" 2>/dev/null | grep -m1 'average rate' \
      || echo "no data"
done

echo "== TF tree =="
ros2 run tf2_tools view_frames 2>/dev/null || true
echo "done."
