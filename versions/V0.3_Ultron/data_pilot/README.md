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
├── feature_extract.py   # bag -> anonymous motion features (laptop, offline)
├── requirements.txt
└── index.md             # mission log table
```

## Extract features from a mission bag

```bash
pip install -r requirements.txt
python3 feature_extract.py <bag_dir_or_mcap> --mission MISSION_001 \
    --out-dir ./missions/MISSION_001
```

Produces `mission_summary.json` (duration, distance, peak speed, dwell/occupancy
grid stats, hot zones) and `features.csv` (10 s bins of traveled distance).
No raw depth/video is ever extracted.

## Rules

- Never commit rosbag/mcap or raw depth/video to git.
- Every mission folder has a `README.md` with metadata per the data
  dictionary ([`docs/30_data_and_privacy/data_dictionary.md`](../../../docs/30_data_and_privacy/data_dictionary.md)).
- Encryption and retention per
  [`docs/30_data_and_privacy/privacy_policy.md`](../../../docs/30_data_and_privacy/privacy_policy.md).
