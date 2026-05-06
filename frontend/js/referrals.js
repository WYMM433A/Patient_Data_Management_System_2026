/* ============================================================
   PDMS — Referrals
   ============================================================ */

function buildReferralForm(encId, canAdd) {
  const w = document.getElementById("ref-form-wrap");
  if (!canAdd || !_encIsOpen) { w.innerHTML = ""; return; }
  w.innerHTML = `
    <div class="card">
      <div class="card-title" style="margin-bottom:12px">Add Referral</div>
      <div class="form-grid">
        <div class="field"><label>Specialty *</label><input type="text" id="ref-spec" placeholder="e.g. Cardiology"></div>
        <div class="field"><label>Urgency</label>
          <select id="ref-urgency">
            <option value="routine">Routine</option>
            <option value="urgent">Urgent</option>
          </select>
        </div>
        <div class="field span2"><label>Reason *</label><textarea id="ref-reason" style="min-height:60px"></textarea></div>
      </div>
      <div style="display:flex;justify-content:flex-end;margin-top:8px">
        <button class="btn btn-primary btn-sm" onclick="saveReferral('${encId}')">Add Referral</button>
      </div>
    </div>`;
}

async function saveReferral(encId) {
  const body = {
    specialty: document.getElementById("ref-spec").value,
    reason:    document.getElementById("ref-reason").value,
    urgency:   document.getElementById("ref-urgency").value
  };
  if (!body.specialty || !body.reason) { toast("Specialty and reason required", "error"); return; }
  const r = await api(`/encounters/${encId}/referrals`, { method: "POST", body: JSON.stringify(body) });
  if (r) { toast("Referral created", "success"); loadReferrals(encId); }
}

async function loadReferrals(encId) {
  const data = await api(`/encounters/${encId}/referrals`);
  document.getElementById("ref-tbody").innerHTML = !data?.length
    ? `<tr><td colspan="5"><div class="empty">No referrals</div></td></tr>`
    : data.map(r => `<tr>
        <td>${r.specialty}</td>
        <td>${r.reason}</td>
        <td><span class="badge ${r.urgency === "urgent" ? "badge-orange" : "badge-gray"}">${r.urgency}</span></td>
        <td><span class="badge ${r.status === "completed" ? "badge-green" : r.status === "accepted" ? "badge-blue" : "badge-gray"}">${r.status || "pending"}</span></td>
        <td style="font-size:11px">${formatDate(r.created_at)}</td>
      </tr>`).join("");
}
