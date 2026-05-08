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
  const role    = _currentUser?.role || "";
  const isDr    = role === "doctor";
  const isNurse = role === "nurse";
  const isReceptionist = role === "receptionist";

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
      ${isReceptionist
        ? `<button class="btn btn-secondary btn-sm" onclick="openApptForPatient('${patientId}')">+ Book Appointment</button>`
        : `<div style="display:flex;flex-direction:column;gap:8px">
            <span style="font-size:12px;color:var(--text3)">Start encounters from the Appointments page.</span>
            ${isDr ? `<button class="btn btn-secondary btn-sm" style="margin-top:4px" onclick="generatePatientSummary()">🤖 AI Patient Summary</button>` : ""}
           </div>`}
    </div>`;

  // Show/hide clinical tabs
  document.getElementById("tab-encounters").style.display   = ["doctor","nurse"].includes(role) ? "" : "none";
  document.getElementById("tab-history").style.display      = isReceptionist ? "none" : "";
  document.getElementById("tab-allergies").style.display    = isReceptionist ? "none" : "";
  document.getElementById("tab-vaccinations").style.display = isReceptionist ? "none" : "";

  // Role-based action buttons inside tabs
  document.getElementById("hist-actions").innerHTML    = isDr ? `<button class="btn btn-secondary btn-sm" onclick="openModal('modal-history')">+ Add</button>` : "";
  document.getElementById("allergy-actions").innerHTML = isDr ? `<button class="btn btn-secondary btn-sm" onclick="openModal('modal-allergy')">+ Add</button>` : "";
  document.getElementById("vacc-actions").innerHTML    = (isDr || isNurse) ? `<button class="btn btn-secondary btn-sm" onclick="openModal('modal-vacc')">+ Add</button>` : "";
  document.getElementById("enc-actions").innerHTML     = "";

  // Load clinical sub-tabs
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
      if (t.dataset.tab === "prof-vitals-trend") loadVitalsTrend(patientId);
    };
  });

  // Reset to first tab
  document.querySelector("#profile-tabs .tab").click();
}
// Vitals Trends
async function loadVitalsTrend(pid) {
  const data = await api(`/patients/${pid}/vitals/trends`);
  
  // 1. TABLE: Keep all columns, show newest records at the top
  const tableData = data ? [...data] : [];
  document.getElementById("vitals-trend-tbody").innerHTML = !tableData.length
    ? `<tr><td colspan="10"><div class="empty">No vitals recorded</div></td></tr>`
    : tableData.map(v => `<tr>
        <td>${formatDateTime(v.recorded_at)}</td>
        <td>${v.blood_pressure_sys || "—"}/${v.blood_pressure_dia || "—"}</td>
        <td>${v.heart_rate || "—"}</td>
        <td>${v.temperature || "—"}</td>
        <td>${v.weight_kg || "—"}</td>
        <td>${v.height_cm || "—"}</td>
        <td>${v.bmi || "—"}</td>
        <td>${v.oxygen_saturation || "—"}</td>
        <td>${v.respiratory_rate || "—"}</td>
        <td>${v.is_abnormal ? "⚠️" : ""}</td>
      </tr>`).join("");

  // 2. CHART: Sort chronologically and pass to the render function
  const chartData = [...tableData].sort((a, b) => new Date(a.recorded_at) - new Date(b.recorded_at));
  renderVitalsChart(chartData);
}

function renderVitalsChart(data) {
  if (!window.Chart) return;
  const ctx = document.getElementById('vitals-trend-chart').getContext('2d');
  if (window._vitalsChart) window._vitalsChart.destroy();

  window._vitalsChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.map(v => formatDateTime(v.recorded_at)),
      datasets: [
        { 
          label: 'BP Sys', 
          data: data.map(v => v.blood_pressure_sys), 
          borderColor: '#ef4444', 
          backgroundColor: '#ef444411',
          fill: true,
          tension: 0.3 
        },
        { 
          label: 'BP Dia', 
          data: data.map(v => v.blood_pressure_dia), 
          borderColor: '#f87171', 
          tension: 0.3 
        },
        { 
          label: 'HR', 
          data: data.map(v => v.heart_rate), 
          borderColor: '#3b82f6', 
          tension: 0.3 
        },
        { 
          label: 'Weight (kg)', 
          data: data.map(v => v.weight_kg), 
          borderColor: '#10b981', 
          borderWidth: 3,
          tension: 0.3
        },
        { 
          label: 'SpO₂', 
          data: data.map(v => v.oxygen_saturation), 
          borderColor: '#06b6d4', 
          borderDash: [5, 5],
          tension: 0.3
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: 'index', intersect: false },
      plugins: {
        legend: { position: 'top', labels: { usePointStyle: true } }
      },
      scales: {
        y: { 
          beginAtZero: false, 
          suggestedMin: 40,
          grid: { color: '#f3f4f6' }
        },
        x: { grid: { display: false } }
      }
    }
  });
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

async function generatePatientSummary() {
  const patientId = _currentPatientId;
  if (!patientId) return;

  // Show the overlay with spinner
  document.getElementById("ai-summary-overlay").style.display = "flex";
  document.getElementById("ai-summary-content").innerHTML = 
    `<div class="spinner"></div>`;

  try {
    // Fetch all patient data in parallel
    const [patient, history, allergies, vaccinations, encounters] = await Promise.all([
      api(`/patients/${patientId}`),
      api(`/patients/${patientId}/medical-history`),
      api(`/patients/${patientId}/allergies`),
      api(`/patients/${patientId}/vaccinations`),
      api(`/encounters?patient_id=${patientId}&skip=0&limit=5`)
    ]);

    // Build summary prompt text
    const age = patient.date_of_birth
      ? Math.floor((new Date() - new Date(patient.date_of_birth)) / 31557600000)
      : "Unknown";

    const historyList = (history || [])
      .filter(h => !h.is_removed)
      .map(h => h.condition_name).join(", ") || "None";

    const allergyList = (allergies || [])
      .filter(a => !a.is_removed)
      .map(a => `${a.allergen} (${a.severity})`).join(", ") || "NKDA";

    const vaccList = (vaccinations || [])
      .map(v => v.vaccine_name).join(", ") || "None recorded";

    const recentEncs = (encounters || []).slice(0, 3)
      .map(e => `${e.encounter_date?.split("T")[0]}: ${e.chief_complaint || "No complaint recorded"} (${e.status})`)
      .join("\n") || "No recent encounters";

    // Call AI
    const response = await fetch("http://localhost:8000/ai/patient-summary", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${localStorage.getItem("access_token")}`
      },
      body: JSON.stringify({
        patient_name: `${patient.first_name} ${patient.last_name}`,
        age,
        gender: patient.gender || "Unknown",
        blood_type: patient.blood_type || "Unknown",
        medical_history: historyList,
        allergies: allergyList,
        vaccinations: vaccList,
        recent_encounters: recentEncs
      })
    });

    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "AI error");

    document.getElementById("ai-summary-content").textContent = data.summary;

  } catch (e) {
    document.getElementById("ai-summary-content").innerHTML =
      `<span style="color:var(--danger)">Failed to generate summary. Please try again.</span>`;
  }
}

function closeAISummary() {
  document.getElementById("ai-summary-overlay").style.display = "none";
}
