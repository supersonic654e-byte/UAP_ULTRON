# Ultron_V0.3 — End-User Deployment Guide (Two-Bundle Install)

> How a single operator with the physical robot gets the full autonomous
> system running from two downloaded install bundles.
> This guide is the repo-side companion of **Bible Section 18**
> (`versions/V0.3_Ultron/implementation_bible.md` §18 and the original
> `Ultron_V0.3.txt` Section 18). The Bible is authoritative for details; this
> page is the "so what do I actually download and run" answer.

## 18.1 The model in one paragraph

Ultron_V0.3 is a **two-layer** system. All real-time hardware work (motors,
encoders, IMU, E-stop, battery, LiDAR, depth) happens on the **Jetson Nano**
edge layer. All heavy compute (SLAM, Nav2, localization, RViz2) happens on a
**laptop**. That is why the entire software system ships as **two install
bundles** — one per machine — plus one **firmware flash** on the Arduino.
Install the two bundles, connect the machines with **Tailscale**, and the
system behaves as a single robot over the network.

> Correction for clarity: the transport is **Tailscale + CycloneDDS**
> (`rmw_cyclonedds_cpp`). Zenoh was removed in Bible v4.2 (B3); nothing in
> these bundles uses Zenoh.

## 18.2 What the two bundles are

| Bundle | Runs on | Provides | Where it lives in this repo |
|---|---|---|---|
| **Jetson bundle** | Jetson Nano, Ubuntu 20.04 host, Docker | All onboard nodes: serial, safety, kinect, depth-to-scan, data-logger; static TFs; device access | `versions/V0.3_Ultron/software/jetson/` |
| **Laptop bundle** | Laptop, Ubuntu 22.04, Docker | EKF, SLAM / AMCL localization, Nav2, RViz2, teleop, bag recording | `versions/V0.3_Ultron/software/laptop/` |
| **Firmware** (not a bundle — a flash) | Arduino Mega 2560 R3 | Motor drive, encoders, IMU, E-stop, watchdogs, protocol | `versions/V0.3_Ultron/firmware/ultron_firmware/` |

Both bundles are delivered as **folders** (the Docker build contexts). For
distribution, zip them: `ultron-jetson-bundle.zip` and
`ultron-laptop-bundle.zip`. No ROS installation is required on either host —
everything runs inside Docker.

## 18.3 What is NOT in the bundles (do these first)

The bundles contain **no** hardware. Before they can work:

1. Assemble the robot per Bible §2 (BOM, wiring, power). The right encoder on
   D52/D51 (B1), IBT-2 two-PWM wiring (D1), Kinect on a direct USB port (H1).
2. Flash the Arduino firmware once (Section 11.4 / `deploy/scripts/flash_firmware.sh`).
3. Calibrate before relying on odometry/Nav2 (Bible §13 + `calibration/scripts/`).
4. A Tailscale account with **both machines on the same account**.

## 18.4 Prerequisites per machine (checked by the bundle installers)

### Jetson Nano (Ubuntu 20.04)
- [ ] SD (OS/kernel) + SSD at `/mnt/ssd` mounted **by UUID, nofail**; Docker
      data-root at `/mnt/ssd/docker` (Bible §3.4)
- [ ] Docker CE + compose plugin; `sudo usermod -aG docker`
- [ ] udev rules installed → `/dev/ultron_arduino`, `/dev/ultron_lidar`
      (`deploy/scripts/install_udev.sh`)
- [ ] Tailscale 1.68.2 **pinned** (`apt-mark hold`), service enabled
- [ ] chrony configured to sync from the laptop (`deploy/scripts/install_chrony.sh jetson <LAPTOP_TS_IP>`)
- [ ] Headless mode (optional): `systemctl set-default multi-user.target`
- [ ] Robot powered, battery ≥ 11.1 V

### Laptop (Ubuntu 22.04)
- [ ] Docker CE + compose plugin
- [ ] Tailscale installed + same account
- [ ] chrony configured as the NTP server (`deploy/scripts/install_chrony.sh laptop`)
- [ ] `xhost +local:` only if running RViz2 in a container
- [ ] Robot and laptop visible to each other: `tailscale ping <peer>` → direct

## 18.5 One shared file to customize (the only per-user change)

Both bundles ship a shared `cyclonedds.xml`. **It must be byte-identical on
both machines** and contain the two real Tailscale IPs:

```xml
<CycloneDDS>
  <Domain id="42">
    <General><AllowMulticast>false</AllowMulticast></General>
    <Discovery>
      <Peers>
        <Peer address="<JETSON_TS_IP>"/>
        <Peer address="<LAPTOP_TS_IP>"/>
      </Peers>
    </Discovery>
  </Domain>
</CycloneDDS>
```

- Get the IPs with `tailscale ip -4` on each machine.
- Offline lab (no Tailscale): put the two **LAN IPs** in instead; swap back
  before field use.

## 18.6 Build & install (one time)

### Jetson
```bash
# once: dependencies, udev, chrony, firewall (Bible §4.3)
deploy/scripts/install_udev.sh
deploy/scripts/install_chrony.sh jetson 100.x.x.x        # laptop Tailscale IP
sudo ufw allow 7400:7500/udp && sudo ufw allow 41641/udp

# build the container (first build 20–40 min on the Nano)
cd software/jetson
docker compose build --build-arg MAKEFLAGS=-j2
docker compose up -d
docker compose logs -f
```

### Laptop
```bash
sudo ufw allow 7400:7500/udp && sudo ufw allow 41641/udp
deploy/scripts/install_chrony.sh laptop
cd software/laptop
docker compose build
docker compose up -d nav2_slam
```

## 18.7 Startup order (every session)

1. **Jetson:** power on, wait for boot, then `docker compose up -d`.
   Confirm the log lines:
   - `Serial connected: /dev/ultron_arduino @ 115200`
   - `Kinect depth stream active.`
   - `Safety node active: STOP<=0.35m SLOW<=0.70m`
2. **Laptop:** `docker compose up -d nav2_slam` (EKF + SLAM/Nav2), then
   RViz2 on demand: `docker compose up rviz2`.
3. **Verify the mesh** from the laptop:
   ```bash
   ros2 topic list                       # sees Jetson topics
   ros2 topic hz /scan /odom /ultron/heartbeat
   ```
   Expected: `/scan` ~5.5 Hz, `/odom` ~30 Hz, `/ultron/heartbeat` ~10 Hz.
4. **Drive:** `teleop_twist_keyboard` (remap `/cmd_vel`), or set a 2D Nav Goal
   in RViz2 (autonomous ≤ 0.35 m/s, laptop present — B5).

## 18.8 What to do when it does NOT "just run"

Follow Bible §15 in order — 90 % of first-run failures are:

| Symptom | Cause | Fix |
|---|---|---|
| `ros2 topic list` empty on laptop | wrong `cyclonedds.xml` IPs / firewall | re-check §18.5; `sudo ufw allow 7400:7500/udp` on **both**; `tailscale ping` |
| `/scan` published but AMCL/Nav2 silent | QoS mismatch | `amcl sensor_data_qos: 2` + obstacle layer `best_effort` (already default in the bundle) |
| No `/dev/ultron_arduino` | udev / genuine vs clone | `deploy/scripts/install_udev.sh`; `lsusb \| grep 2341` |
| Fault LED solid at boot | heartbeat before container start | 5 s grace in firmware; start the Jetson container promptly |
| Motors won't move after a clean restart | latched software E-stop | release button + `ros2 topic pub /ultron/clear_faults std_msgs/msg/Empty "{}" --once` |

## 18.9 Summary — is it really "2 downloads and it runs"?

**Yes**, with the exact scope:
- 2 bundles (Jetson + laptop) + 1 firmware flash = the entire software system.
- 1 shared file to edit (Tailscale IPs) = the only per-user configuration.
- Hardware assembly + calibration are prerequisites, not part of the bundles.
- Autonomous Nav2 requires the laptop to be on the loop (B5) — which is the
  point of having two bundles.
