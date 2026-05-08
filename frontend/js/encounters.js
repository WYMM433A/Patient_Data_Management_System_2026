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
    const [soap, encData] = await Promise.all([
      api(`/encounters/${encId}/soap`),
      api(`/encounters/${encId}`)
    ]);

    if (soap) {
      document.getElementById("soap-s").value = soap.subjective || "";
      document.getElementById("soap-o").value = soap.objective  || "";
      document.getElementById("soap-a").value = soap.assessment || "";
      document.getElementById("soap-p").value = soap.plan       || "";
    }

    ["soap-s","soap-o","soap-a","soap-p"].forEach(id => {
      document.getElementById(id).disabled = !_encIsOpen;
    });

    // Wire up AI Draft button
    const aiDraftBtn = document.getElementById("btn-ai-draft");
    const aiCCWrap   = document.getElementById("ai-cc-wrap");

    if (aiDraftBtn) {
      const show = (_encIsOpen && _currentUser?.role === "doctor");
      aiDraftBtn.style.display = show ? "" : "none";

      if (aiCCWrap) {
        aiCCWrap.style.display = show ? "" : "none";
        const ccInput = document.getElementById("ai-chief-complaint");
        if (ccInput && encData?.chief_complaint) {
          ccInput.value = encData.chief_complaint;
        }
      }

      // Remove old listener before adding new one to avoid duplicates
      const newBtn = aiDraftBtn.cloneNode(true);
      aiDraftBtn.parentNode.replaceChild(newBtn, aiDraftBtn);
      newBtn.style.display = show ? "" : "none";
      newBtn.onclick = () => generateSOAPDraft(_currentEncounterId, _currentPatientId);
    }

    // Wire up Save SOAP button
    const saveBtn = document.getElementById("btn-save-soap");
    if (saveBtn) {
      const newSaveBtn = saveBtn.cloneNode(true);
      saveBtn.parentNode.replaceChild(newSaveBtn, saveBtn);
      newSaveBtn.onclick = async () => {
        const body = {
          subjective: document.getElementById("soap-s").value,
          objective:  document.getElementById("soap-o").value,
          assessment: document.getElementById("soap-a").value,
          plan:       document.getElementById("soap-p").value
        };
        const r = await api(`/encounters/${encId}/soap`, {
          method: "PATCH", body: JSON.stringify(body)
        });

        if (r) toast("SOAP note saved", "success");
      };
    }

    // Wire up Close Encounter button
    const closeBtn = document.getElementById("btn-close-enc");
    if (closeBtn) {
      const newCloseBtn = closeBtn.cloneNode(true);
      closeBtn.parentNode.replaceChild(newCloseBtn, closeBtn);
      newCloseBtn.style.display = (_encIsOpen && _currentUser?.role === "doctor") ? "" : "none";
      newCloseBtn.onclick = async () => {
        if (!confirm("Close this encounter? This cannot be undone.")) return;
        const r = await api(`/encounters/${_currentEncounterId}/close`, { method: "POST" });
        if (r) {
          toast("Encounter closed", "success");
          _encIsOpen = false;
          openEncounterPage(_currentEncounterId, _currentPatientId);
        }
      };
    }
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
    <div class="card" style="margin-bottom:12px">
      <div class="card-title" style="margin-bottom:8px">✨ AI ICD Suggest</div>
      <div style="display:flex;gap:8px;align-items:center">
        <input type="text" id="ai-symptom-input" placeholder="Describe symptoms e.g. chest pain and shortness of breath"
          style="flex:1;padding:8px 12px;border:1px solid var(--border);border-radius:var(--radius-sm);font-size:13px">
        <button class="btn btn-secondary btn-sm" onclick="suggestICD('${encId}')">✨ Suggest ICD</button>
      </div>
      <div id="ai-icd-results" style="margin-top:8px;display:flex;flex-wrap:wrap;gap:6px"></div>
    </div>
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


// ── AI: ICD Suggest ─────────────────────────────────────────

async function suggestICD(encId) {
  const input = document.getElementById("ai-symptom-input");
  const resultsDiv = document.getElementById("ai-icd-results");
  const text = input?.value?.trim();

  if (!text) { toast("Please describe the symptoms first", "error"); return; }

  resultsDiv.innerHTML = `<div class="spinner" style="width:18px;height:18px"></div>`;

  try {
    const result = await api("/ai/icd-suggest", {
      method: "POST",
      body: JSON.stringify({ text })
    });

    if (!result?.codes?.length) {
      resultsDiv.innerHTML = `<span style="font-size:12px;color:var(--text3)">No suggestions found</span>`;
      return;
    }

    resultsDiv.innerHTML = result.codes.map(c => `
      <div onclick="applyICDSuggestion('${c.code}', '${c.description.replace(/'/g, "&#39;")}')"
        style="
          cursor:pointer;
          padding:6px 10px;
          border:1px solid var(--border);
          border-radius:var(--radius-sm);
          background:var(--surface);
          font-size:12px;
          display:flex;
          align-items:center;
          gap:6px;
          transition:background 0.15s;
        "
        onmouseover="this.style.background='var(--primary-light, #eff6ff)'"
        onmouseout="this.style.background='var(--surface)'"
      >
        <span class="badge badge-blue" style="font-size:11px">${c.code}</span>
        <span style="color:var(--text2)">${c.description}</span>
        ${c.confidence ? `<span style="color:var(--text3);margin-left:auto">${Math.round(c.confidence * 100)}%</span>` : ""}
      </div>
    `).join("");

    if (result.disclaimer) {
      resultsDiv.innerHTML += `
        <p style="font-size:11px;color:var(--text3);margin-top:4px;width:100%">
          ⚠️ ${result.disclaimer}
        </p>`;
    }

  } catch (e) {
    resultsDiv.innerHTML = `<span style="font-size:12px;color:var(--danger)">AI service unavailable</span>`;
    toast("AI service unavailable", "error");
  }
}

function applyICDSuggestion(code, description) {
  const icdInput  = document.getElementById("dx-icd");
  const descInput = document.getElementById("dx-desc");
  if (icdInput)  icdInput.value  = code;
  if (descInput) descInput.value = description;
  // Clear suggestions after selection
  const resultsDiv = document.getElementById("ai-icd-results");
  if (resultsDiv) resultsDiv.innerHTML = `
    <span style="font-size:12px;color:var(--text3)">
      ✓ Applied: <strong>${code}</strong> — ${description}
    </span>`;
  toast(`ICD ${code} applied`, "success");
}


// ── AI: SOAP Draft ───────────────────────────────────────────

async function generateSOAPDraft(encId, patientId) {
  const btn = document.getElementById("btn-ai-draft");
  if (btn) { btn.disabled = true; btn.textContent = "Generating…"; }

  try {
    // Gather all data in parallel
    const [enc, vitalsData, allergiesData, historyData] = await Promise.all([
      api(`/encounters/${encId}`),
      api(`/encounters/${encId}/vitals`),
      api(`/patients/${patientId}/allergies`),
      api(`/patients/${patientId}/medical-history`)
    ]);

    // Build vitals object from most recent vitals entry
    let vitals = null;
    if (vitalsData?.length) {
      const latest = vitalsData[0];
      vitals = {};
      if (latest.blood_pressure_sys)  vitals.systolic_bp        = latest.blood_pressure_sys;
      if (latest.blood_pressure_dia)  vitals.diastolic_bp       = latest.blood_pressure_dia;
      if (latest.heart_rate)          vitals.heart_rate         = latest.heart_rate;
      if (latest.temperature)         vitals.temperature        = latest.temperature;
      if (latest.oxygen_saturation)   vitals.oxygen_saturation  = latest.oxygen_saturation;
      if (latest.respiratory_rate)    vitals.respiratory_rate   = latest.respiratory_rate;
      if (latest.weight_kg)           vitals.weight             = latest.weight_kg;
      if (latest.height_cm)           vitals.height             = latest.height_cm;
    }

    // Build allergies list
    const allergies = (allergiesData || [])
      .filter(a => !a.is_removed)
      .map(a => a.allergen);

    // Build medical history list
    const medical_history = (historyData || [])
      .filter(h => !h.is_removed)
      .map(h => h.condition_name);

    const chiefComplaint = document.getElementById("ai-chief-complaint")?.value?.trim()
  || enc?.chief_complaint
  || "Not specified";

    const body = {
      chief_complaint: chiefComplaint,
      vitals,
      allergies,
      medical_history
    };


    const result = await api("/ai/soap-draft", {
      method: "POST",
      body: JSON.stringify(body)
    });

    if (!result) { toast("AI returned no response", "error"); return; }

    // Fill in the SOAP textareas
    if (result.subjective) document.getElementById("soap-s").value = result.subjective;
    if (result.objective)  document.getElementById("soap-o").value = result.objective;
    if (result.assessment) document.getElementById("soap-a").value = result.assessment;
    if (result.plan)       document.getElementById("soap-p").value = result.plan;

    toast("SOAP draft generated — please review before saving", "success");

  } catch (e) {
    toast("AI service unavailable", "error");
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = "✨ AI Draft"; }
  }
}
