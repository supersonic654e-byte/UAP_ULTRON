# V0.3 — Tests

Procedures, offline unit tests, hardware harnesses, and recorded results.

## Layout

```
tests/
├── procedures/        # runnable summaries of Bible §13 procedures
├── scripts/           # automated checks
│   ├── protocol_test.py      # CRC-8 + frame layout cross-check (offline)
│   ├── test_safety_node.py   # zone/fusion math unit tests (offline)
│   ├── test_depth_scan.py    # depth->scan projection unit tests (offline)
│   ├── run_tests.sh          # runs all offline tests
│   ├── motor_test.py         # bench: drive + speed clamp
│   ├── estop_test.py         # bench: latch/release/clear (B7)
│   ├── overcurrent_test.py   # bench: locked-wheel trip (B8)
│   ├── runtime_test.py       # bench: battery voltage-vs-time CSV
│   └── bag_checksum.py       # SHA-256 of a mission bag
└── results/            # CSV/JSON of every run (date, conditions, N)
```

## Run the offline tests (no hardware, no ROS)

```bash
cd scripts && ./run_tests.sh
# or: pytest -q protocol_test.py test_safety_node.py test_depth_scan.py
```

## Hardware bench tests

Robot lifted. See `procedures/README.md` for the full steps and commands.

## Recording convention

Every result file: `date`, `operator`, `firmware/software hash`,
`battery_voltage`, `N`, mean ± std, units, deviation notes.

> No benchmark is real until its CSV is in `results/`. That is the rule.
