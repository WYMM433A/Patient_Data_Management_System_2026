/* ============================================================
   PDMS — Care Plans (doctor)
   ============================================================ */

async function loadCarePlans() {
  const uid  = _currentUser?.user_id;
  const data = await api(`/care-plans?doctor_id=${uid}&limit=100`);
  const tbody = document.getElementById("care-plan-tbody");
  if (!data?.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty">No care plans</div></td></tr>`;
    return;
  }
  tbody.innerHTML = data.map(p => `<tr>
    <td style="font-size:11px">${p.patient_id?.slice(0, 8)}…</td>
    <td>${p.condition}</td>
    <td><span class="badge ${p.status === "active" ? "badge-green" : p.status === "completed" ? "badge-blue" : "badge-gray"}">${p.status}</span></td>
    <td>${p.start_date}</td>
    <td>${p.review_date}</td>
    <td style="max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12px">${p.goals}</td>
    <td>${p.status === "active"
      ? `<button class="link-btn danger" onclick="completePlan('${p.plan_id}')">Complete</button>`
      : ""}</td>
  </tr>`).join("");
}

async function completePlan(planId) {
  if (!confirm("Mark this care plan as completed?")) return;
  await api(`/care-plans/${planId}`, {
    method: "PATCH", body: JSON.stringify({ status: "completed" })
  });
  toast("Care plan completed", "success");
  loadCarePlans();
}
