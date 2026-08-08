# Shared BOM (cross-version)

Parts that survive across generations. The **authoritative** V0.3 BOM with full
specs and wiring lives in the implementation Bible
(`versions/V0.3_Ultron/implementation_bible.md`, §2.1); this page lists what is
reused vs replaced.

| Component | V0.3 | InsightV1.0 | Shared? |
|---|---|---|---|
| Jetson Nano 4 GB | ✔ | → Orin Nano Super 8 GB | no |
| Arduino Mega 2560 | ✔ | → Arduino Nano + CAN | no |
| DK-37R gear motors | ✔ | ✔ (encoders → AS5048B) | chassis yes |
| IBT-2 / BTS7960 | ✔ | → (CAN + new driver) | no |
| MPU6050 | ✔ | → BNO085 | no |
| RPLiDAR A1M8 | ✔ | → A2M12 | no |
| Kinect 1414 | ✔ | → RealSense D455 | no |
| ACS712-30A | ✔ | ✔ | yes |
| 3S LiPo | ✔ | → larger pack | no (upgrade) |
| Buck 12→5V | ✔ | → re-sized | no |
| USB hub (Orico) | ✔ | (internal USB3) | maybe |
| E-stop, LEDs, resistors | ✔ | ✔ | yes |

## Long-lead / risk parts

- RealSense D455, BNO085, A2M12, AS5048B, MCP2515, AX210 — source early; they
  define the InsightV1.0 BOM.
- Verify `libfreenect` version availability at install time (arm64 apt).
