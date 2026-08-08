# Docs (UAP_ULTRON)

Cross-version documentation for the mother project.

```
docs/
├── 00_project/           overview · roadmap · naming_and_versioning · glossary
├── 10_architecture/      system · ros · sensor_fusion · data_flow · safety · ai · diagrams
├── 20_engineering_process/  audit · risk_register · decisions (ADR) · quality_gates · changelog
├── 30_data_and_privacy/  data_collection_spec · privacy_policy · data_dictionary
├── 40_business/          market_analysis
└── 90_reference/         BOM_shared · datasheets · CAD
```

**Reading order for a newcomer:** `00_project/overview.md` → `00_project/roadmap.md`
→ `10_architecture/system_architecture.md` → `versions/` for a specific build.

**Rule:** shared knowledge lives here; build-specific facts live under
`versions/V0.3_Ultron/`. If a fact is in both, the implementation Bible wins
for V0.3.
