#!/bin/bash
set -e
source /opt/ros/humble/setup.bash
exec python3 -m server.main --host 0.0.0.0 --port 8080
