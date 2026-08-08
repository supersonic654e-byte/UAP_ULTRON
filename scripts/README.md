# Scripts

Small, repeatable automation. One script = one job, named clearly.

| Script | Purpose |
|---|---|
| `smoke_test.sh` | Pre-session checks: topics, heartbeat, E-stop state (mitigates risk R12) |
| `deploy/scripts/flash_firmware.sh` | arduino-cli build + upload (Mega 2560) |
| `software/laptop/scripts/record_bag.sh` | start a mission rosbag (mcap) for a `mission_id` |
| `software/laptop/scripts/save_map.sh` | save the SLAM map to the maps volume |
| `software/laptop/scripts/start_teleop.sh` | keyboard teleop (remaps `/cmd_vel`) |

Run the smoke test before every session.
