/* ============================================================
   PDMS — App: modal wiring, event listeners, auto-login init
   This file runs last and assumes all other JS files are loaded.
   ============================================================ */

// ── Generic modal close handlers ────────────────────────────────

document.querySelectorAll("[data-close]").forEach(btn => {
  btn.addEventListener("click", () => closeModal(btn.dataset.close));
});
document.querySelectorAll(".modal-overlay").forEach(overlay => {
  overlay.addEventListener("click", e => {
    if (e.target === overlay) overlay.classList.remove("open");
  });
});

// ── Patient modal ────────────────────────────────────────────────

document.getElementById("btn-new-patient").addEventListener("click", () => openModal("modal-patient"));
document.getElementById("btn-save-patient").addEventListener("click", async () => {
  const body = {
    first_name:              document.getElementById("pt-fname").value,
    last_name:               document.getElementById("pt-lname").value,
    date_of_birth:           document.getElementById("pt-dob").value,
    gender:                  document.getElementById("pt-gender").value  || undefined,
    blood_type:              document.getElementById("pt-blood").value   || undefined,
    phone:                   document.getElementById("pt-phone").value   || undefined,
    email:                   document.getElementById("pt-email").value   || undefined,
    address:                 document.getElementById("pt-address").value || undefined,
    emergency_contact_name:  document.getElementById("pt-ec-name").value  || undefined,
    emergency_contact_phone: document.getElementById("pt-ec-phone").value || undefined
  };
  if (!body.first_name || !body.last_name || !body.date_of_birth) {
    toast("First name, last name and DOB required", "error"); return;
  }
  const r = await api("/patients", { method: "POST", body: JSON.stringify(body) });
  if (r && !r._conflict) { toast("Patient registered", "success"); closeModal("modal-patient"); loadPatients(); }
});

// ── Appointment modal ─────────────────────────────────────────────

document.getElementById("btn-new-appt").addEventListener("click", () => openApptModal());

document.getElementById("btn-save-appt").addEventListener("click", async () => {
  const body = {
    patient_id:   document.getElementById("appt-pt-id").value,
    doctor_id:    document.getElementById("appt-doctor").value,
    scheduled_at: document.getElementById("appt-datetime").value || undefined,
    reason:       document.getElementById("appt-reason").value   || undefined,
    notes:        document.getElementById("appt-notes").value    || undefined
  };
  if (!body.patient_id || !body.doctor_id || !body.scheduled_at) {
    toast("Patient, doctor and datetime required", "error"); return;
  }
  const r = await api("/appointments", { method: "POST", body: JSON.stringify(body) });
  if (r && !r._conflict) { toast("Appointment booked", "success"); closeModal("modal-appt"); loadAppointments(); }
});

// ── Encounter modal ───────────────────────────────────────────────

function openModalEncounter(patientId, apptId) {
  document.getElementById("enc-patient-id-hidden").value = patientId;
  document.getElementById("enc-appt-id-hidden").value    = apptId || "";
  openModal("modal-encounter");
}

document.getElementById("btn-open-encounter").addEventListener("click", async () => {
  const body = {
    patient_id:      document.getElementById("enc-patient-id-hidden").value,
    doctor_id:       _currentUser.user_id,
    encounter_type:  document.getElementById("enc-type").value,
    chief_complaint: document.getElementById("enc-complaint").value || undefined
  };
  const apptId = document.getElementById("enc-appt-id-hidden").value;
  if (apptId) body.appointment_id = apptId;
  const r = await api("/encounters", { method: "POST", body: JSON.stringify(body) });
  if (r && !r._conflict) {
    toast("Encounter opened", "success");
    closeModal("modal-encounter");
    openEncounterPage(r.encounter_id, body.patient_id);
  }
});

// ── Medical History modal ─────────────────────────────────────────

document.getElementById("btn-save-history").addEventListener("click", async () => {
  const body = {
    condition_name: document.getElementById("hist-condition").value,
    icd_code:       document.getElementById("hist-icd").value    || undefined,
    onset_date:     document.getElementById("hist-onset").value  || undefined,
    is_chronic:     document.getElementById("hist-chronic").value === "true",
    notes:          document.getElementById("hist-notes").value  || undefined
  };
  if (!body.condition_name) { toast("Condition name required", "error"); return; }
  const r = await api(`/patients/${_currentPatientId}/medical-history`, {
    method: "POST", body: JSON.stringify(body)
  });
  if (r) { toast("History added", "success"); closeModal("modal-history"); loadMedHistory(_currentPatientId); }
});

// ── Allergy modal ─────────────────────────────────────────────────

document.getElementById("btn-save-allergy").addEventListener("click", async () => {
  const body = {
    allergen:      document.getElementById("allergy-name").value,
    reaction_type: document.getElementById("allergy-reaction").value || undefined,
    severity:      document.getElementById("allergy-severity").value
  };
  if (!body.allergen) { toast("Allergen required", "error"); return; }
  const r = await api(`/patients/${_currentPatientId}/allergies`, {
    method: "POST", body: JSON.stringify(body)
  });
  if (r) { toast("Allergy added", "success"); closeModal("modal-allergy"); loadAllergies(_currentPatientId); }
});

// ── Vaccination modal ─────────────────────────────────────────────

document.getElementById("btn-save-vacc").addEventListener("click", async () => {
  const body = {
    vaccine_name:    document.getElementById("vacc-name").value,
    dose_number:     parseInt(document.getElementById("vacc-dose").value) || undefined,
    administered_at: document.getElementById("vacc-admin").value || undefined,
    next_due_date:   document.getElementById("vacc-next").value  || undefined,
    notes:           document.getElementById("vacc-notes").value || undefined
  };
  if (!body.vaccine_name)    { toast("Vaccine name required", "error"); return; }
  if (!body.administered_at) { toast("Administered date required", "error"); return; }
  const r = await api(`/patients/${_currentPatientId}/vaccinations`, {
    method: "POST", body: JSON.stringify(body)
  });
  if (r) { toast("Vaccination recorded", "success"); closeModal("modal-vacc"); loadVaccinations(_currentPatientId); }
});

// ── User modal (Create) ───────────────────────────────────────────

document.getElementById("btn-new-user").addEventListener("click", async () => {
  if (!_roles.length) {
    const roles = await api("/users/roles");
    _roles = roles || [];
    _buildRoleDropdown('user-role', _roles);
    _buildRolePills(_roles);
    _syncEditRoleDropdown(_roles);
  }
  // Clear fields
  ['user-fname','user-lname','user-username','user-email','user-password','user-password-confirm'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  document.getElementById('pw-strength-wrap').style.display = 'none';
  document.querySelectorAll('#role-pills .role-pill').forEach(p => p.classList.remove('active'));
  openModal("modal-user");
});

// Password strength live update
document.getElementById("user-password")?.addEventListener("input", function() {
  updatePwStrength(this.value);
});

// Eye toggle for create modal
document.getElementById("btn-toggle-pw")?.addEventListener("click", function() {
  const inp = document.getElementById("user-password");
  inp.type = inp.type === "password" ? "text" : "password";
});

// Eye toggle for edit modal
document.getElementById("btn-toggle-edit-pw")?.addEventListener("click", function() {
  const inp = document.getElementById("edit-password");
  inp.type = inp.type === "password" ? "text" : "password";
});

// Save new user
document.getElementById("btn-save-user").addEventListener("click", async () => {
  const pw  = document.getElementById("user-password").value;
  const cpw = document.getElementById("user-password-confirm").value;
  if (pw && pw !== cpw) { toast("Passwords do not match", "error"); return; }
  const body = {
    first_name: document.getElementById("user-fname").value,
    last_name:  document.getElementById("user-lname").value,
    username:   document.getElementById("user-username").value,
    email:      document.getElementById("user-email").value,
    password:   pw,
    role_id:    document.getElementById("user-role").value
  };
  if (!body.first_name || !body.username || !body.password || !body.email || !body.role_id) {
    toast("All fields required", "error"); return;
  }
  const r = await api("/users", { method: "POST", body: JSON.stringify(body) });
  if (r && !r._conflict) { toast("Account created", "success"); closeModal("modal-user"); loadUsers(); }
});

// Save edit user
document.getElementById("btn-save-edit-user")?.addEventListener("click", saveEditUser);

// Deactivate from edit modal
document.getElementById("btn-deactivate-staff")?.addEventListener("click", async () => {
  const uid = document.getElementById("edit-user-id").value;
  const isActive = document.getElementById("edit-is-active").checked;
  const msg = isActive ? "Deactivate this staff member?" : "Reactivate this staff member?";
  if (!confirm(msg)) return;
  await api(`/users/${uid}`, { method: "PATCH", body: JSON.stringify({ is_active: !isActive }) });
  toast(`Account ${isActive ? "deactivated" : "reactivated"}`, "success");
  closeModal("modal-edit-user");
  loadUsers();
});

// User search — filters cached list, no API call
document.getElementById("user-search")?.addEventListener("input", function() {
  _renderUserTable(this.value);
});

// ── Care Plan modal ───────────────────────────────────────────────

document.getElementById("btn-new-care-plan").addEventListener("click", () => openModal("modal-care-plan"));
document.getElementById("btn-save-care-plan").addEventListener("click", async () => {
  const body = {
    patient_id:    document.getElementById("cp-patient-id").value,
    condition:     document.getElementById("cp-condition").value,
    goals:         document.getElementById("cp-goals").value,
    interventions: document.getElementById("cp-interventions").value,
    start_date:    document.getElementById("cp-start").value,
    review_date:   document.getElementById("cp-review").value,
    notes:         document.getElementById("cp-notes").value || undefined
  };
  if (!body.patient_id || !body.condition || !body.goals) {
    toast("Required fields missing", "error"); return;
  }
  const r = await api("/care-plans", { method: "POST", body: JSON.stringify(body) });
  if (r && !r._conflict) { toast("Care plan created", "success"); closeModal("modal-care-plan"); loadCarePlans(); }
});

// ── Search & filter event listeners ──────────────────────────────

document.getElementById("btn-search-patient").addEventListener("click", () => {
  loadPatients(document.getElementById("patient-search").value);
});
document.getElementById("patient-search").addEventListener("keydown", e => {
  if (e.key === "Enter") loadPatients(e.target.value);
});
document.getElementById("btn-back-patients").addEventListener("click", () => {
  document.getElementById("btn-ai-summary").style.display = "none";
  showPage("patients"); loadPatients();
});
document.getElementById("btn-back-enc").addEventListener("click", () => {
  if (_currentPatientId) openPatientProfile(_currentPatientId);
  else { showPage("patients"); loadPatients(); }
});
document.getElementById("btn-audit-filter")?.addEventListener("click", loadAudit);
document.getElementById("btn-audit-reset")?.addEventListener("click",  resetAuditFilters);
document.getElementById("btn-audit-export")?.addEventListener("click", exportAuditCSV);
document.getElementById("btn-filter-labs").addEventListener("click",   loadLabOrders);
document.getElementById("btn-rx-search").addEventListener("click",    loadPharmRx);
document.getElementById("btn-logout").addEventListener("click",       logout);

// ── Login form ────────────────────────────────────────────────────

document.getElementById("login-btn").addEventListener("click", async () => {
  const u   = document.getElementById("login-username").value.trim();
  const p   = document.getElementById("login-password").value;
  const err = document.getElementById("login-error");
  if (!u || !p) { err.textContent = "Enter username and password"; err.style.display = "flex"; return; }
  const btn = document.getElementById("login-btn");
  btn.disabled = true; btn.textContent = "Signing in…";
  try {
    await login(u, p);
    err.style.display = "none";
    showApp();
  } catch (e) {
    err.textContent = e.message;
    err.style.display = "flex";
  } finally {
    btn.disabled = false; btn.textContent = "Sign in";
  }
});

document.getElementById("login-password").addEventListener("keydown", e => {
  if (e.key === "Enter") document.getElementById("login-btn").click();
});

// ── Auto-login if tokens exist ────────────────────────────────────

if (_token && _currentUser) {
  showApp();
} else {
  showLogin();
}
