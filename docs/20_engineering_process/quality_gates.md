# Quality Gates

A version/feature is **done** only when it passes the applicable gates. These
are deliberately cheap to run so we actually run them.

## Gate A — Every PR

- [ ] Builds clean (CI: firmware build + docs lint)
- [ ] No TODO/FIXME added without a linked issue
- [ ] Docs updated if behavior changed (link the doc in the PR)
- [ ] Author self-reviewed the diff

## Gate B — Hardware/firmware change

- [ ] Robot on bench (wheels off the ground) for any motor test
- [ ] Bible §13.1 hardware tests pass (motors, encoders, E-stop, IMU, battery, overcurrent)
- [ ] E-stop release + `/ultron/clear_faults` recovery verified

## Gate C — Software/ROS change

- [ ] `ros2 topic hz` checks pass for affected topics
- [ ] QoS table (§7.4) unchanged or intentionally changed + documented
- [ ] TF chain verified (`view_frames`)
- [ ] Heartbeat/watchdog behavior verified (kill test)

## Gate D — Field/pilot session

- [ ] Bible §16.3 pre-field checklist complete
- [ ] Battery ≥ 11.1 V, mission within 12 min
- [ ] Data collection running (rosbag + logger + mission_id)
- [ ] E-stop within reach, operator present
- [ ] Post-mission: bag + JSONL archived, feature extraction run

## Gate E — Version release (tag)

- [ ] All P0 items closed
- [ ] Risk register reviewed
- [ ] Changelog updated
- [ ] Tag pushed; release notes written

## Gate F — Journal/paper artifact

- [ ] Ethics/data-protection statement in place if any human data
- [ ] Raw experiment data committed or archived with a DOI
- [ ] Reproducibility: scripts + protocol committed
