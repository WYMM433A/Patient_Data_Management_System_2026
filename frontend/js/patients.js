/* ============================================================
   PDMS — Patients: list, profile, medical history, allergies,
          vaccinations, encounter list
   ============================================================ */

async function loadPatients(search = "") {
  const data  = await api(`/patients?search=${encodeURIComponent(search)}&limit=100`);
  const tbody = document.getElementById("patient-tbody");
  if (!data?.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty">No patients found</div></td></tr>`;
    return;
  }
  const _ptColors = ['#3b82f6','#0d9488','#8b5cf6','#f97316','#ec4899','#22c55e','#0ea5e9','#a78bfa'];
  tbody.innerHTML = data.map(p => {
    const initials = (p.first_name?.[0] || '') + (p.last_name?.[0] || '');
    const avBg     = _ptColors[((p.first_name?.charCodeAt(0)||0) + (p.last_name?.charCodeAt(0)||0)) % _ptColors.length];
    const statusCls = p.is_active === false ? 'badge-pt-inactive' : 'badge-pt-active';
    const statusTxt = p.is_active === false ? 'INACTIVE' : 'ACTIVE';
    return `<tr>
      <td><span class="mrn-link" onclick="openPatientProfile('${p.patient_id}')">${p.mrn}</span></td>
      <td>
        <div style="display:flex;align-items:center;gap:9px">
          <div class="pt-av" style="background:${avBg}">${initials.toUpperCase()}</div>
          <a href="#" onclick="openPatientProfile('${p.patient_id}');return false" style="font-weight:500">${p.first_name} ${p.last_name}</a>
        </div>
      </td>
      <td>${p.date_of_birth ? formatDate(p.date_of_birth) : '—'}</td>
      <td>${p.gender || '—'}</td>
      <td>${p.phone || '—'}</td>
      <td>${p.blood_type ? `<span class="badge-blood">${p.blood_type}</span>` : '—'}</td>
      <td><span class="${statusCls}">${statusTxt}</span></td>
      <td><button class="btn-outline" onclick="openPatientProfile('${p.patient_id}')">View Profile</button></td>
    </tr>`;
  }).join('');
}

async function openPatientProfile(patientId) {
  _currentPatientId = patientId;
  showPage("patient-profile");

  const patient = await api(`/patients/${patientId}`);
  if (!patient) return;
  const role = _currentUser?.role || "";

  // Patient header
  const initials = (patient.first_name?.[0] || "") + (patient.last_name?.[0] || "");
  document.getElementById("profile-header").innerHTML = `
    <div class="patient-avatar">${initials}</div>
    <div class="patient-info">
      <h2>${patient.first_name} ${patient.last_name} <span class="mrn">${patient.mrn}</span></h2>
      <div class="patient-meta">
        <span>DOB: <strong>${patient.date_of_birth || "—"}</strong></span>
        <span>Gender: <strong>${patient.gender || "—"}</strong></span>
        <span>Blood: <strong>${patient.blood_type || "—"}</strong></span>
        <span>Phone: <strong>${patient.phone || "—"}</strong></span>
        <span>Email: <strong>${patient.email || "—"}</strong></span>
      </div>
      ${patient.emergency_contact_name
        ? `<div class="patient-meta"><span>Emergency: <strong>${patient.emergency_contact_name} ${patient.emergency_contact_phone || ""}</strong></span></div>`
        : ""}
    </div>`;

  // Overview details
  document.getElementById("overview-details").innerHTML = `
    <div class="card">
      <div class="card-title" style="margin-bottom:12px">Demographics</div>
      <table><tbody>
        <tr><td style="color:var(--text3);width:140px">Address</td><td>${patient.address || "—"}</td></tr>
        <tr><td style="color:var(--text3)">Registered</td><td>${formatDate(patient.created_at)}</td></tr>
      </tbody></table>
    </div>
    <div class="card">
      <div class="card-title" style="margin-bottom:12px">Quick Actions</div>
      ${role === "receptionist"
        ? `<button class="btn btn-secondary btn-sm" onclick="openApptForPatient('${patientId}')">+ Book Appointment</button>`
        : "<span style='font-size:12px;color:var(--text3)'>Start encounters from the Appointments page.</span>"}
    </div>`;

  // Show/hide clinical tabs
  const isReceptionist = role === "receptionist";
  document.getElementById("tab-encounters").style.display    = ["doctor","nurse"].includes(role) ? "" : "none";
  document.getElementById("tab-history").style.display       = isReceptionist ? "none" : "";
  document.getElementById("tab-allergies").style.display     = isReceptionist ? "none" : "";
  document.getElementById("tab-vaccinations").style.display  = isReceptionist ? "none" : "";

  // Role-based action buttons inside tabs
  const isDr    = role === "doctor";
  const isNurse = role === "nurse";
  document.getElementById("hist-actions").innerHTML    = isDr    ? `<button class="btn btn-secondary btn-sm" onclick="openModal('modal-history')">+ Add</button>` : "";
  document.getElementById("allergy-actions").innerHTML = isDr    ? `<button class="btn btn-secondary btn-sm" onclick="openModal('modal-allergy')">+ Add</button>` : "";
  document.getElementById("vacc-actions").innerHTML    = (isDr || isNurse) ? `<button class="btn btn-secondary btn-sm" onclick="openModal('modal-vacc')">+ Add</button>` : "";
  document.getElementById("enc-actions").innerHTML     = ""; // Encounters started from Appointments page only

  // Load clinical sub-tabs (not for receptionist)
  if (!isReceptionist) {
    loadMedHistory(patientId);
    loadAllergies(patientId);
    loadVaccinations(patientId);
  }
  if (isDr || isNurse) loadEncounterList(patientId);

  // Tab switching
  document.querySelectorAll("#profile-tabs .tab").forEach(t => {
    t.onclick = () => {
      document.querySelectorAll("#profile-tabs .tab").forEach(x => x.classList.remove("active"));
      t.classList.add("active");
      document.querySelectorAll(".tab-panel[id^=prof-]").forEach(p => p.classList.remove("active"));
      document.getElementById(t.dataset.tab).classList.add("active");
    };
  });
  // Reset to first tab
  document.querySelector("#profile-tabs .tab").click();
}

async function loadMedHistory(pid) {
  const data  = await api(`/patients/${pid}/medical-history`);
  const isDr  = _currentUser?.role === "doctor";
  document.getElementById("history-tbody").innerHTML = !data?.length
    ? `<tr><td colspan="6"><div class="empty">No records</div></td></tr>`
    : data.map(h => `<tr>
        <td>${h.condition_name}</td>
        <td>${h.icd_code || "—"}</td>
        <td>${h.onset_date || "—"}</td>
        <td>${h.is_chronic ? "Yes" : "No"}</td>
        <td>${h.notes || "—"}</td>
        <td>${isDr ? `<button class="link-btn danger" onclick="deleteHistory('${pid}','${h.history_id}')">Remove</button>` : ""}</td>
      </tr>`).join("");
}

async function loadAllergies(pid) {
  const data = await api(`/patients/${pid}/allergies`);
  const isDr = _currentUser?.role === "doctor";
  document.getElementById("allergy-tbody").innerHTML = !data?.length
    ? `<tr><td colspan="4"><div class="empty">No allergies recorded</div></td></tr>`
    : data.map(a => `<tr>
        <td>${a.allergen}</td>
        <td>${a.reaction_type || "—"}</td>
        <td><span class="badge ${a.severity === "severe" ? "badge-red" : a.severity === "moderate" ? "badge-orange" : "badge-gray"}">${a.severity}</span></td>
        <td>${isDr ? `<button class="link-btn danger" onclick="deleteAllergy('${pid}','${a.allergy_id}')">Remove</button>` : ""}</td>
      </tr>`).join("");
}

async function loadVaccinations(pid) {
  const data = await api(`/patients/${pid}/vaccinations`);
  document.getElementById("vacc-tbody").innerHTML = !data?.length
    ? `<tr><td colspan="5"><div class="empty">No vaccinations</div></td></tr>`
    : data.map(v => `<tr>
        <td>${v.vaccine_name}</td>
        <td>${v.dose_number || "—"}</td>
        <td>${formatDate(v.administered_at)}</td>
        <td>${v.next_due_date || "—"}</td>
        <td>${v.notes || "—"}</td>
      </tr>`).join("");
}

async function loadEncounterList(pid) {
  const data = await api(`/encounters?patient_id=${pid}&limit=50`);
  document.getElementById("enc-list-tbody").innerHTML = !data?.length
    ? `<tr><td colspan="6"><div class="empty">No encounters</div></td></tr>`
    : data.map(e => `<tr class="${e.status === "closed" ? "enc-closed" : ""}">
        <td>${formatDate(e.encounter_date)}</td>
        <td>${e.encounter_type}</td>
        <td>${e.chief_complaint || "—"}</td>
        <td>${statusBadge(e.status)}</td>
        <td>#${e.visit_number}</td>
        <td><button class="link-btn" onclick="openEncounterPage('${e.encounter_id}','${pid}')">Open</button></td>
      </tr>`).join("");
}

// Delete helpers (called from inline onclick)
async function deleteHistory(pid, hid) {
  if (!confirm("Remove this history record?")) return;
  await api(`/patients/${pid}/medical-history/${hid}`, { method: "DELETE" });
  loadMedHistory(pid);
}

async function deleteAllergy(pid, aid) {
  if (!confirm("Remove this allergy?")) return;
  await api(`/patients/${pid}/allergies/${aid}`, { method: "DELETE" });
  loadAllergies(pid);
}
