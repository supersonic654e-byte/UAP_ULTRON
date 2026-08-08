#!/bin/bash
# Record a pilot mission bag (Bible §17.4). Run BEFORE the mission starts.
# Usage: ./record_bag.sh <mission_id>
set -euo pipefail

MISSION_ID="${1:?usage: record_bag.sh <mission_id>}"
OUT_DIR="${2:-$HOME/ultron_data/$MISSION_ID}"
TOPICS="/odom /imu/data /scan /kinect/scan /battery/state \
/ultron/fault /ultron/heartbeat /cmd_vel /safe_cmd_vel"

mkdir -p "$OUT_DIR"
echo "Recording mission $MISSION_ID -> $OUT_DIR"
echo "Topics: $TOPICS"
ros2 bag record -s mcap -o "$OUT_DIR" $TOPICS
