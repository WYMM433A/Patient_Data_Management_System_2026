/* ============================================================
   PDMS — Audit Logs
   ============================================================ */

let _auditPage  = 1;
const AUDIT_PER = 50;
let   _auditAll = [];
let   _userMap  = {};   // user_id → { name, initials, color }

// Avatar color (same logic as users.js)
function _auditAvColor(name = '') {
  let h = 0;
  for (let c of name) h = (h * 31 + c.charCodeAt(0)) & 0xff;
  return `user-av-${h % 8}`;
}

function _actionBadge(action) {
  const map = {
    CREATE: 'badge-action-create',
    UPDATE: 'badge-action-update',
    DELETE: 'badge-action-delete',
    VIEW:   'badge-action-view',
  };
  const cls = map[(action || '').toUpperCase()] || 'badge-action-view';
  return `<span class="${cls}">${(action || '—').toUpperCase()}</span>`;
}

async function loadAudit() {
  _auditPage = 1;

  // Build params
  const action = document.getElementById('audit-action')?.value || '';
  const from   = document.getElementById('audit-from')?.value   || '';
  const to     = document.getElementById('audit-to')?.value     || '';
  const table  = document.getElementById('audit-table')?.value  || '';
  const params = new URLSearchParams({ limit: 200 });
  if (action) params.set('action',         action);
  if (from)   params.set('date_from',      from + 'T00:00:00');
  if (to)     params.set('date_to',        to   + 'T23:59:59');
  if (table)  params.set('table_affected', table);

  // Fetch audit logs; re-use users already cached by users.js (_allUsers) or fetch fresh
  const userSource = (typeof _allUsers !== 'undefined' && _allUsers.length)
    ? Promise.resolve(_allUsers)
    : api('/users?limit=200');

  const [data, users] = await Promise.all([
    api(`/audit-logs?${params}`),
    userSource,
  ]);

  // Always rebuild map (normalize keys to lowercase for UUID case-insensitivity)
  if (users && users.length) {
    _userMap = {};
    users.forEach(u => {
      const name = `${u.first_name} ${u.last_name}`;
      _userMap[String(u.user_id).toLowerCase()] = {
        name,
        initials: ((u.first_name?.[0] || '') + (u.last_name?.[0] || '')).toUpperCase(),
        color:    _auditAvColor(name),
      };
    });
  }

  _auditAll = data || [];
  _renderAuditPage();
}

function _renderAuditPage() {
  const start  = (_auditPage - 1) * AUDIT_PER;
  const slice  = _auditAll.slice(start, start + AUDIT_PER);
  const tbody  = document.getElementById('audit-tbody');
  const footer = document.getElementById('audit-footer');

  if (!_auditAll.length) {
    tbody.innerHTML = `<tr><td colspan="6"><div class="empty">No log entries matching filters</div></td></tr>`;
    if (footer) footer.textContent = '';
    return;
  }

  tbody.innerHTML = slice.map(l => {
    // Normalize UUID to lowercase for map lookup
    const uid  = l.user_id ? String(l.user_id).toLowerCase() : '';
    const user = uid ? _userMap[uid] : null;
    const userCell = user
      ? `<span class="audit-av ${user.color}">${user.initials}</span>${user.name}`
      : uid
        ? `<span class="audit-av user-av-7" style="font-size:9px">${uid.slice(0,4).toUpperCase()}</span><span style="color:var(--text3);font-size:12px;font-family:var(--mono)">${uid.slice(0,13)}…</span>`
        : `<span style="color:var(--text4);font-size:12px">System</span>`;

    const ts = l.timestamp ? new Date(l.timestamp).toLocaleString('en-GB', {
      year:'numeric', month:'2-digit', day:'2-digit',
      hour:'2-digit', minute:'2-digit', second:'2-digit', hour12: false
    }).replace(',', '') : '—';

    const recId = l.record_id ? l.record_id.toString().slice(0, 13) + '…' : '—';

    return `<tr>
      <td style="font-size:12px;font-family:var(--mono);white-space:nowrap">${ts}</td>
      <td style="font-size:13px">${userCell}</td>
      <td>${_actionBadge(l.action)}</td>
      <td style="font-size:13px">${l.module || '—'}</td>
      <td style="font-size:13px;font-family:var(--mono)">${l.table_affected || '—'}</td>
      <td style="font-size:12px;color:var(--text3);font-family:var(--mono)">${recId}</td>
    </tr>`;
  }).join('');

  // Footer: pagination
  const end       = Math.min(start + AUDIT_PER, _auditAll.length);
  const totalPages = Math.ceil(_auditAll.length / AUDIT_PER);
  if (footer) {
    const prevDis = _auditPage <= 1           ? 'disabled' : '';
    const nextDis = _auditPage >= totalPages  ? 'disabled' : '';
    footer.innerHTML = `
      <span>Showing <strong>${start + 1}–${end}</strong> of <strong>${_auditAll.length}</strong> records</span>
      <div style="display:flex;gap:6px;align-items:center">
        <button class="btn btn-sm" ${prevDis} onclick="_auditPage--;_renderAuditPage()">&#8592; Prev</button>
        <span style="font-size:12px">Page ${_auditPage} / ${totalPages}</span>
        <button class="btn btn-sm" ${nextDis} onclick="_auditPage++;_renderAuditPage()">Next &#8594;</button>
      </div>`;
  }
}

function resetAuditFilters() {
  ['audit-action','audit-from','audit-to','audit-table'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  loadAudit();
}

function exportAuditCSV() {
  if (!_auditAll.length) { toast('No data to export', 'info'); return; }
  const headers = ['Timestamp','User','Action','Module','Table','Record ID','IP'];
  const rows = _auditAll.map(l => {
    const uid  = l.user_id?.toString() || '';
    const user = _userMap[uid];
    return [
      l.timestamp || '',
      user ? user.name : uid,
      l.action || '',
      l.module || '',
      l.table_affected || '',
      l.record_id || '',
      l.ip_address || '',
    ].map(v => `"${String(v).replace(/"/g,'""')}"`).join(',');
  });
  const csv  = [headers.join(','), ...rows].join('\n');
  const blob = new Blob([csv], { type: 'text/csv' });
  const a    = document.createElement('a');
  a.href     = URL.createObjectURL(blob);
  a.download = `audit_log_${new Date().toISOString().slice(0,10)}.csv`;
  a.click();
  toast('CSV exported', 'success');
}

