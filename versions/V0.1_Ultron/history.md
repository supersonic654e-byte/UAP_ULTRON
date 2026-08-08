# UAP_ULTRON — Ultron_V0.1 & Ultron_V0.2 (Laboratory Prototype History)

> Generation history of the UAP_ULTRON mother project.
> These two robots are **experimental / laboratory prototypes and learning/research platforms** — **not** deployment-ready robots. They exist to document *how* the project learned to build the deployable platform, not as reference hardware.

---

## Ultron_V0.1 (2024)

**Role:** Laboratory / learning prototype — the first physical build.

- Primary purpose: **experimentation, research, and practical robotics learning**.
- First-contact platform: hand-built chassis, hobby electronics, basic motor control.
- Used to acquire real-world experience with mobile-robot fundamentals: drive trains, encoders, IMUs, power, and ROS 2 on constrained hardware.
- Objective: **get the first robot moving and learn the hard lessons cheaply** — before investing in a deployable design.

**Known outcomes (role, not capability):**
- Validated the general concept (indoor wheeled platform + LIDAR + ROS 2).
- Exposed the classic beginner failure modes: power/ground loops, encoder wiring errors, H-bridge mis-wiring, PID/odometry drift, USB bandwidth contention, SD wear, thermal limits.
- These failures became the explicit fix list carried into Ultron_V0.2 and V0.3.

---

---

_See also: [Ultron_V0.2 history](../V0.2_Ultron/history.md)._
