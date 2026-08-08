# Ultron V0.3 — Web Control System

The **live server of the robot**. Runs on the laptop (the V0.3 "cloud"),
reads the robot's ROS topics over CycloneDDS, and serves two web UIs:

| UI | URL | Access | Role |
|---|---|---|---|
| **Admin Command Centre** | `/admin` | 10-char admin password | Read-only data/ops dashboard by default; **admin_control** (re-enter the same password) unlocks robot operation + live camera/sensors |
| **User Control Panel** | `/user` | 4-digit PIN | Remote robot control from anywhere (live camera + obstacle detection, live map, waypoint navigation, teleop, notifications, activity, system status) |

## Design rules implemented (per the system requirements)

- **Admin never operates the robot in the normal case.** The admin dashboard
  only shows the demo-style data + V0.3 pilot data-collection view.
- **Robot operation + live camera/sensor access require `admin_control`**,
  granted only by re-entering the 10-character admin password. Every such
  session is logged.
- **The user controls the robot** through the user panel with the 4-digit PIN.
- **The PIN is shown and changeable only by the admin** (admin dashboard →
  Settings).
- If the laptop (web server) goes offline, robot communication via the web
  cuts off; onboard safety (Jetson safety node + Arduino watchdogs) continues
  to protect the robot (Bible §16 network-drop behavior).

## User Control Panel features (Ultron_V0.3 r4 — redesigned)

- **PIN-protected entry** — 4-digit operator PIN (admin-changeable), with
  animated orbit login screen. Session persists across browser reloads.
- **Live camera feed** — MJPEG stream from `web_video_server` (topic
  `/detection/image` by default, configurable). Colorized depth rendering
  with obstacle detection overlay (red ≤0.35 m STOP / amber ≤0.70 m SLOW /
  green clear). Continuous object detection tags from `/ultron/detection/objects`.
- **Live map** — `ros2djs` viewer subscribing to `/map` (OccupancyGrid).
  Robot pose overlay (AMCL `/amcl_pose` or EKF `/odom`). Click on map to
  place named waypoints; waypoints persist to localStorage and sync to
  `/ultron/waypoints` topic for robot-side persistence.
- **Navigation** — Named waypoint buttons (auto-loaded from waypoint_manager).
  "Go to \<waypoint\>" publishes to `/ultron/waypoints/navigate`; Nav2
  action `/navigate_to_pose` used on laptop for goal execution.
- **Manual teleop** — On-screen 5-button pad (▲/◄/■/►/▼) with speed slider
  (0.05–0.45 m/s), plus full keyboard support (WASD / arrows, space = stop).
  Server-side clamped to 0.45 m/s (teleop) and 0.35 m/s (goals).
- **E-STOP** — Prominent pulsating red button in top bar; publishes
  `/ultron/estop` (Bool) + zero `/cmd_vel` instantly.
- **System status panel** — Real-time tiles: LiDAR health (OK/TIMEOUT),
  Serial/ODOM health, Fault flags (hex + decoded names), Safe velocity
  actually sent to motors (`/safe_cmd_vel`), Left/Right motor current
  (ACS712 via `/ultron/current_left/right`).
- **Notifications strip** — Color-coded live log (success/warning/error/info)
  with timestamps, capped at 25 entries, auto-fade after 10s.
- **Settings modal** — rosbridge URL, video stream base URL, video topic,
  and operator PIN change (requires current PIN).

## Layout

```
software/web/
├── server/               # FastAPI backend
│   ├── main.py           # routes, WebSocket streams, auth, command gating
│   ├── auth.py           # PIN / 10-char admin password, HMAC tokens, rate limit
│   ├── store.py          # SQLite (settings, activity, notifications, missions)
│   ├── robot_state.py    # live state model + safety command gating
│   ├── ros_bridge.py     # optional rclpy bridge (laptop → robot topics)
│   ├── detection.py      # obstacle/object detection from scans + depth
│   └── map_render.py     # dependency-free PNG renderer (map + depth feed)
├── static/               # frontend (admin.html, user.html, style.css, app.js)
├── tests/                # 45 offline tests (auth, store, detection, render, API)
├── Dockerfile            # laptop container (host net + CycloneDDS)
├── entrypoint.sh
└── requirements.txt
```

## Run

On the laptop, after the normal bring-up:

```bash
cd ../laptop && docker compose up -d ultron_web
# then open:
#   http://<laptop>:8080/admin   (admin password)
#   http://<laptop>:8080/user    (4-digit PIN)
```

First run prints the generated PIN and admin password to the container log once.
Change the PIN from admin → Settings. Change the admin password by deleting
the row in the SQLite DB and restarting (documented reset path).

### World access

The server binds `0.0.0.0`. For access "from anywhere", expose it securely —
never plain HTTP to the open internet. Recommended: **Tailscale Funnel**,
**Cloudflare Tunnel**, or an SSH reverse tunnel, all in front of the PIN /
password auth.

## Tests (offline, no ROS)

```bash
pip install -r requirements.txt pytest httpx
python -m pytest -q software/web/tests
```

## Command safety (server-side)

- Teleop clamped to 0.45 m/s, yaw to 1.0 rad/s (matches firmware).
- Nav2 "go to waypoint…" goals capped at 0.35 m/s (B6).
- Commands rejected while the robot heartbeat is stale (`robot_not_live`).
- `admin` role is read-only; only `admin_control` (10-char password) or
  `user` (PIN) may issue commands.