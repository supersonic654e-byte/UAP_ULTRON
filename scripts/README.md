# Scripts

Small, repeatable automation. One script = one job, named clearly.

| Script | Purpose |
|---|---|
| `smoke_test.sh` | Pre-session checks: topics, heartbeat, E-stop state (mitigates risk R12) |
| (planned) `flash_firmware.sh` | arduino-cli build + upload |
| (planned) `record_mission.sh` | start/stop rosbag + logger for a mission_id |

Run the smoke test before every session.
