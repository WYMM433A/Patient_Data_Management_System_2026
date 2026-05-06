/* ============================================================
   PDMS — Imaging
   ============================================================ */

function buildImagingForm(encId, canAdd) {
  const w = document.getElementById("img-form-wrap");
  if (!canAdd || !_encIsOpen) { w.innerHTML = ""; return; }
  w.innerHTML = `
    <div class="card">
      <div class="card-title" style="margin-bottom:12px">Add Imaging</div>
      <div class="form-grid">
        <div class="field"><label>Type</label>
          <select id="img-type">
            <option value="X-ray">X-ray</option>
            <option value="Ultrasound">Ultrasound</option>
            <option value="MRI">MRI</option>
            <option value="CT">CT</option>
            <option value="ECG">ECG</option>
          </select>
        </div>
        <div class="field"><label>Body Part</label><input type="text" id="img-part" placeholder="e.g. Chest"></div>
        <div class="field span2"><label>Findings</label><textarea id="img-findings" style="min-height:60px"></textarea></div>
        <div class="field span2"><label>Image URL</label><input type="text" id="img-url" placeholder="https://…"></div>
      </div>
      <div style="display:flex;justify-content:flex-end;margin-top:8px">
        <button class="btn btn-primary btn-sm" onclick="saveImaging('${encId}')">Add</button>
      </div>
    </div>`;
}

async function saveImaging(encId) {
  const body = {
    imaging_type: document.getElementById("img-type").value,
    body_part:    document.getElementById("img-part").value,
    findings:     document.getElementById("img-findings").value || undefined,
    image_url:    document.getElementById("img-url").value || undefined
  };
  if (!body.body_part) { toast("Body part required", "error"); return; }
  const r = await api(`/encounters/${encId}/imaging`, { method: "POST", body: JSON.stringify(body) });
  if (r) { toast("Imaging record added", "success"); loadImaging(encId); }
}

async function loadImaging(encId) {
  const data = await api(`/encounters/${encId}/imaging`);
  document.getElementById("imaging-tbody").innerHTML = !data?.length
    ? `<tr><td colspan="5"><div class="empty">No imaging records</div></td></tr>`
    : data.map(i => `<tr>
        <td><span class="badge badge-blue">${i.imaging_type}</span></td>
        <td>${i.body_part}</td>
        <td>${i.findings || "—"}</td>
        <td>${i.radiologist_notes || "—"}</td>
        <td style="font-size:11px">${formatDate(i.created_at)}</td>
      </tr>`).join("");
}
