# V0.3 — Software (ROS 2)

The ROS 2 stack: Jetson onboard container + laptop Nav2/SLAM/RViz2.

## Planned layout

```
software/
├── jetson/                  # build context (on /mnt/ssd/ultron/jetson)
│   ├── Dockerfile           # ros:humble-ros-base + deps (CycloneDDS)
│   ├── docker-compose.yml   # host net, device passthrough, mem cap
│   ├── entrypoint.sh
│   ├── config/cyclonedds.xml, params.yaml
│   ├── launch/jetson_bringup.launch.py
│   └── src/ultron_onboard/  # kinect, depth_to_scan, safety, serial, data_logger
├── laptop/                  # nav2_slam + rviz2 containers + data sink
└── README.md
```

## Environment rules

- ROS 2 Humble in Docker; `RMW=rmw_cyclonedds_cpp`, `ROS_DOMAIN_ID=42`.
- Containers use `network_mode: host` (ADR-0001 / fix D2).
- All heavy I/O on `/mnt/ssd`; SD holds the OS only.

## Key params (from the Bible §6.2)

- Nav2 `max_vel_x: 0.35` (autonomous cap), inflation 0.35.
- AMCL `sensor_data_qos: 2` (best_effort) — required for `/scan`.
- EKF `publish_tf: true`, frames world=odom/odom/base_link.

## Reproducibility

`docker compose build` on the Jetson with `MAKEFLAGS=-j2`; the laptop containers
reuse the same base image. A devcontainer spec for VS Code is planned so the
env is one click away.
