#!/usr/bin/env bash
# Pre-session smoke test for Ultron_V0.3 (run on the laptop, robot powered).
# Fails fast so we don't discover a dead link mid-mission.
set -euo pipefail

DOMAIN=42
export ROS_DOMAIN_ID=${DOMAIN}

echo "== [1/5] DDS link =="
timeout 15 ros2 topic list >/dev/null || { echo "FAIL: ros2 topic list (check Tailscale + cyclonedds.xml)"; exit 1; }
echo "ok"

echo "== [2/5] core topics =="
for t in /scan /odom /ultron/heartbeat /battery/state; do
  timeout 15 ros2 topic info "$t" >/dev/null 2>&1 || { echo "FAIL: missing topic $t"; exit 1; }
  echo "  $t ok"
done

echo "== [3/5] heartbeat rate =="
hz=$(timeout 15 ros2 topic hz /ultron/heartbeat 2>/dev/null | grep 'average rate' | awk '{print $3}' || true)
echo "  heartbeat: ${hz:-0} Hz (expect ~10)"
case "${hz:-0}" in
  1[0-9].*|9.*) echo "ok" ;;
  *) echo "WARN: heartbeat rate looks off; check the Jetson container" ;;
esac

echo "== [4/5] battery =="
timeout 15 ros2 topic echo /battery/state --once 2>/dev/null | grep -q voltage && echo "ok (check value yourself)" || echo "WARN: no battery reading"

echo "== [5/5] E-stop =="
echo "  Confirm the physical E-stop is RELEASED and motors are enabled."
echo "  If a fault is latched: release button, then:"
echo "    ros2 topic pub /ultron/clear_faults std_msgs/msg/Empty \"{}\" --once"

echo
echo "Smoke test complete."
