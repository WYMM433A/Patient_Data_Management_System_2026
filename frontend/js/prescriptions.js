/* ============================================================
   PDMS — Prescriptions
   Used in encounter tab (doctor) and pharmacist page.
   ============================================================ */

// ── Encounter: prescription form ──────────────────────────────

function buildRxForm(encId, patientId, canAdd) {
  const w = document.getElementById("rx-form-wrap");
  if (!canAdd || !_encIsOpen) { w.innerHTML = ""; return; }
  w.innerHTML = `
    <div class="card">
      <div class="card-title" style="margin-bottom:12px">Add Prescription</div>
      <div class="form-grid">
        <div class="field"><label>Drug Name *</label><input type="text" id="rx-drug"></div>
        <div class="field"><label>Dosage *</label><input type="text" id="rx-dosage" placeholder="e.g. 500mg"></div>
        <div class="field"><label>Frequency *</label><input type="text" id="rx-freq" placeholder="e.g. twice daily"></div>
        <div class="field"><label>Duration *</label><input type="text" id="rx-dur" placeholder="e.g. 7 days"></div>
        <div class="field"><label>Route</label>
          <select id="rx-route">
            <option value="oral">Oral</option>
            <option value="IV">IV</option>
            <option value="topical">Topical</option>
            <option value="inhaled">Inhaled</option>
            <option value="subcutaneous">Subcutaneous</option>
          </select>
        </div>
        <div class="field"><label>Instructions</label><input type="text" id="rx-instr" placeholder="Special instructions"></div>
      </div>
      <div style="display:flex;justify-content:flex-end;margin-top:8px">
        <button class="btn btn-primary btn-sm" onclick="saveRx('${encId}','${patientId}')">Prescribe</button>
      </div>
    </div>`;
}

async function saveRx(encId, patientId) {
  const body = {
    patient_id:   patientId,
    doctor_id:    _currentUser.user_id,
    drug_name:    document.getElementById("rx-drug").value,
    dosage:       document.getElementById("rx-dosage").value,
    frequency:    document.getElementById("rx-freq").value,
    duration:     document.getElementById("rx-dur").value,
    route:        document.getElementById("rx-route").value,
    instructions: document.getElementById("rx-instr").value || undefined
  };
  if (!body.drug_name || !body.dosage) { toast("Drug name and dosage required", "error"); return; }

  const r = await api(`/encounters/${encId}/prescriptions`, { method: "POST", body: JSON.stringify(body) });
  if (!r) return;

  if (r._conflict) {
    const banner = document.getElementById("allergy-conflict");
    banner.style.display = "flex";
    // Encode body for inline onclick — replace single quotes to avoid breaking attribute string
    const safeBody = JSON.stringify(body).replace(/'/g, "\\'");
    banner.innerHTML = `
      ⚠️ <strong>Allergy Conflict:</strong> ${r.detail}<br>
      <button class="btn btn-danger btn-sm" style="margin-top:8px"
              onclick="forceRx('${encId}','${safeBody}')">Confirm Override</button>
      <button class="btn btn-secondary btn-sm" style="margin-top:8px;margin-left:8px"
              onclick="document.getElementById('allergy-conflict').style.display='none'">Cancel</button>`;
    return;
  }
  document.getElementById("allergy-conflict").style.display = "none";
  toast("Prescription added", "success");
  loadPrescriptions(encId);
}

/** Override allergy conflict and force-save the prescription. */
async function forceRx(encId, bodyStr) {
  const body = JSON.parse(bodyStr);
  body.force_override = true;
  const headers = {
    "Content-Type": "application/json",
    "Authorization": `Bearer ${_token}`
  };
  try {
    const res = await fetch(`${BASE}/encounters/${encId}/prescriptions`, {
      method: "POST", headers, body: JSON.stringify(body)
    });
    if (res.ok || res.status === 201) {
      document.getElementById("allergy-conflict").style.display = "none";
      toast("Prescription added (allergy override)", "warning");
      loadPrescriptions(encId);
    } else {
      const e = await res.json().catch(() => ({}));
      toast(e.detail || "Override failed", "error");
    }
  } catch {
    toast("Network error during override", "error");
  }
}

async function loadPrescriptions(encId) {
  const data = await api(`/encounters/${encId}/prescriptions`);
  document.getElementById("rx-tbody").innerHTML = !data?.length
    ? `<tr><td colspan="7"><div class="empty">No prescriptions</div></td></tr>`
    : data.map(r => `<tr>
        <td><strong>${r.drug_name}</strong></td>
        <td>${r.dosage}</td>
        <td>${r.frequency}</td>
        <td>${r.duration}</td>
        <td>${r.route}</td>
        <td>${r.is_active
          ? `<span class="badge badge-green">Active</span>`
          : `<span class="badge badge-gray">Discontinued</span>`}</td>
        <td style="font-size:11px;color:var(--text3)">${formatDate(r.prescribed_at)}</td>
      </tr>`).join("");
}

// ── Pharmacist page ────────────────────────────────────────────

async function loadPharmRx() {
  const search = document.getElementById("rx-search")?.value || "";
  const active = document.getElementById("rx-active-filter")?.value || "";
  const params = new URLSearchParams();
  if (search) params.set("patient_id", search);
  if (active) params.set("active_only", active);
  params.set("limit", "100");

  const data  = await api(`/prescriptions?${params}`);
  const tbody = document.getElementById("pharm-rx-tbody");
  if (!data?.length) {
    tbody.innerHTML = `<tr><td colspan="8"><div class="empty">No prescriptions</div></td></tr>`;
    return;
  }
  tbody.innerHTML = data.map(r => `<tr>
    <td><strong>${r.drug_name}</strong></td>
    <td style="font-size:11px">${r.patient_id?.slice(0, 8)}…</td>
    <td>${r.dosage}</td>
    <td>${r.frequency}</td>
    <td>${r.route}</td>
    <td>${r.is_active
      ? `<span class="badge badge-green">Active</span>`
      : `<span class="badge badge-gray">Discontinued</span>`}</td>
    <td style="font-size:11px">${formatDate(r.prescribed_at)}</td>
    <td>${r.is_active
      ? `<button class="link-btn danger" onclick="toggleRx('${r.prescription_id}',false)">Discontinue</button>`
      : `<button class="link-btn" onclick="toggleRx('${r.prescription_id}',true)">Reactivate</button>`
    }</td>
  </tr>`).join("");
}

async function toggleRx(rxId, active) {
  const r = await api(`/prescriptions/${rxId}`, {
    method: "PATCH", body: JSON.stringify({ is_active: active })
  });
  if (r) {
    toast(active ? "Prescription reactivated" : "Prescription discontinued", "success");
    loadPharmRx();
  }
}
