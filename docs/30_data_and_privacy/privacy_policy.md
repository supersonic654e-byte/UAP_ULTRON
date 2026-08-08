# Privacy Policy (project-level, V0.3 pilot)

Privacy is an architecture requirement here, not a checkbox.

## Principles

1. **Data minimization.** Collect the least that answers the question.
2. **Anonymous by default.** Store motion *features* (counts, flow, dwell), not
   identifiable video or faces.
3. **Consent gate.** Any identifiable raw data requires documented consent +
   ethical approval before collection, and is destroyed after a defined period.
4. **Encryption at rest.** Laptop (pilot "cloud") and SSD are encrypted.
5. **No off-site transfer by default.** Nothing leaves the operator laptop
   without review.
6. **Retention limit.** Every dataset has an expiry; expired data is deleted.

## We store

- Anonymous motion features, environment signals, odometry/SLAM trajectories,
  logistics timestamps, aggregated analytics, fault/battery telemetry.

## We do NOT store (without a gate)

- Names, faces, or identifying metadata.
- Raw depth/video of identifiable people.

## Roles

- **Data owner:** the hospital/site (for real deployments).
- **Data steward:** the team operator who runs the laptop.
- **Reviewer:** a named team member who approves any exception to the default.

## Exception flow

1. State why raw data is needed (which question).
2. Get written consent/approval (documented in the mission folder).
3. Collect minimally (region-of-interest, short window).
4. Encrypt, add retention, and delete on schedule.
5. Record the exception in the changelog.

## To review

- Anyone can open an issue titled `privacy:` to audit a dataset or a procedure.
