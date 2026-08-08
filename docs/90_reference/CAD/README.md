# CAD (Shared Mechanical Parts)

Shared/mechanical parts that outlive a single build. Keep both the native file
(Fusion/FreeCAD) and an exported STL.

Proposed layout:

```
CAD/
├── wheels/            # wheel + hub (V0.3, reused)
├── sensor_mounts/     # lidar, kinect (later D455) mounts
├── electronics_bay/   # Jetson/Arduino/hub trays
├── chassis/           # base board, columns
└── stl/               # exported STL for printing
```

Conventions:

- One folder per assembly. `README.md` inside with a photo + print settings.
- Version the file names (`base-board_v03.step`).
- Native CAD files are binary — use Git LFS or keep them out of git and track
  only STL + a link.
