/* Ultron V0.3 Command Centre — shared client helpers. */
"use strict";

const API = {
  token: () => localStorage.getItem("ultron_token") || "",
  role: () => localStorage.getItem("ultron_role") || "",
  set(role, token) {
    localStorage.setItem("ultron_role", role);
    localStorage.setItem("ultron_token", token);
  },
  clear() {
    localStorage.removeItem("ultron_role");
    localStorage.removeItem("ultron_token");
  },
  headers(extra) {
    return Object.assign(
      { "Content-Type": "application/json",
        "Authorization": "Bearer " + API.token() },
      extra || {});
  },
  async req(method, path, body) {
    const opt = { method, headers: API.headers() };
    if (body !== undefined) opt.body = JSON.stringify(body);
    const res = await fetch(path, opt);
    let data = null;
    try { data = await res.json(); } catch (_) { /* empty body */ }
    if (res.status === 401) { API.onUnauthorized(); }
    if (!res.ok) {
      const detail = (data && data.detail) || ("HTTP " + res.status);
      throw new Error(detail);
    }
    return data;
  },
  get(path) { return API.req("GET", path); },
  post(path, body) { return API.req("POST", path, body === undefined ? {} : body); },
  onUnauthorized() { /* overridden per page */ },
  wsURL(path) {
    const proto = location.protocol === "https:" ? "wss:" : "ws:";
    return proto + "//" + location.host + path + "?token=" + encodeURIComponent(API.token());
  }
};

function toast(text, kind) {
  let wrap = document.querySelector(".toast-wrap");
  if (!wrap) { wrap = document.createElement("div"); wrap.className = "toast-wrap"; document.body.appendChild(wrap); }
  const t = document.createElement("div");
  t.className = "toast" + (kind ? " " + kind : "");
  t.textContent = text;
  wrap.appendChild(t);
  setTimeout(() => t.remove(), 3200);
}

/* Demo-mode hook: `?demo=1` auto-login, only available when the server runs
   with --sim (never in production). */
function demoParam() {
  try { return new URLSearchParams(location.search).get("demo") || ""; } catch (_) { return ""; }
}
async function demoSession(role) {
  const res = await fetch("/api/demo/session?role=" + encodeURIComponent(role));
  if (!res.ok) throw new Error("demo session unavailable");
  const d = await res.json();
  API.set(d.role, d.token);
  return d.role;
}

function $(sel, root) { return (root || document).querySelector(sel); }
function $$(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

function esc(s) {
  return String(s).replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  })[c]);
}

function fmtVoltage(v) { return (typeof v === "number") ? v.toFixed(2) + " V" : "—"; }
function fmtNum(v, d) { return (typeof v === "number") ? v.toFixed(d === undefined ? 2 : d) : "—"; }
function fmtTime(ts) {
  if (!ts) return "—";
  const d = new Date(ts * 1000);
  return d.toISOString().slice(0, 19).replace("T", " ");
}

/* ---- shared live-streaming widget (status websocket) ---------------------- */
function startStatusWS(render, intervalMs) {
  const ws = new WebSocket(API.wsURL("/ws/status"));
  ws.onmessage = (ev) => { try { render(JSON.parse(ev.data)); } catch (_) {} };
  ws.onclose = () => setTimeout(() => { try { startStatusWS(render, intervalMs); } catch (_) {} }, 2000);
  return ws;
}

function startImageWS(path, img, onOffline, intervalMs) {
  const ws = new WebSocket(API.wsURL(path));
  ws.binaryType = "arraybuffer";
  ws.onmessage = (ev) => {
    if (ev.data instanceof ArrayBuffer) {
      const url = URL.createObjectURL(new Blob([ev.data], { type: "image/png" }));
      img.src = url;
      img.onload = () => URL.revokeObjectURL(url);
      if (onOffline) onOffline(false);
    } else if (onOffline) {
      onOffline(true);
    }
  };
  ws.onclose = () => setTimeout(() => { try { startImageWS(path, img, onOffline); } catch (_) {} }, 3000);
  return ws;
}

function startAlertsWS(render) {
  const ws = new WebSocket(API.wsURL("/ws/alerts"));
  ws.onmessage = (ev) => { try { render(JSON.parse(ev.data)); } catch (_) {} };
  ws.onclose = () => setTimeout(() => { try { startAlertsWS(render); } catch (_) {} }, 2000);
  return ws;
}

/* ---- fault bits → text ---------------------------------------------------- */
const FAULT_NAMES = ["ESTOP", "OVERCURRENT", "WATCHDOG", "IMU",
                     "ENCODER", "BATTERY", "HEARTBEAT", "RESERVED"];

function faultNames(flags) {
  if (!flags) return [];
  const out = [];
  for (let i = 0; i < 8; i++) if (flags & (1 << i)) out.push(FAULT_NAMES[i]);
  return out;
}

function obstaclePill(status) {
  if (!status || status.state === undefined) return '<span class="pill neutral">no data</span>';
  if (status.state === "stop") return '<span class="pill danger"><span class="dot"></span>STOP</span>';
  if (status.state === "slow") return '<span class="pill warn"><span class="dot"></span>SLOW</span>';
  return '<span class="pill ok"><span class="dot"></span>CLEAR</span>';
}

/* Render a generic stat-card grid from a robot snapshot. */
function renderStatCards(snap, root) {
  const grid = $(root);
  if (!grid) return;
  const faults = faultNames(snap.faults && snap.faults.flags);
  const batt = snap.battery && snap.battery.voltage;
  const batteryPill = batt <= 0 ? '<span class="pill neutral">no battery</span>'
    : (batt <= 10.5 ? '<span class="pill danger">' + batt.toFixed(2) + ' V</span>'
       : (batt <= 11.1 ? '<span class="pill warn">' + batt.toFixed(2) + ' V</span>'
          : '<span class="pill ok">' + batt.toFixed(2) + ' V</span>'));
  grid.innerHTML =
    '<div class="card"><div class="stat"><span class="label">Connection</span>' +
    '<span class="value">' + (snap.connected ? "ONLINE" : "OFFLINE") + '</span>' +
    '<span class="sub">' + (snap.ros_ready ? "ROS bridge up" : "ROS bridge down") + '</span></div></div>' +
    '<div class="card"><div class="stat"><span class="label">Battery</span>' +
    '<span class="value">' + batteryPill + '</span>' +
    '<span class="sub">critical 10.5 V / warning 11.1 V</span></div></div>' +
    '<div class="card"><div class="stat"><span class="label">Mode</span>' +
    '<span class="value" style="text-transform:capitalize">' + esc(snap.mode || "idle") + '</span>' +
    '<span class="sub">heartbeat seq ' + (snap.heartbeat_seq || 0) + '</span></div></div>' +
    '<div class="card"><div class="stat"><span class="label">Faults</span>' +
    '<span class="value" style="font-size:16px">' +
    (faults.length ? faults.map(esc).join(" · ") : '<span class="pill ok">none</span>') +
    '</span><span class="sub">' + (faults.length ? "latched — resolve & clear" : "all clear") + '</span></div></div>';
}
