/* ============================================================
   PDMS — Lab Orders
   Used in encounter tab (doctor) and lab technician page.
   ============================================================ */

// ── Doctor: order lab test form ────────────────────────────────

async function buildLabForm(encId, canAdd) {
  const w = document.getElementById("lab-form-wrap");
  if (!canAdd || !_encIsOpen) { w.innerHTML = ""; return; }

  const templates = await api("/lab/templates?active_only=true") || [];

  w.innerHTML = `
    <div class="card">
      <div class="card-title" style="margin-bottom:12px">Order Lab Test</div>
      <div class="form-grid">
        <div class="field" style="grid-column:1/-1">
          <label>Select Template</label>
          <select id="lab-template">
            <option value="">— Select a test template —</option>
            ${templates.map(t =>
              `<option value="${t.template_id}"
                       data-name="${t.test_name}"
                       data-code="${t.test_code}"
                       data-cat="${t.test_category}">${t.test_name} (${t.test_code})</option>`
            ).join("")}
          </select>
        </div>
        <div class="field"><label>Test Name *</label><input type="text" id="lab-name" placeholder="Auto-filled or enter manually"></div>
        <div class="field"><label>Test Code</label><input type="text" id="lab-code" placeholder="e.g. CBC"></div>
        <div class="field"><label>Category</label><input type="text" id="lab-cat" placeholder="e.g. hematology"></div>
        <div class="field"><label>Priority</label>
          <select id="lab-pri">
            <option value="routine">Routine</option>
            <option value="urgent">Urgent</option>
            <option value="stat">STAT</option>
          </select>
        </div>
      </div>
      <div style="display:flex;justify-content:flex-end;margin-top:8px">
        <button class="btn btn-primary btn-sm" onclick="saveLabOrder('${encId}')">Order Test</button>
      </div>
    </div>`;

  document.getElementById("lab-template").addEventListener("change", function () {
    const opt = this.options[this.selectedIndex];
    if (opt.value) {
      document.getElementById("lab-name").value = opt.dataset.name;
      document.getElementById("lab-code").value = opt.dataset.code;
      document.getElementById("lab-cat").value  = opt.dataset.cat;
    }
  });
}

async function saveLabOrder(encId) {
  const templateSel = document.getElementById("lab-template");
  const body = {
    test_name:     document.getElementById("lab-name").value,
    test_code:     document.getElementById("lab-code").value,
    test_category: document.getElementById("lab-cat").value,
    priority:      document.getElementById("lab-pri").value
  };
  if (templateSel?.value) body.template_id = templateSel.value;
  if (!body.test_name) { toast("Test name required", "error"); return; }
  const r = await api(`/encounters/${encId}/lab-orders`, { method: "POST", body: JSON.stringify(body) });
  if (r && !r._conflict) { toast("Lab order placed", "success"); loadLabOrders(encId); }
}

// ── Shared: load lab orders ────────────────────────────────────

async function loadLabOrders(encIdOrPage) {
  const isEncPage =
    _currentPage === "encounter" ||
    (typeof encIdOrPage === "string" && encIdOrPage.length > 10);

  if (isEncPage && _currentEncounterId) {
    const data = await api(`/encounters/${_currentEncounterId}/lab-orders`);
    const el   = document.getElementById("lab-orders-list");
    if (!el) return;
    if (!data?.length) { el.innerHTML = `<div class="empty">No lab orders</div>`; return; }
    el.innerHTML = `<div class="table-wrap"><table><thead><tr>
      <th>Test</th><th>Code</th><th>Priority</th><th>Status</th><th>Ordered</th><th>Results</th>
    </tr></thead><tbody>${data.map(o => `
      <tr>
        <td>${o.test_name}</td>
        <td>${o.test_code || "—"}</td>
        <td><span class="badge ${o.priority === "stat" ? "badge-red" : o.priority === "urgent" ? "badge-orange" : "badge-gray"}">${o.priority}</span></td>
        <td><span class="badge ${o.status === "completed" ? "badge-green" : o.status === "in-progress" ? "badge-blue" : "badge-gray"}">${o.status}</span></td>
        <td style="font-size:11px">${formatDate(o.ordered_at)}</td>
        <td>${o.status === "completed"
          ? `<button class="link-btn" onclick="viewLabResults('${o.order_id}')">View Results</button>`
          : "Pending"}</td>
      </tr>`).join("")}</tbody></table></div>`;
    return;
  }

  // Lab technician page
  const status = document.getElementById("lab-status-filter")?.value || "ordered";
  const data   = await api(`/lab-orders?order_status=${status}&limit=100`);
  const tbody  = document.getElementById("lab-tbody");
  if (!tbody) return;
  if (!data?.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty">No lab orders</div></td></tr>`;
    return;
  }
  tbody.innerHTML = data.map(o => `<tr>
    <td>${o.test_name}</td>
    <td>${o.test_category || "—"}</td>
    <td><span class="badge ${o.priority === "stat" ? "badge-red" : o.priority === "urgent" ? "badge-orange" : "badge-gray"}">${o.priority}</span></td>
    <td style="font-size:11px">${o.patient_id?.slice(0, 8) || "—"}</td>
    <td style="font-size:11px">${formatDate(o.ordered_at)}</td>
    <td><span class="badge ${o.status === "completed" ? "badge-green" : o.status === "in-progress" ? "badge-blue" : "badge-gray"}">${o.status}</span></td>
    <td><div class="row-actions">
      ${o.status === "ordered"      ? `<button class="link-btn" onclick="startLabOrder('${o.order_id}')">Start</button>` : ""}
      ${o.status === "in-progress"  ? `<button class="link-btn" onclick="openSubmitResults('${o.order_id}')">Submit Results</button>` : ""}
      ${o.status === "completed"    ? `<button class="link-btn" onclick="viewLabResults('${o.order_id}')">View</button>` : ""}
    </div></td>
  </tr>`).join("");
}

async function startLabOrder(orderId) {
  const r = await api(`/lab-orders/${orderId}/status`, {
    method: "PATCH", body: JSON.stringify({ status: "in-progress" })
  });
  if (r) { toast("Order marked in-progress", "success"); loadLabOrders(); }
}

// ── Submit results modal ───────────────────────────────────────

async function openSubmitResults(orderId) {
  _currentLabOrderId = orderId;
  const order = await api(`/lab-orders/${orderId}`);
  const form  = document.getElementById("lab-result-form");

  if (order?.template_id) {
    // Template-driven: pre-fill parameter rows
    const tmpl   = await api(`/lab/templates/${order.template_id}`);
    const params = tmpl?.parameters || [];
    form.innerHTML = `
      <p style="color:var(--text3);margin-bottom:12px;font-size:13px">
        Test: <strong>${order.test_name}</strong> &nbsp;·&nbsp;
        Template: <strong>${tmpl?.test_name || ""}</strong>
      </p>
      <div id="lab-params"></div>`;
    const c = document.getElementById("lab-params");
    params
      .sort((a, b) => a.display_order - b.display_order)
      .forEach(p => {
        const normalRange = (p.normal_range_min != null && p.normal_range_max != null)
          ? `${p.normal_range_min} - ${p.normal_range_max}`
          : (p.normal_range_text || "");
        const row = document.createElement("div");
        row.className = "form-grid";
        row.style.marginBottom = "10px";
        row.dataset.paramId = p.parameter_id;
        row.innerHTML = `
          <div class="field"><label>${p.parameter_name}${p.is_required ? " *" : ""}</label>
            <input type="text" class="lp-name" value="${p.parameter_name}"
                   readonly style="background:var(--surface2);color:var(--text3)"></div>
          <div class="field"><label>Value</label><input type="text" class="lp-val" placeholder="Enter result"></div>
          <div class="field"><label>Unit</label><input type="text" class="lp-unit" value="${p.unit || ""}"></div>
          <div class="field"><label>Normal Range</label><input type="text" class="lp-range" value="${normalRange}"></div>`;
        c.appendChild(row);
      });
  } else {
    // Manual entry
    form.innerHTML = `
      <p style="color:var(--text3);margin-bottom:12px;font-size:13px">
        Test: <strong>${order?.test_name || orderId}</strong>
      </p>
      <div id="lab-params"></div>
      <button class="btn btn-secondary btn-sm" style="margin-top:8px" onclick="addLabParam()">+ Add Parameter</button>`;
    document.getElementById("lab-params").innerHTML = "";
    addLabParam();
  }
  openModal("modal-lab-result");
}

function addLabParam() {
  const c = document.getElementById("lab-params");
  const row = document.createElement("div");
  row.className = "form-grid";
  row.style.marginBottom = "10px";
  row.innerHTML = `
    <div class="field"><label>Parameter</label><input type="text" class="lp-name" placeholder="e.g. Haemoglobin"></div>
    <div class="field"><label>Value</label><input type="text" class="lp-val" placeholder="e.g. 14.5"></div>
    <div class="field"><label>Unit</label><input type="text" class="lp-unit" placeholder="e.g. g/dL"></div>
    <div class="field"><label>Normal Range</label><input type="text" class="lp-range" placeholder="e.g. 12.0 - 17.5"></div>`;
  c.appendChild(row);
}

// Submit results button
document.getElementById("btn-submit-lab-result").addEventListener("click", async () => {
  const rows    = document.querySelectorAll("#lab-params > div");
  const results = Array.from(rows).map(r => {
    const entry = {
      parameter_name: r.querySelector(".lp-name").value,
      result_value:   r.querySelector(".lp-val").value,
      unit:           r.querySelector(".lp-unit").value,
      normal_range:   r.querySelector(".lp-range").value
    };
    if (r.dataset.paramId) entry.parameter_id = r.dataset.paramId;
    return entry;
  }).filter(r => r.parameter_name && r.result_value);

  if (!results.length) { toast("Add at least one result", "error"); return; }

  const r = await api(`/lab-orders/${_currentLabOrderId}/results`, {
    method: "POST", body: JSON.stringify({ results })
  });
  if (r) {
    await api(`/lab-orders/${_currentLabOrderId}/status`, {
      method: "PATCH", body: JSON.stringify({ status: "completed" })
    });
    toast("Results submitted", "success");
    closeModal("modal-lab-result");
    loadLabOrders();
  }
});

// ── View results modal ─────────────────────────────────────────

async function viewLabResults(orderId) {
  const [order, data] = await Promise.all([
    api(`/lab-orders/${orderId}`),
    api(`/lab-orders/${orderId}/results`)
  ]);
  document.getElementById("view-results-title").textContent = `Results — ${order?.test_name || "Lab Order"}`;
  const body = document.getElementById("view-results-body");
  if (!data?.length) {
    body.innerHTML = `<div class="empty">No results recorded yet</div>`;
  } else {
    body.innerHTML = `<div class="table-wrap"><table>
      <thead><tr>
        <th>Parameter</th><th>Result</th><th>Unit</th><th>Normal Range</th><th>Status</th>
      </tr></thead>
      <tbody>${data.map(r => `
        <tr style="${r.is_abnormal ? "background:var(--danger-dim)" : ""}">
          <td><strong>${r.parameter_name}</strong></td>
          <td style="${r.is_abnormal ? "color:var(--danger);font-weight:600" : ""}">${r.result_value}</td>
          <td>${r.unit || "—"}</td>
          <td>${r.normal_range || "—"}</td>
          <td>${r.is_abnormal
            ? `<span class="badge badge-red">⚠ ${r.abnormal_level || "Abnormal"}</span>`
            : `<span class="badge badge-green">Normal</span>`}</td>
        </tr>`).join("")}
      </tbody>
    </table></div>`;
  }
  openModal("modal-view-results");
}
