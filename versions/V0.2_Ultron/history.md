# Ultron_V0.2 (formerly Robot_ODA_v2.0) — Experimental / Research Prototype

 (formerly Robot_ODA_v2.0, 2025)

**Role:** Experimental / research prototype.

- Second physical build; still a **laboratory platform**.
- Focus: **testing different hardware/software approaches**, isolating *why* systems fail, and learning how to engineer an effective, enhanced, AI-integrated autonomous robot.
- Used to evaluate trade-offs that V0.3 formalizes: motor-driver control schemes, interrupt/encoder wiring, real-time ↔ Linux compute split, containerization, cross-machine ROS 2 communication, power budgeting.

**Known outcomes (role, not capability):**
- Delivered the engineering basis for the v4.x implementation-Bible defect history (pin-change interrupts, H-bridge control, watchdog design, serial protocol, storage layout).
- Confirmed the two-layer compute split (edge + remote compute) as the right prototype architecture for the available hardware.
- Confirmed what V0.3 must NOT repeat: open-loop drive without validation, overly complex abandoned-payload scope, and architecture choices that could not scale.

---

---

_See also: [Ultron_V0.1 history](../V0.1_Ultron/history.md)._
