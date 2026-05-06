/* ============================================================
   PDMS — API Layer
   Centralised fetch wrapper with automatic token refresh.
   ============================================================ */

async function refreshToken() {
  const rt = localStorage.getItem("refresh_token");
  if (!rt) throw new Error("No refresh token");
  const res = await fetch(`${BASE}/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: rt })
  });
  if (!res.ok) throw new Error("Refresh failed");
  const d = await res.json();
  _token = d.access_token;
  localStorage.setItem("access_token", d.access_token);
  if (d.refresh_token) localStorage.setItem("refresh_token", d.refresh_token);
}

async function api(path, opts = {}, retry = true) {
  const isForm = opts.headers?.["Content-Type"] === "application/x-www-form-urlencoded";
  const headers = isForm
    ? { "Content-Type": "application/x-www-form-urlencoded", ...opts.headers }
    : { "Content-Type": "application/json", "Authorization": `Bearer ${_token}`, ...opts.headers };

  const res = await fetch(`${BASE}${path}`, { ...opts, headers });

  if (res.status === 401 && retry) {
    try {
      await refreshToken();
      return api(path, opts, false);
    } catch {
      logout();
      return null;
    }
  }
  if (res.status === 403) { toast("Access denied", "error"); return null; }
  if (res.status === 409) {
    const e = await res.json();
    return { _conflict: true, detail: e.detail };
  }
  if (!res.ok) {
    let msg = "Request failed";
    try { const e = await res.json(); msg = e.detail || msg; } catch {}
    toast(msg, "error");
    return null;
  }
  if (res.status === 204) return { ok: true };
  return res.json();
}

async function login(username, password) {
  const res = await fetch(`${BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ username, password })
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Login failed");
  _token = data.access_token;
  localStorage.setItem("access_token", data.access_token);
  localStorage.setItem("refresh_token", data.refresh_token);
  localStorage.setItem("user", JSON.stringify(data.user));
  _currentUser = data.user;
  return data;
}

function logout() {
  localStorage.clear();
  _token = "";
  _currentUser = null;
  showLogin();
}
