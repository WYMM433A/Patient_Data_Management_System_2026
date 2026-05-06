/* ============================================================
   PDMS — Dashboard (doctor)
   ============================================================ */

async function loadDashboard() {
  const today = new Date().toISOString().split('T')[0];
  const uid   = _currentUser?.user_id;
  const fname = _currentUser?.first_name || _currentUser?.username || '';
  const hour  = new Date().getHours();
  const greet = hour < 12 ? 'Good morning' : hour < 17 ? 'Good afternoon' : 'Good evening';

  // Greeting
  const gEl = document.getElementById('dash-greeting');
  if (gEl) {
    gEl.innerHTML = `<h2>${greet}, ${fname}</h2><p>${new Date().toLocaleDateString('en-GB', {weekday:'long', year:'numeric', month:'long', day:'numeric'})}</p>`;
  }

  const [appts, encs] = await Promise.all([
    api(`/appointments?doctor_id=${uid}&date=${today}&limit=50`),
    api(`/encounters?doctor_id=${uid}&enc_status=open&limit=20`)
  ]);

  const total     = appts?.length || 0;
  const checkedIn = appts?.filter(a => a.status === 'checked_in').length || 0;
  const completed = appts?.filter(a => a.status === 'completed').length  || 0;
  const openEnc   = encs?.length || 0;

  // Colorful stat cards with icons
  document.getElementById('dash-stats').innerHTML = `
    <div class="stat-card sc-blue">
      <div><div class="stat-val">${total}</div><div class="stat-label">Today's Appointments</div></div>
      <div class="stat-icon si-blue"><svg viewBox="0 0 24 24" fill="currentColor" width="22" height="22"><path d="M19 3h-1V1h-2v2H8V1H6v2H5C3.9 3 3 3.9 3 5v16c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 18H5V8h14v13z"/></svg></div>
    </div>
    <div class="stat-card sc-orange">
      <div><div class="stat-val">${checkedIn}</div><div class="stat-label">Checked In</div></div>
      <div class="stat-icon si-orange"><svg viewBox="0 0 24 24" fill="currentColor" width="22" height="22"><path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8V21.6h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/></svg></div>
    </div>
    <div class="stat-card sc-teal">
      <div><div class="stat-val">${openEnc}</div><div class="stat-label">Open Encounters</div></div>
      <div class="stat-icon si-teal"><svg viewBox="0 0 24 24" fill="currentColor" width="22" height="22"><path d="M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2z"/></svg></div>
    </div>
    <div class="stat-card sc-green">
      <div><div class="stat-val">${completed}</div><div class="stat-label">Completed Today</div></div>
      <div class="stat-icon si-green"><svg viewBox="0 0 24 24" fill="currentColor" width="22" height="22"><path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></div>
    </div>`;

  // Appointments as mini-table
  const aEl = document.getElementById('dash-appts');
  if (!appts?.length) {
    aEl.innerHTML = `<div class="empty">No appointments today</div>`;
  } else {
    aEl.innerHTML = `<table class="dash-table">
      <thead><tr><th>Time</th><th>Patient</th><th>Reason</th><th>Status</th></tr></thead>
      <tbody>${appts.slice(0, 8).map(a => `
        <tr>
          <td style="font-family:var(--mono);color:var(--primary);font-weight:600;font-size:12px">${formatTime(a.scheduled_at)}</td>
          <td style="font-weight:500">${a.patient_name || '<span style="color:var(--text3);font-size:11px">—</span>'}</td>
          <td style="font-size:12px;color:var(--text3)">${a.reason || '—'}</td>
          <td>${statusBadge(a.status)}</td>
        </tr>`).join('')}
      </tbody></table>`;
  }

  // Encounters as feed
  const eEl = document.getElementById('dash-encounters');
  if (!encs?.length) {
    eEl.innerHTML = `<div class="empty">No open encounters</div>`;
  } else {
    eEl.innerHTML = `<div class="enc-feed">${encs.slice(0, 7).map(e => {
      const pid = String(e.patient_id || '');
      return `<div class="enc-feed-item" onclick="openEncounterPage('${e.encounter_id}','${e.patient_id}')">
        <div class="enc-feed-av">${pid.slice(0,2).toUpperCase()}</div>
        <div style="flex:1;min-width:0">
          <div class="enc-feed-name">${e.chief_complaint || 'No complaint'}</div>
          <div style="display:flex;gap:6px;margin-top:3px">
            <span class="badge badge-blue" style="font-size:10px">${e.encounter_type}</span>
            <span style="font-size:11px;color:var(--text4)">${formatDate(e.encounter_date)}</span>
          </div>
        </div>
      </div>`;
    }).join('')}</div>`;
  }
}
