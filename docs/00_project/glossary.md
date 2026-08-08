# Glossary

| Term | Meaning |
|---|---|
| Edge layer | The Jetson on the robot: sensors, safety node, MCU bridge. Works without the network. |
| Remote compute layer | The laptop running Nav2/SLAM/EKF (V0.3). |
| Real-time layer | The Arduino Mega: E-stop ISR, watchdogs, PWM drive. |
| Two-layer architecture | Edge + remote compute split used by Ultron_V0.3. |
| Nav2 | ROS 2 Navigation stack (planner, controller, costmaps). |
| slam_toolbox | ROS 2 package used for SLAM mapping. |
| AMCL | Adaptive Monte Carlo Localization (used against saved maps). |
| EKF | Extended Kalman Filter (robot_localization) for odom+IMU fusion. |
| DDS | Data Distribution Service — ROS 2 middleware. CycloneDDS here. |
| Tailscale | WireGuard-based VPN used to link the laptop and robot. |
| CycloneDDS | Our RMW implementation (`rmw_cyclonedds_cpp`). |
| BTS7960 / IBT-2 | Motor driver module (two-PWM H-bridge). |
| Watchdog (WDT) | Hardware/software timer that stops the robot on a hang. |
| E-stop | Emergency stop; hardware-latched, two-step release. |
| ROS bag | Recorded ROS 2 message log (pilot data). |
| mcap | Compact indexed bag storage format. |
| JSONL | Newline-delimited JSON used by the onboard logger. |
| Motion features | Anonymous counts/flow/dwell derived from perception (no identity). |
| Privacy-by-design | Data minimization as an architecture requirement, not an afterthought. |
| Ultron_insightV1.0 | First real-world deployment generation (planned). |

Add new terms as we introduce them. Keep definitions short and concrete.
