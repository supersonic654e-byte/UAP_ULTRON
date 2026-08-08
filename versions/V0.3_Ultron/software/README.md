# V0.3 — Software (ROS 2)

Two-layer ROS 2 stack: Jetson onboard container + laptop Nav2/SLAM/RViz2.
All configs are the same files the Bible documents; the code is byte-for-byte
compatible with the firmware protocol.

## Layout (implemented)

```
software/
├── jetson/                  # build context (on /mnt/ssd/ultron/jetson)
│   ├── Dockerfile           # ros:humble-ros-base + deps (CycloneDDS)
│   ├── docker-compose.yml   # host net, device passthrough, mem cap, healthcheck
│   ├── entrypoint.sh
│   ├── config/
│   │   ├── cyclonedds.xml   # SHARED — identical to laptop
│   │   └── params.yaml      # safety/kinect/depth/serial/rplidar params
│   ├── launch/jetson_bringup.launch.py
│   └── src/ultron_onboard/  # ament_python package
│       ├── ultron_protocol.py    # pure protocol (crc8, frames) — no ROS
│       ├── safety_logic.py       # pure zone/fusion math — no ROS
│       ├── depth_scan_logic.py   # pure depth->scan projection — no ROS
│       ├── serial_node.py        # ROS <-> Arduino bridge (B4/B7)
│       ├── safety_node.py        # STOP/SLOW zones + heartbeat (10 Hz)
│       ├── kinect_driver_node.py # freenect, ROI 320x120, 8 FPS
│       ├── depth_to_scan_node.py # middle row -> /kinect/scan
│       └── data_logger_node.py   # Section 17 JSONL pilot logger
└── laptop/
    ├── docker-compose.yml        # nav2_slam + rviz2 services
    ├── container/                # EKF + SLAM + Nav2 + AMCL configs/launches
    │   ├── Dockerfile, entrypoint.sh
    │   ├── config/cyclonedds.xml (SHARED), nav2_params.yaml (B6),
    │   │         ekf_params.yaml (B4), slam_params.yaml
    │   └── launch/laptop_bringup.launch.py       (SLAM mode)
    │       launch/laptop_localization.launch.py  (saved-map + AMCL mode)
    ├── rviz2/                    # Dockerfile, entrypoint, config/ultron.rviz
    └── scripts/record_bag.sh, save_map.sh, start_teleop.sh
└── web/                      # Ultron_V0.3 web control system (laptop container)
    ├── server/               # FastAPI + auth + SQLite + ROS bridge + detection
    ├── static/               # admin dashboard (/admin) + user panel (/user)
    ├── tests/                # 45 offline tests
    └── Dockerfile, entrypoint.sh, requirements.txt
```

## Environment rules

- ROS 2 Humble; `RMW=rmw_cyclonedds_cpp`, `ROS_DOMAIN_ID=42`.
- Containers use `network_mode: host` (ADR-0001 / fix D2).
- All heavy I/O on `/mnt/ssd`; SD holds the OS only.

## Key params (Bible §6.2)

- Nav2 `max_vel_x: 0.35` (autonomous cap), inflation 0.35.
- AMCL `sensor_data_qos: 2` (best_effort) — required for `/scan`.
- EKF `publish_tf: true`, frames world=odom/odom/base_link.

## Reproducibility

`docker compose build` on the Jetson with `MAKEFLAGS=-j2`; the laptop
containers reuse the same base image family. The pure-logic modules
(`ultron_protocol`, `safety_logic`, `depth_scan_logic`) are unit-tested
offline in `../../tests/scripts/` with no ROS runtime required.

CI: `.github/workflows/software-test.yml` runs the offline unit tests on every
push that touches `software/**` or `tests/scripts/**`.

## End-user deployment (two-bundle install)

For a user with the physical robot: the **Jetson bundle** is this folder and
the **laptop bundle** is `../laptop/`. Install them on the two machines, flash
the firmware, edit the one shared `cyclonedds.xml` with the two Tailscale IPs,
and start in order. The **web control system** (`../web/`) runs on the laptop
as the "live server of the robot" — admin dashboard at `/admin` and user
control panel at `/user`. Full detail:
[`docs/20_engineering_process/user_deployment_guide.md`](../../../docs/20_engineering_process/user_deployment_guide.md)
and Bible Sections 18–19.
