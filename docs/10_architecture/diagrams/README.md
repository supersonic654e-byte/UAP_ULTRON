# Architecture Diagrams

Rendered from the Mermaid sources in this folder. We keep the `.mmd` sources so
diagrams stay version-controlled and diffable — the old JPEGs we used to hand-edit
are gone for good.

| File | What it shows |
|---|---|
| `two-layer-overview.mmd` | The two-layer (edge + remote compute) split plus the Arduino real-time layer. |
| `full-system-architecture.mmd` | Full node/layer breakdown and data paths. |
| `ros2-node-communication.mmd` | Topic-level communication, QoS, and TF ownership. |

## How to regenerate

```bash
# mermaid-cli
mmdc -i two-layer-overview.mmd -o two-layer-overview.png --scale 2
mmdc -i full-system-architecture.mmd -o full-system-architecture.png --scale 2
mmdc -i ros2-node-communication.mmd -o ros2-node-communication.png --scale 2
```

Or paste each file into https://mermaid.live and export PNG/SVG. Use a 2x scale
for crisp prints in reports and the journal paper figures.

## Editing workflow

1. Edit the `.mmd` source.
2. Re-render locally.
3. Commit **both** the source and the rendered PNG.
4. Keep the figure numbering in sync with the paper/manual when we export them.

_Last rendered: 2026-08-08 (v5.0 / Ultron_V0.3 edition)._
