# Risk Register

Living table — add, close, or re-rate risks as the project evolves. Each risk
has a named owner. Ratings: Severity/Probability/Impact = High/Med/Low.

| # | Risk | Sev | Prob | Impact | Current mitigation | Required action | Owner |
|---|---|---|---|---|---|---|---|
| R1 | Open-loop wheel drive: actual speed ≠ commanded (battery sag, load) | High | High | Stop margin invalid; Nav2 tracking poor | Firmware velocity clamp; Nav2 cap 0.35 m/s | P0/P1: per-wheel velocity PID + re-validate stop margins at min battery | Team |
| R2 | Kinect 1414 obsolete; USB contention; 12 W | Med | High | Frame drops, power drain, upgrade friction | Direct-port allocation; ROI 8 FPS | P1: camera_info-driven depth→scan for D455 drop-in | Team |
| R3 | ~15–20 min runtime on 3S 2200 mAh | High | High | Missions cut short; pilot data incomplete | ≤12-min mission rule | ≥2 packs + hot-swap now; bigger pack at Insight | Team |
| R4 | RELIABLE DDS over VPN stalls under jitter | Med | Med | Frozen teleop/nav (safety holds) | Local heartbeat; unicast peers | P1: EKF onboard; remote teleop ≤0.3 m/s | Team |
| R5 | EKF on laptop → localization depends on network+clock | Med | Med | TF jumps, AMCL instability | chrony; single TF owner | P1: move EKF container to Jetson | Team |
| R6 | Thin obstacles missed (5.5 Hz + 1° LiDAR) | High | Med | Collisions in cluttered space | Kinect mid-field zone | Widen costmap footprint; consider A2M12 earlier | Team |
| R7 | Nano OOM/thermal/brownout under load | Med | Med | Container death → safe stop, disruptive | ZRAM/swap, mem cap, headless | §3.6 soak test; verify 5 V/4 A | Team |
| R8 | BTS7960 (43 A) + 15 A fuse on 44 A battery | Med | Low | Fuse blow on dual stall; wiring heat | 7 A/motor software trip | Wire-gauge spec for 12 V rail; repeated overcurrent test | Team |
| R9 | MPU6050 gyro bias → heading drift | Med | Med | Slow yaw drift | EKF yaw covariance | P1: IMU offset cal + DLPF | Team |
| R10 | Tailscale pinned at 1.68.2 | Low | Med | Security/stale features | apt-mark hold | Documented upgrade test before Insight | Team |
| R11 | Pilot privacy breach (raw video stored) | High | Med | Legal/ethical failure | privacy-by-design (Bible §17) | Consent gate; anonymize; retention policy | Team |
| R12 | DDS discovery regression (bridge networking) | Med | Low | Silent topic loss | host networking rule | Smoke-test script before sessions | Team |
| R13 | Old kernel (L4T 32.7.2) can't run AX210/BNO085 | Med | Med | Upgrade blocked until Orin | — | Sequence those upgrades with the Orin | Team |

Closed items get struck through here and recorded in the changelog.
