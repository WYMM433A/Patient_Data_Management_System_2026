/* ============================================================
   PDMS — Encounters: detail page, SOAP, vitals, diagnoses
   ============================================================ */

async function openEncounterPage(encId, patientId) {
  _currentEncounterId = encId;
  _currentPatientId   = patientId;
  showPage("encounter");

  const [enc, patient] = await Promise.all([
    api(`/encounters/${encId}`),
    api(`/patients/${patientId}`)
  ]);
  if (!enc || !patient) return;

  _encIsOpen = enc.status === "open";

  // Patient mini-header
  document.getElementById("enc-patient-header").innerHTML = `
    <div style="display:flex;align-items:center;gap:10px">
      <div class="patient-avatar" style="width:38px;height:38px;font-size:14px">
        ${patient.first_name?.[0]}${patient.last_name?.[0]}
      </div>
      <div>
        <div style="font-weight:600">${patient.first_name} ${patient.last_name}
          <span class="mrn">${patient.mrn}</span>
        </div>
        <div style="font-size:12px;color:var(--text3)">
          ${patient.date_of_birth} · ${patient.gender || "—"} · Blood: ${patient.blood_type || "—"}
        </div>
      </div>
    </div>`;

  document.getElementById("enc-info-bar").innerHTML = `
    <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
      <span class="badge badge-blue">Visit #${enc.visit_number}</span>
      <span class="badge ${enc.status === "open" ? "badge-green" : "badge-gray"}">${enc.status}</span>
      <span class="badge badge-gray">${enc.encounter_type}</span>
      <span style="font-size:12px;color:var(--text3)">${formatDateTime(enc.encounter_date)}</span>
      ${enc.chief_complaint ? `<span style="font-size:12px;color:var(--text2)">Chief: <strong>${enc.chief_complaint}</strong></span>` : ""}
    </div>`;

  document.getElementById("enc-closed-banner").style.display = _encIsOpen ? "none" : "flex";

  const role    = _currentUser?.role || "";
  const isDr    = role === "doctor";
  const isNurse = role === "nurse";

  document.getElementById("btn-save-soap").style.display  = isDr ? "" : "none";
  document.getElementById("btn-close-enc").style.display  = (isDr && _encIsOpen) ? "" : "none";

  // Tab switching
  document.querySelectorAll("#enc-tabs .tab").forEach(t => {
    t.onclick = () => {
      document.querySelectorAll("#enc-tabs .tab").forEach(x => x.classList.remove("active"));
      t.classList.add("active");
      document.querySelectorAll(".tab-panel[id^=enc-]").forEach(p => p.classList.remove("active"));
      document.getElementById(t.dataset.tab).classList.add("active");
      loadEncTab(t.dataset.tab.replace("enc-", ""), encId, patientId);
    };
  });

  // Load initial SOAP tab and build all sub-forms
  loadEncTab("soap", encId, patientId);
  buildVitalsForm(encId, isNurse || isDr);
  buildDxForm(encId, isDr);
  buildRxForm(encId, patientId, isDr);
  await buildLabForm(encId, isDr);
  buildImagingForm(encId, isDr);
  buildReferralForm(encId, isDr);
}

async function loadEncTab(tab, encId, patientId) {
  if (tab === "soap") {
    const soap = await api(`/encounters/${encId}/soap`);
    if (soap) {
      document.getElementById("soap-s").value = soap.subjective || "";
      document.getElementById("soap-o").value = soap.objective  || "";
      document.getElementById("soap-a").value = soap.assessment || "";
      document.getElementById("soap-p").value = soap.plan       || "";
    }
    ["soap-s","soap-o","soap-a","soap-p"].forEach(id => {
      document.getElementById(id).disabled = !_encIsOpen;
    });
  }
  else if (tab === "vitals")        await loadVitals(encId);
  else if (tab === "diagnoses")     await loadDiagnoses(encId);
  else if (tab === "prescriptions") await loadPrescriptions(encId);
  else if (tab === "labs")          await loadLabOrders(encId);
  else if (tab === "imaging")       await loadImaging(encId);
  else if (tab === "referrals")     await loadReferrals(encId);
}

// SOAP save
document.getElementById("btn-save-soap").addEventListener("click", async () => {
  const body = {
    subjective: document.getElementById("soap-s").value,
    objective:  document.getElementById("soap-o").value,
    assessment: document.getElementById("soap-a").value,
    plan:       document.getElementById("soap-p").value
  };
  const r = await api(`/encounters/${_currentEncounterId}/soap`, {
    method: "PATCH", body: JSON.stringify(body)
  });
  if (r) toast("SOAP note saved", "success");
});

// Close encounter
document.getElementById("btn-close-enc").addEventListener("click", async () => {
  if (!confirm("Close this encounter? This cannot be undone.")) return;
  const r = await api(`/encounters/${_currentEncounterId}/close`, { method: "POST" });
  if (r) {
    toast("Encounter closed", "success");
    _encIsOpen = false;
    openEncounterPage(_currentEncounterId, _currentPatientId);
  }
});

// ── Vitals ──────────────────────────────────────────────────

function buildVitalsForm(encId, canAdd) {
  const w = document.getElementById("vitals-form-wrap");
  if (!canAdd || !_encIsOpen) { w.innerHTML = ""; return; }
  w.innerHTML = `
    <div class="card">
      <div class="card-title" style="margin-bottom:12px">Record Vitals</div>
      <div class="three-col">
        <div class="field"><label>BP Systolic</label><input type="number" id="v-sys"    placeholder="120"></div>
        <div class="field"><label>BP Diastolic</label><input type="number" id="v-dia"   placeholder="80"></div>
        <div class="field"><label>Heart Rate</label><input type="number"   id="v-hr"    placeholder="72"></div>
        <div class="field"><label>Temp (°C)</label><input type="number" step="0.1" id="v-temp"   placeholder="36.8"></div>
        <div class="field"><label>Weight (kg)</label><input type="number" step="0.1" id="v-weight" placeholder="70"></div>
        <div class="field"><label>Height (cm)</label><input type="number" step="0.1" id="v-height" placeholder="170"></div>
        <div class="field"><label>SpO₂ (%)</label><input type="number"  id="v-spo2"   placeholder="98"></div>
        <div class="field"><label>Resp Rate</label><input type="number"  id="v-rr"     placeholder="16"></div>
      </div>
      <div style="display:flex;justify-content:flex-end;margin-top:8px">
        <button class="btn btn-primary btn-sm" onclick="saveVitals('${encId}')">Save Vitals</button>
      </div>
    </div>`;
}

async function saveVitals(encId) {
  const get = id => { const v = document.getElementById(id)?.value; return v ? parseFloat(v) : undefined; };
  const body = {};
  const map  = {
    "v-sys":    "blood_pressure_sys",
    "v-dia":    "blood_pressure_dia",
    "v-hr":     "heart_rate",
    "v-temp":   "temperature",
    "v-weight": "weight_kg",
    "v-height": "height_cm",
    "v-spo2":   "oxygen_saturation",
    "v-rr":     "respiratory_rate"
  };
  Object.entries(map).forEach(([id, key]) => {
    const v = get(id); if (v !== undefined) body[key] = v;
  });
  const r = await api(`/encounters/${encId}/vitals`, { method: "POST", body: JSON.stringify(body) });
  if (r) { toast("Vitals recorded", "success"); loadVitals(encId); }
}

async function loadVitals(encId) {
  const data  = await api(`/encounters/${encId}/vitals`);
  const tbody = document.getElementById("vitals-tbody");
  if (!data?.length) {
    tbody.innerHTML = `<tr><td colspan="10"><div class="empty">No vitals recorded</div></td></tr>`;
    return;
  }
  tbody.innerHTML = data.map(v => `
    <tr class="${v.is_abnormal ? "abnormal" : ""}">
      <td class="${v.is_abnormal ? "vital-abnormal" : ""}">${v.blood_pressure_sys || "—"}/${v.blood_pressure_dia || "—"}</td>
      <td class="${v.is_abnormal ? "vital-abnormal" : ""}">${v.heart_rate || "—"}</td>
      <td class="${v.is_abnormal ? "vital-abnormal" : ""}">${v.temperature || "—"}</td>
      <td>${v.weight_kg || "—"}</td>
      <td>${v.height_cm || "—"}</td>
      <td>${v.bmi || "—"}</td>
      <td>${v.oxygen_saturation || "—"}</td>
      <td>${v.respiratory_rate || "—"}</td>
      <td>${v.is_abnormal
        ? `<span class="badge badge-red">Abnormal</span>`
        : `<span class="badge badge-green">Normal</span>`}</td>
      <td style="font-size:11px;color:var(--text3)">${formatDateTime(v.recorded_at)}</td>
    </tr>`).join("");
}

// ── Diagnoses ────────────────────────────────────────────────

function buildDxForm(encId, canAdd) {
  const w = document.getElementById("dx-form-wrap");
  if (!canAdd || !_encIsOpen) { w.innerHTML = ""; return; }
  w.innerHTML = `
    <div class="card">
      <div class="card-title" style="margin-bottom:12px">Add Diagnosis</div>
      <div class="form-grid">
        <div class="field"><label>ICD Code *</label><input type="text" id="dx-icd" placeholder="e.g. J06.9"></div>
        <div class="field"><label>Description *</label><input type="text" id="dx-desc" placeholder="Condition description"></div>
        <div class="field"><label>Type</label>
          <select id="dx-type"><option value="primary">Primary</option><option value="secondary">Secondary</option></select>
        </div>
        <div class="field"><label>Condition</label>
          <select id="dx-cond"><option value="confirmed">Confirmed</option><option value="suspected">Suspected</option><option value="excluded">Excluded</option><option value="recurrent">Recurrent</option></select>
        </div>
        <div class="field"><label>Timing</label>
          <select id="dx-timing"><option value="acute">Acute</option><option value="chronic">Chronic</option><option value="complication">Complication</option><option value="recurrence">Recurrence</option></select>
        </div>
        <div class="field"><label>Chronic</label>
          <select id="dx-chronic"><option value="false">No</option><option value="true">Yes</option></select>
        </div>
      </div>
      <div style="display:flex;justify-content:flex-end;margin-top:8px">
        <button class="btn btn-primary btn-sm" onclick="saveDiagnosis('${encId}')">Add Diagnosis</button>
      </div>
    </div>`;
}

async function saveDiagnosis(encId) {
  const body = {
    icd_code:       document.getElementById("dx-icd").value,
    description:    document.getElementById("dx-desc").value,
    diagnosis_type: document.getElementById("dx-type").value,
    condition:      document.getElementById("dx-cond").value,
    timing:         document.getElementById("dx-timing").value,
    is_chronic:     document.getElementById("dx-chronic").value === "true"
  };
  if (!body.icd_code || !body.description) { toast("ICD code and description required", "error"); return; }
  const r = await api(`/encounters/${encId}/diagnoses`, { method: "POST", body: JSON.stringify(body) });
  if (r && !r._conflict) { toast("Diagnosis added", "success"); loadDiagnoses(encId); }
}

async function loadDiagnoses(encId) {
  const data = await api(`/encounters/${encId}/diagnoses`);
  const isDr = _currentUser?.role === "doctor";
  document.getElementById("dx-tbody").innerHTML = !data?.length
    ? `<tr><td colspan="7"><div class="empty">No diagnoses</div></td></tr>`
    : data.map(d => `<tr>
        <td><span class="badge badge-blue">${d.icd_code}</span></td>
        <td>${d.description}</td>
        <td><span class="badge ${d.diagnosis_type === "primary" ? "badge-blue" : "badge-gray"}">${d.diagnosis_type}</span></td>
        <td>${d.condition}</td>
        <td>${d.timing}</td>
        <td>${d.is_chronic ? "Yes" : "No"}</td>
        <td>${isDr && _encIsOpen
          ? `<button class="link-btn danger" onclick="deleteDiagnosis('${encId}','${d.diagnosis_id}')">Remove</button>`
          : ""}</td>
      </tr>`).join("");
}

async function deleteDiagnosis(encId, dId) {
  if (!confirm("Remove this diagnosis?")) return;
  await api(`/encounters/${encId}/diagnoses/${dId}`, { method: "DELETE" });
  loadDiagnoses(encId);
}
