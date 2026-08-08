# Ultron_V0.3 — Deploy Assets

One-time installers and platform files for the Jetson host. Used by the
[end-user deployment guide](../../../docs/20_engineering_process/user_deployment_guide.md)
and Bible Section 18.

## Contents

```
deploy/
├── udev/               # device symlinks: ultron_arduino, ultron_lidar, Kinect
├── systemd/            # ultron-v03.service (auto-start) + docker SSD-wait drop-in
├── chrony/             # jetson (client) and laptop (server) time-sync configs
└── scripts/
    ├── install_udev.sh      # udev + dialout/plugdev groups
    ├── install_chrony.sh    # <jetson|laptop> mode, IP arg for jetson
    ├── install_service.sh   # optional boot auto-start
    ├── build_firmware.sh    # arduino-cli compile (Mega 2560)
    ├── flash_firmware.sh    # arduino-cli upload
    └── verify_environment.sh # symlinks, tailscale, DDS env, topic rates, TF
```

## Typical first-time flow (Jetson)

```bash
./scripts/install_udev.sh
./scripts/install_chrony.sh jetson <LAPTOP_TS_IP>
./scripts/build_firmware.sh
./scripts/flash_firmware.sh /dev/ultron_arduino
sudo ufw allow 7400:7500/udp && sudo ufw allow 41641/udp
cd ../software/jetson && docker compose build --build-arg MAKEFLAGS=-j2
docker compose up -d
```

Verify afterwards: `./scripts/verify_environment.sh`.

## Typical first-time flow (Laptop)

```bash
sudo ufw allow 7400:7500/udp && sudo ufw allow 41641/udp
./scripts/install_chrony.sh laptop
cd ../software/laptop && docker compose build
docker compose up -d nav2_slam
```
