# ADR-0001: DDS transport across machines

- **Date:** 2026-08-05
- **Status:** Accepted

## Context

ROS 2 needs the laptop and the Jetson to discover each other and exchange
messages. Default DDS uses multicast, which does not cross a VPN or the
internet. Earlier attempts used a Zenoh router container plus JSON5 configs;
that added a moving part, a version lock, and a Rust toolchain requirement on
arm64 that made installs painful.

We also needed the link to work in three situations: same-LAN lab, remote
(home WiFi ↔ hospital), and field with a supervised laptop.

## Decision

- Use **Tailscale** (WireGuard) as the encrypted transport, pinned at 1.68.2 to
  avoid a kernel panic on the Jetson's older kernel.
- Use **CycloneDDS** (`rmw_cyclonedds_cpp`) as the RMW, with **unicast Peers**
  in a shared `cyclonedds.xml`, `ROS_DOMAIN_ID=42`.
- Every container uses `network_mode: host` so discovery works bidirectionally.
- Remove the Zenoh router and configs entirely.

## Consequences

- Easier: no router container, no PPA/source build, one shared XML file, works
  on amd64 + arm64.
- Easier: the same setup serves lab, remote, and field (Peers = Tailscale IPs;
  LAN fallback swaps in LAN IPs).
- Harder: DDS-over-VPN is not lossless; RELIABLE QoS can stall under jitter.
  Accepted because all safety paths are local and we cap remote teleop speed.
- Pin: Tailscale 1.68.2 must be tested before upgrading (see risk R10).
