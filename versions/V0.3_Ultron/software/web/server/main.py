# -*- coding: utf-8 -*-
"""Ultron V0.3 — Web Control System (live server of the robot).

FastAPI application that:
  - serves the admin dashboard + user control panel (static SPA)
  - authenticates the 4-digit user PIN (role 'user') and the 10-char admin
    password (roles 'admin' read-only / 'admin_control' override)
  - streams live robot state, depth camera feed and map over WebSocket
  - accepts robot commands (teleop / "go to room" / stop / clear faults)
    with server-side safety gating (V0.3 clamps, live-only)

Run on the laptop (the V0.3 "cloud"), host networking, same CycloneDDS
domain as the robot. Start:  python -m server.main
"""

import argparse
import asyncio
import hmac
import os

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from server import auth
from server.robot_state import RobotState
from server.store import Store
from server.ros_bridge import RosBridge

HERE = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(os.path.dirname(HERE), "static")
DEFAULT_DB = os.path.join(os.path.dirname(os.path.dirname(HERE)), "data",
                          "ultron_web.db")

app = FastAPI(title="Ultron V0.3 Command Centre", version="0.3.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# ---- runtime state (initialized in main()) --------------------------------
store: Store = None
state: RobotState = None
bridge: RosBridge = None
token: auth.Token = None
limiter = auth.LoginRateLimiter()
bearer = HTTPBearer(auto_error=False)

# ---- request models ---------------------------------------------------------
class PinLogin(BaseModel):
    pin: str = Field(..., min_length=4, max_length=4)


class PasswordLogin(BaseModel):
    password: str = Field(..., min_length=10, max_length=64)


class TwistCmd(BaseModel):
    vx: float = 0.0
    wz: float = 0.0


class GoalCmd(BaseModel):
    room_id: str | None = None
    x: float | None = None
    y: float | None = None
    theta: float = 0.0


class ChangePin(BaseModel):
    pin: str = Field(..., min_length=4, max_length=4)


class RoomsUpdate(BaseModel):
    rooms: dict


# ---- auth helpers -----------------------------------------------------------
def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


def _require_role(*roles):
    def dep(creds: HTTPAuthorizationCredentials = Depends(bearer)):
        if creds is None:
            raise HTTPException(401, "missing token")
        payload = token.verify(creds.credentials)
        if payload is None:
            raise HTTPException(401, "invalid/expired token")
        if payload["role"] not in roles:
            raise HTTPException(403, "insufficient role")
        return payload
    return dep


def _issue(role: str, ip: str):
    store.log_activity(role, "login", ip)
    return {"token": token.issue(role, ip), "role": role}


# ---- pages ------------------------------------------------------------------
@app.get("/", response_class=HTMLResponse)
def index():
    return "Ultron V0.3 Command Centre — /user (control panel), /admin (dashboard)"


@app.get("/user", response_class=HTMLResponse)
def user_page():
    with open(os.path.join(STATIC_DIR, "user.html"), encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/admin", response_class=HTMLResponse)
def admin_page():
    with open(os.path.join(STATIC_DIR, "admin.html"), encoding="utf-8") as f:
        return HTMLResponse(f.read())


# ---- auth -------------------------------------------------------------------
@app.post("/api/login/user")
def login_user(body: PinLogin, request: Request):
    ip = _client_ip(request)
    if not limiter.allow(ip):
        raise HTTPException(429, "too many attempts — try again later")
    if not auth.pin_ok(body.pin):
        limiter.hit(ip)
        raise HTTPException(400, "PIN must be 4 digits")
    expected = store.get("user_pin")
    if expected is None or not hmac.compare_digest(body.pin, expected):
        limiter.hit(ip)
        store.log_activity("login", "failed_user_pin", ip)
        raise HTTPException(401, "wrong PIN")
    return _issue("user", ip)


@app.post("/api/login/admin")
def login_admin(body: PasswordLogin, request: Request):
    return _login_admin(body, request, role="admin")


@app.post("/api/login/admin_control")
def login_admin_control(body: PasswordLogin, request: Request):
    return _login_admin(body, request, role="admin_control")


def _login_admin(body, request, role):
    ip = _client_ip(request)
    if not limiter.allow(ip):
        raise HTTPException(429, "too many attempts — try again later")
    salt = bytes.fromhex(store.get("admin_salt"))
    expected = store.get("admin_hash")
    if not auth.verify_secret(body.password, salt, expected):
        limiter.hit(ip)
        store.log_activity("login", f"failed_{role}", ip)
        raise HTTPException(401, "wrong admin password")
    store.notify("info", f"{role} override session started")
    return _issue(role, ip)


@app.get("/api/me")
def me(creds: dict = Depends(_require_role("user", "admin", "admin_control"))):
    return {"role": creds["role"], "identity": creds["identity"]}


# ---- status -----------------------------------------------------------------
@app.get("/api/status")
def status(creds: dict = Depends(_require_role("user", "admin_control"))):
    return state.snapshot()


@app.get("/api/rooms")
def rooms(creds: dict = Depends(_require_role("user", "admin_control"))):
    return {"rooms": store.get_rooms()}


@app.get("/api/admin/dashboard")
def admin_dashboard(creds: dict = Depends(_require_role("admin"))):
    """Aggregate data-collection dashboard (no live camera/sensor — those are
    admin_control only). Mirrors the demo dashboard data + V0.3 pilot data."""
    return {
        "robot": {
            "connected": state.connected,
            "battery_v": state.battery["voltage"],
            "faults": state.faults,
            "mode": state.mode,
            "heartbeat_seq": state.heartbeat_seq,
        },
        "missions": store.missions(),
        "notifications": store.all_notifications(),
        "activity": store.recent_activity(),
        "rooms": store.get_rooms(),
    }


# ---- admin settings ----------------------------------------------------------
@app.get("/api/admin/pin")
def get_pin(creds: dict = Depends(_require_role("admin"))):
    return {"pin": store.get("user_pin")}


@app.post("/api/admin/pin")
def change_pin(body: ChangePin, creds: dict = Depends(_require_role("admin"))):
    if not auth.pin_ok(body.pin):
        raise HTTPException(400, "PIN must be 4 digits")
    store.set("user_pin", body.pin)
    store.log_activity("admin", "change_pin", "user PIN updated")
    store.notify("info", "User control PIN was updated")
    return {"ok": True}


@app.post("/api/admin/rooms")
def update_rooms(body: RoomsUpdate,
                 creds: dict = Depends(_require_role("admin"))):
    store.set_rooms(body.rooms)
    store.log_activity("admin", "update_rooms", f"{len(body.rooms)} rooms")
    return {"ok": True, "rooms": store.get_rooms()}


@app.get("/api/admin/activity")
def activity(creds: dict = Depends(_require_role("admin"))):
    return {"activity": store.recent_activity()}


@app.get("/api/admin/notifications")
def notifications(creds: dict = Depends(_require_role("admin", "user"))):
    return {"notifications": store.all_notifications()}


@app.post("/api/admin/notifications/seen")
def notifications_seen(creds: dict = Depends(_require_role("admin", "user"))):
    store.mark_notifications_seen()
    return {"ok": True}


# ---- commands (user / admin_control) ----------------------------------------
@app.post("/api/cmd/twist")
def cmd_twist(body: TwistCmd,
              creds: dict = Depends(_require_role("user", "admin_control"))):
    ok, reason, vx, wz = state.gate_twist(body.vx, body.wz, creds["role"])
    if not ok:
        raise HTTPException(409, reason)
    sent = bridge.publish_twist(vx, wz)
    state.record_cmd(vx, wz)
    store.log_activity(creds["role"], "cmd_twist", f"vx={vx} wz={wz}")
    return {"ok": True, "sent": sent, "vx": vx, "wz": wz}


@app.post("/api/cmd/stop")
def cmd_stop(creds: dict = Depends(_require_role("user", "admin_control"))):
    bridge.stop_robot()
    state.record_cmd(0.0, 0.0)
    state.set_mode("stopped")
    store.log_activity(creds["role"], "cmd_stop", "emergency stop")
    store.notify("warning", "Robot stop requested")
    return {"ok": True}


@app.post("/api/cmd/goal")
def cmd_goal(body: GoalCmd,
             creds: dict = Depends(_require_role("user", "admin_control"))):
    rooms = store.get_rooms()
    if body.room_id:
        if body.room_id not in rooms:
            raise HTTPException(404, "unknown room")
        r = rooms[body.room_id]
        x, y, theta = r["x"], r["y"], r["theta"]
        label = r.get("label", body.room_id)
    elif body.x is not None and body.y is not None:
        x, y, theta = body.x, body.y, body.theta
        label = f"goal({x},{y})"
    else:
        raise HTTPException(400, "provide room_id or x/y")
    if not state.is_live():
        raise HTTPException(409, "robot_not_live")
    result = bridge.send_goal(x, y, theta)
    state.set_mode("navigating")
    store.log_activity(creds["role"], "cmd_goal",
                       f"{label} -> {result.get('via', '?')}")
    store.notify("info", f"Navigation goal: {label}")
    return {"ok": result["ok"], "via": result.get("via"),
            "target": label, "reason": result.get("reason")}


@app.post("/api/cmd/clear_faults")
def cmd_clear_faults(creds: dict = Depends(_require_role("user",
                                                         "admin_control"))):
    bridge.clear_faults()
    store.log_activity(creds["role"], "clear_faults", "sent to Arduino")
    store.notify("info", "Clear-faults sent (E-stop must be released)")
    return {"ok": True}


@app.post("/api/cmd/mode")
def cmd_mode(body: dict,
             creds: dict = Depends(_require_role("user", "admin_control"))):
    mode = body.get("mode", "idle")
    state.set_mode(str(mode))
    store.log_activity(creds["role"], "set_mode", mode)
    return {"ok": True, "mode": mode}


# ---- WebSockets -------------------------------------------------------------
async def _ws_auth(ws: WebSocket):
    qp = ws.query_params
    t = qp.get("token", "")
    payload = token.verify(t)
    if payload is None:
        await ws.close(code=4401)
        return None
    return payload


@app.websocket("/ws/status")
async def ws_status(ws: WebSocket):
    await ws.accept()
    creds = await _ws_auth(ws)
    if creds is None:
        return
    try:
        while True:
            await ws.send_json(state.snapshot())
            await _sleep(0.2)
    except WebSocketDisconnect:
        pass


@app.websocket("/ws/camera")
async def ws_camera(ws: WebSocket):
    await ws.accept()
    creds = await _ws_auth(ws)
    if creds is None:
        return
    if creds["role"] not in ("user", "admin_control"):
        await ws.close(code=4403)
        return
    try:
        while True:
            png = bridge.depth_png()
            if png:
                await ws.send_bytes(png)
            else:
                await ws.send_json({"offline": True})
            await _sleep(0.25)
    except WebSocketDisconnect:
        pass


@app.websocket("/ws/map")
async def ws_map(ws: WebSocket):
    await ws.accept()
    creds = await _ws_auth(ws)
    if creds is None:
        return
    if creds["role"] not in ("user", "admin_control"):
        await ws.close(code=4403)
        return
    try:
        while True:
            png = bridge.map_png()
            if png:
                await ws.send_bytes(png)
            else:
                await ws.send_json({"offline": True})
            await _sleep(0.5)
    except WebSocketDisconnect:
        pass


@app.websocket("/ws/alerts")
async def ws_alerts(ws: WebSocket):
    await ws.accept()
    creds = await _ws_auth(ws)
    if creds is None:
        return
    try:
        last = set()
        while True:
            rows = store.unread_notifications()
            for r in rows:
                if r["id"] not in last:
                    await ws.send_json(r)
                    last.add(r["id"])
            await _sleep(1.0)
    except WebSocketDisconnect:
        pass


async def _sleep(sec):
    await asyncio.sleep(sec)


def main():
    global store, state, bridge, token
    ap = argparse.ArgumentParser(description="Ultron V0.3 web control system")
    ap.add_argument("--host", default="0.0.0.0")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--db", default=DEFAULT_DB)
    ap.add_argument("--no-ros", action="store_true",
                    help="run without the ROS bridge (demo/offline mode)")
    args = ap.parse_args()

    store = Store(args.db)
    state = RobotState()
    bridge = RosBridge(state)
    token = auth.Token(bytes.fromhex(store.get("token_secret")))

    if args.no_ros:
        print("[web] --no-ros: running in offline/demo mode (no commands)")
    else:
        bridge.start()

    if store.first_run_secrets:
        sec = store.first_run_secrets
        print("\n" + "=" * 60)
        print(" FIRST RUN — default access secrets (change them now):")
        print(f"   USER CONTROL PIN   : {sec.get('user_pin', '?')}")
        print(f"   ADMIN PASSWORD     : {sec.get('admin_password', '?')}")
        print("   (admin password is stored only as a hash)")
        print("=" * 60 + "\n")

    import uvicorn
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
