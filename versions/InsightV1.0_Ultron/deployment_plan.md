# InsightV1.0 — Deployment Plan (draft)

> Planning only. Nothing here is committed until the V0.3 pilot proves the data
> pipeline and the platform passes its quality gates.

## 1. Readiness prerequisites

- [ ] V0.3 pilot: ≥10 missions with the Section 17 pipeline (bags + features archived).
- [ ] P0/P1 corrections closed (velocity control, camera_info, IMU cal, EKF-onboard).
- [ ] Orin port: identical topics on the new compute; onboard Nav2 validated.
- [ ] Full V0.3 test suite passes on the upgraded hardware.

## 2. Ethics & data protection (before any hospital site)

- [ ] Institutional / hospital ethics approval documented.
- [ ] Privacy policy + consent model signed off (see `docs/30_data_and_privacy/`).
- [ ] Anonymization verified: no raw video stored by default; features only.
- [ ] Data retention + deletion schedule agreed with the site.

## 3. Pilot site (typical 200-bed hospital)

- Select 1 site; map one corridor + one service area with SLAM.
- Deploy as **supervised** missions first (operator + laptop), then onboard autonomy.
- Collect: environment signals, logistics timings, anonymous motion features.

## 4. Command Centre (remote monitoring)

- Consume `/diagnostics` (already stubbed on V0.3) for fleet health.
- Web dashboard: robot status, missions, alerts, maintenance, feedback.
- One-button start for staff; no training beyond that (pitch requirement).

## 5. Success metrics for the pilot

- Mission success rate, run time vs battery, navigation accuracy.
- Data quality: feature completeness, bag integrity.
- Staff time saved (measure before/after).

## 6. Beyond the pilot

- Incremental releases (insightV1.1, v1.2, …) per the roadmap; never a rebuild.
- VitalsV2.0 / MedAssistV3.0 add-on modules.
