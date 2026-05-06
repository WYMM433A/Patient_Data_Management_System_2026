/* ============================================================
   PDMS — Auth: login/logout UI, nav build, user chip
   ============================================================ */

function showLogin() {
  document.getElementById("page-login").classList.add("active");
  document.getElementById("app").classList.remove("active");
}

function showApp() {
  document.getElementById("page-login").classList.remove("active");
  document.getElementById("app").classList.add("active");
  buildNav();
  updateUserChip();
  navigateToDefault();
}

function buildNav() {
  const role  = _currentUser?.role || _currentUser?.role_name || "";
  const items = NAV_CONFIG[role] || [];
  const nav   = document.getElementById("sidebar-nav");
  nav.innerHTML = "";

  items.forEach(item => {
    const el = document.createElement("div");
    el.className    = "nav-item";
    el.dataset.page = item.page;
    el.innerHTML    = `${ICONS[item.icon] || ""}<span>${item.label}</span>`;
    el.addEventListener("click", () => {
      showPage(item.page);
      loadPage(item.page);
    });
    nav.appendChild(el);
  });

  // Show/hide "Register Patient" and "Book Appointment" buttons
  const canRegister = ["receptionist", "doctor"].includes(role);
  const elNew  = document.getElementById("btn-new-patient");
  const elAppt = document.getElementById("btn-new-appt");
  if (elNew)  elNew.style.display  = canRegister ? "" : "none";
  if (elAppt) elAppt.style.display = canRegister ? "" : "none";
}

function updateUserChip() {
  if (!_currentUser) return;
  const u = _currentUser;
  const name     = `${u.first_name || ""} ${u.last_name || ""}`.trim() || u.username;
  const initials = (u.first_name?.[0] || "") + (u.last_name?.[0] || "") || u.username?.[0] || "?";
  document.getElementById("nav-avatar").textContent   = initials.toUpperCase();
  document.getElementById("nav-username").textContent = name;
  document.getElementById("nav-role").textContent     = (u.role || "").replace(/_/g, " ");
  // Topbar right-side user chip
  const ta = document.getElementById("topbar-actions");
  if (ta) ta.innerHTML = `<div class="topbar-user"><div class="topbar-user-av">${initials.toUpperCase()}</div><div><div class="topbar-user-name">${name}</div><div class="topbar-user-role">${(u.role||'').replace(/_/g,' ')}</div></div></div>`;
}

function navigateToDefault() {
  const role = _currentUser?.role || "";
  const defaults = {
    system_admin:   "users",
    doctor:         "dashboard",
    nurse:          "patients",
    receptionist:   "patients",
    lab_technician: "lab-orders",
    pharmacist:     "prescriptions"
  };
  const page = defaults[role] || "patients";
  showPage(page);
  loadPage(page);
}
