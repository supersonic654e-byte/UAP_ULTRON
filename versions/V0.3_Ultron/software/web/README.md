# Ultron V0.3 — Web Control System

The **live server of the robot**. Runs on the laptop (the V0.3 "cloud"),
reads the robot's ROS topics over CycloneDDS, and serves two web UIs:

| UI | URL | Access | Role |
|---|---|---|---|
| **Admin Command Centre** | `/admin` | 10-char admin password | Read-only data/ops dashboard by default; **admin_control** (re-enter the same password) unlocks robot operation + live camera/sensors |
| **User Control Panel** | `/user` | 4-digit PIN | Remote robot control from anywhere (live camera + obstacle detection, live map, "go to room…", teleop, notifications, activity) |

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
- Nav2 "go to room…" goals capped at 0.35 m/s (B6).
- Commands rejected while the robot heartbeat is stale (`robot_not_live`).
- `admin` role is read-only; only `admin_control` (10-char password) or
  `user` (PIN) may issue commands.
