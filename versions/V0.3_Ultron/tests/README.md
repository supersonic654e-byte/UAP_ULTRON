# V0.3 — Tests

Procedures + recorded results. The procedures are in the Bible §13; **this
folder is where we keep the actual run logs and numbers** so a paper or a
reviewer can reproduce them.

## Planned layout

```
tests/
├── procedures/        # copies/summaries of Bible §13 procedures
├── results/           # CSV/JSON of every run (date, conditions, N)
├── plots/             # generated figures (from results, scripted)
└── README.md
```

## Recording convention

Every result file:

- `date`, `operator`, `firmware/software hash`, `battery_voltage`.
- Number of trials `N`, mean ± std, units.
- Notes on any deviation from the procedure.

## Must-have benchmark set (for the journal paper)

- Odometry: straight 1.0 m ±0.02 m; 360° θ≈6.28 rad.
- Twist accuracy vs commanded (0.3 m/s ±10%) — after velocity control.
- E-stop latency (<5 ms) and stop distance at 0.35 m/s.
- Overcurrent trip (locked wheels) and fuse behavior.
- Runtime curve (voltage vs time) on a full pack.
- Navigation: goal-success rate, path length/time ratio over N runs.
- Mapping/localization: AMCL pose error.

> No benchmark is real until its CSV is here. That is the rule.
