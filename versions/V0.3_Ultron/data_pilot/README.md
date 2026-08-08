# V0.3 — Data Pilot

Pilot data collection (Bible §17). Raw bags are large — **index only, commit
small artifacts**. Large blobs go to Zenodo with a DOI referenced here.

```
data_pilot/
├── missions/            # one folder per mission_id
│   └── <mission_id>/
│       ├── README.md    # metadata: site, operator, result, retention
│       ├── checksums.txt
│       └── features.csv # anonymous motion features (small, commit)
├── notebooks/           # analysis + plots (feature_extract usage)
└── index.md             # mission log table
```

## Rules

- Never commit rosbag/mcap or raw depth/video to git.
- Every mission folder has a `README.md` with metadata per the data dictionary.
- Encryption and retention per `docs/30_data_and_privacy/privacy_policy.md`.
