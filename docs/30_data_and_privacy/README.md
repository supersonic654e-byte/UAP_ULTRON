# Data Collection & Privacy

Pilot data is the point of V0.3. These docs define what we collect, how we keep
it private, and what every field means.

| Doc | Purpose |
|---|---|
| `data_collection_spec.md` | The collection + logging pipeline (Bible §17) |
| `privacy_policy.md` | Privacy-by-design rules and consent gates |
| `data_dictionary.md` | Every collected field: unit, source, retention |

## Non-negotiable

- **Data minimization**: store anonymous motion features and derived data.
- **No identifiable raw video by default.** Raw depth/video only under an
  explicit consent + approval gate, with encryption and a deletion date.
- The operator laptop is the V0.3 "cloud"; nothing leaves it without review.
