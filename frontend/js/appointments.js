/* ============================================================
   PDMS — Appointments  (schedule + list view)
   ============================================================ */

let _schedDate   = new Date();          // currently displayed date
let _schedView   = "schedule";          // "schedule" | "list"
let _schedData   = [];                  // cached appointments for current date

// ── helpers ──────────────────────────────────────────────────────

function _dateStr(d) {
  // "YYYY-MM-DD"
  return d.toISOString().split("T")[0];
}

function _fmtSchedDate(d) {
  const today = new Date();
  const isToday = _dateStr(d) === _dateStr(today);
  return d.toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", year: "numeric" })
    + (isToday ? "  —  Today" : "");
}

function _fmtTime(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}

const _schedColors = {
  scheduled:  { card: "#f0f9ff", border: "#bae6fd", time: "#0369a1", dot: "#0ea5e9" },
  confirmed:  { card: "#f0fdf4", border: "#bbf7d0", time: "#15803d", dot: "#22c55e" },
  checked_in: { card: "#fffbeb", border: "#fde68a", time: "#b45309", dot: "#f59e0b" },
  completed:  { card: "#f8fafc", border: "#e2e8f0", time: "#64748b", dot: "#94a3b8" },
  cancelled:  { card: "#fff1f2", border: "#fecdd3", time: "#be123c", dot: "#f43f5e" },
};

function _schedCardHTML(a, role) {
  const c       = _schedColors[a.status] || _schedColors.scheduled;
  const patient = a.patient_name || "Unknown Patient";
  const doctor  = a.doctor_name  ? "Dr. " + a.doctor_name : "";
  const initials = patient.split(" ").map(w => w[0]).slice(0,2).join("").toUpperCase();

  const actions = [];
  if (role === "receptionist" && a.status === "scheduled")
    actions.push(`<button class="sched-action-btn sched-btn-checkin" onclick="checkIn('${a.appointment_id}')">✓ Check In</button>`);
  if (role === "receptionist" && a.status !== "cancelled" && a.status !== "completed")
    actions.push(`<button class="sched-action-btn sched-btn-cancel" onclick="cancelAppt('${a.appointment_id}')">✕ Cancel</button>`);
  if (role === "doctor" && a.status === "checked_in")
    actions.push(`<button class="sched-action-btn sched-btn-start" onclick="openModalEncounter('${a.patient_id}','${a.appointment_id}')">▶ Start Encounter</button>`);

  const statusLabel = a.status.replace("_", " ").replace(/\b\w/g, l => l.toUpperCase());

  return `
  <div class="sched-card ${a.status === 'cancelled' ? 'sched-card-cancelled' : ''}"
       style="--sc-bg:${c.card};--sc-border:${c.border};--sc-time:${c.time}">
    <div class="sched-time-col">
      <div class="sched-time">${_fmtTime(a.scheduled_at)}</div>
      <div class="sched-dot" style="background:${c.dot}"></div>
      <div class="sched-line"></div>
    </div>
    <div class="sched-body">
      <div class="sched-card-inner">
        <div class="sched-patient-av">${initials}</div>
        <div class="sched-card-main">
          <div class="sched-patient-name" onclick="openPatientProfile('${a.patient_id}')">${patient}</div>
          ${doctor ? `<div class="sched-doctor">${doctor}</div>` : ""}
          ${a.reason ? `<div class="sched-reason">${a.reason}</div>` : ""}
        </div>
        <div class="sched-card-right">
          <span class="sched-status-pill" style="background:${c.card};border-color:${c.border};color:${c.time}">${statusLabel}</span>
          <div class="sched-card-actions">${actions.join("")}</div>
        </div>
      </div>
    </div>
  </div>`;
}

// ── main load ─────────────────────────────────────────────────────

async function loadAppointments() {
  const role         = _currentUser?.role || "";
  const doctorFilter = role === "doctor" ? `doctor_id=${_currentUser.user_id}&` : "";
  const statusFilter = document.getElementById("appt-filter-status")?.value || "";
  const dateStr      = _dateStr(_schedDate);

  // Update date label
  document.getElementById("sched-date-label").textContent = _fmtSchedDate(_schedDate);

  if (_schedView === "schedule") {
    const data = await api(
      `/appointments?${doctorFilter}date=${dateStr}&${statusFilter ? "appt_status=" + statusFilter + "&" : ""}limit=100`
    );
    _schedData = (data || []).sort((a, b) => new Date(a.scheduled_at) - new Date(b.scheduled_at));
    _renderSchedule(role);
  } else {
    const data = await api(
      `/appointments?${doctorFilter}${statusFilter ? "appt_status=" + statusFilter + "&" : ""}limit=200`
    );
    _renderList(data || [], role);
  }
}

function _renderSchedule(role) {
  const container = document.getElementById("sched-cards");
  const summary   = document.getElementById("sched-summary");

  if (!_schedData.length) {
    summary.innerHTML = "";
    container.innerHTML = `<div class="sched-empty"><div style="font-size:40px;margin-bottom:12px">📅</div><div>No appointments scheduled for this day</div></div>`;
    return;
  }

  // Summary chips
  const counts = {};
  _schedData.forEach(a => { counts[a.status] = (counts[a.status] || 0) + 1; });
  const c = _schedColors;
  summary.innerHTML = `<div class="sched-summary-chips">
    <span class="sched-chip" style="color:var(--text3)">Total: <strong>${_schedData.length}</strong></span>
    ${Object.entries(counts).map(([s, n]) => {
      const col = c[s] || c.scheduled;
      return `<span class="sched-chip" style="background:${col.card};border-color:${col.border};color:${col.time}">${s.replace("_"," ")}: <strong>${n}</strong></span>`;
    }).join("")}
  </div>`;

  // Cards + "now" line for today
  const todayStr = _dateStr(new Date());
  const isToday  = _dateStr(_schedDate) === todayStr;
  const nowMs    = Date.now();
  let   nowInserted = false;

  let html = "";
  _schedData.forEach(a => {
    if (isToday && !nowInserted && new Date(a.scheduled_at).getTime() > nowMs) {
      html += `<div class="sched-now-line"><span class="sched-now-label">Now</span><div class="sched-now-bar"></div></div>`;
      nowInserted = true;
    }
    html += _schedCardHTML(a, role);
  });
  container.innerHTML = html;
}

function _renderList(data, role) {
  const tbody = document.getElementById("appt-tbody");
  if (!data.length) {
    tbody.innerHTML = `<tr><td colspan="6"><div class="empty">No appointments found</div></td></tr>`;
    return;
  }
  tbody.innerHTML = data.map(a => `<tr>
    <td>${formatDateTime(a.scheduled_at)}</td>
    <td><a href="#" onclick="openPatientProfile('${a.patient_id}');return false" style="font-weight:500">${a.patient_name || a.patient_id?.slice(0,8)+'…'}</a></td>
    <td style="color:var(--text2)">${a.doctor_name ? 'Dr. ' + a.doctor_name : a.doctor_id?.slice(0,8)+'…'}</td>
    <td>${a.reason || "—"}</td>
    <td>${statusBadge(a.status)}</td>
    <td><div class="row-actions">
      ${role === "receptionist" && a.status === "scheduled"
        ? `<button class="link-btn" onclick="checkIn('${a.appointment_id}')">Check In</button>` : ""}
      ${role === "receptionist" && a.status !== "cancelled" && a.status !== "completed"
        ? `<button class="link-btn danger" onclick="cancelAppt('${a.appointment_id}')">Cancel</button>` : ""}
      ${role === "doctor" && a.status === "checked_in"
        ? `<button class="link-btn" onclick="openModalEncounter('${a.patient_id}','${a.appointment_id}')">▶ Start Encounter</button>` : ""}
    </div></td>
  </tr>`).join("");
}

// ── actions ───────────────────────────────────────────────────────

async function checkIn(apptId) {
  const r = await api(`/appointments/${apptId}/check-in`, { method: "POST" });
  if (r) { toast("Patient checked in", "success"); loadAppointments(); }
}

async function cancelAppt(apptId) {
  if (!confirm("Cancel this appointment?")) return;
  await api(`/appointments/${apptId}`, { method: "DELETE" });
  toast("Appointment cancelled", "success");
  loadAppointments();
}

// ── nav / toggle wiring (runs after DOM ready) ────────────────────

document.addEventListener("DOMContentLoaded", () => {

  document.getElementById("sched-prev").addEventListener("click", () => {
    _schedDate.setDate(_schedDate.getDate() - 1);
    loadAppointments();
  });
  document.getElementById("sched-next").addEventListener("click", () => {
    _schedDate.setDate(_schedDate.getDate() + 1);
    loadAppointments();
  });
  document.getElementById("sched-today").addEventListener("click", () => {
    _schedDate = new Date();
    loadAppointments();
  });

  document.getElementById("appt-filter-status").addEventListener("change", () => loadAppointments());

  document.getElementById("btn-view-schedule").addEventListener("click", () => {
    _schedView = "schedule";
    document.getElementById("appt-schedule-view").style.display = "";
    document.getElementById("appt-list-view").style.display     = "none";
    document.getElementById("btn-view-schedule").classList.add("active");
    document.getElementById("btn-view-list").classList.remove("active");
    loadAppointments();
  });

  document.getElementById("btn-view-list").addEventListener("click", () => {
    _schedView = "list";
    document.getElementById("appt-schedule-view").style.display = "none";
    document.getElementById("appt-list-view").style.display     = "";
    document.getElementById("btn-view-list").classList.add("active");
    document.getElementById("btn-view-schedule").classList.remove("active");
    loadAppointments();
  });

});

// ── patient autocomplete ──────────────────────────────────────────

document.getElementById("appt-pt-search").addEventListener("input", e => {
  clearTimeout(_apptSearchTimer);
  _apptSearchTimer = setTimeout(async () => {
    const res = await api(`/patients?search=${encodeURIComponent(e.target.value)}&limit=10`);
    const el  = document.getElementById("appt-pt-results");
    if (!res?.length) { el.style.display = "none"; return; }
    el.style.display = "block";
    el.innerHTML = res.map(p =>
      `<div style="padding:8px 12px;cursor:pointer;font-size:13px;border-bottom:1px solid var(--border)"
            onmousedown="selectApptPatient('${p.patient_id}','${p.first_name} ${p.last_name}','${p.mrn}')">
         ${p.first_name} ${p.last_name}
         <span class="mrn" style="font-size:11px">${p.mrn}</span>
       </div>`
    ).join("");
  }, 300);
});

function selectApptPatient(id, name, mrn) {
  document.getElementById("appt-pt-id").value     = id;
  document.getElementById("appt-pt-search").value = `${name} (${mrn})`;
  document.getElementById("appt-pt-results").style.display = "none";
}

async function openApptModal() {
  const doctors = await api("/users/doctors") || [];
  const sel     = document.getElementById("appt-doctor");
  sel.innerHTML = doctors.map(d =>
    `<option value="${d.user_id}">Dr. ${d.first_name} ${d.last_name}</option>`
  ).join("");
  openModal("modal-appt");
}

function openApptForPatient(patientId) {
  selectApptPatient(patientId, "Selected Patient", "");
  openApptModal();
}
