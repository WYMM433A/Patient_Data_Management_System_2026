/* ============================================================
   PDMS — Staff Management (system_admin)
   ============================================================ */

// ── Role metadata ─────────────────────────────────────────────────
const ROLE_LABEL = {
  system_admin:   'SYSTEM ADMIN',
  doctor:         'DOCTOR',
  nurse:          'NURSE',
  lab_technician: 'LAB TECHNICIAN',
  receptionist:   'RECEPTIONIST',
};
const ROLE_CSS = {
  system_admin:   'badge-role-admin',
  doctor:         'badge-role-doctor',
  nurse:          'badge-role-nurse',
  lab_technician: 'badge-role-lab',
  receptionist:   'badge-role-rec',
};
const ROLE_DESC = {
  system_admin:   'User has full system access and can manage all staff accounts.',
  doctor:         'User has full access to patient records and medical charting.',
  nurse:          'User can record vitals, view clinical notes, and update vaccinations.',
  lab_technician: 'User can process lab orders and submit test results.',
  receptionist:   'User manages patient registration and appointment scheduling.',
};
const ROLE_PILL_ICON = {
  system_admin:   '🛡',
  doctor:         '👤',
  nurse:          '🩺',
  lab_technician: '🧪',
  receptionist:   '💬',
};

function _roleKey(roleName = '') {
  return (roleName || '').toLowerCase().replace(/\s+/g, '_');
}
function _roleLabel(roleName) {
  return ROLE_LABEL[_roleKey(roleName)] || roleName?.toUpperCase() || '—';
}
function _roleCss(roleName) {
  return ROLE_CSS[_roleKey(roleName)] || 'badge-role-rec';
}
function _roleDesc(roleName) {
  return ROLE_DESC[_roleKey(roleName)] || '';
}

// Avatar color deterministic from name
function _avColor(name = '') {
  let h = 0;
  for (let c of name) h = (h * 31 + c.charCodeAt(0)) & 0xff;
  return `user-av-${h % 8}`;
}
function _avInitials(first = '', last = '') {
  return ((first[0] || '') + (last[0] || '')).toUpperCase();
}

// Relative time
function _relTime(dt) {
  if (!dt) return 'Never';
  const diff = Date.now() - new Date(dt).getTime();
  const m = Math.floor(diff / 60000);
  if (m < 1)   return 'Just now';
  if (m < 60)  return `${m} min${m > 1 ? 's' : ''} ago`;
  const h = Math.floor(m / 60);
  if (h < 24)  return `${h} hour${h > 1 ? 's' : ''} ago`;
  const d = Math.floor(h / 24);
  if (d < 7)   return `${d} day${d > 1 ? 's' : ''} ago`;
  return formatDate(dt);
}

// ── Module-level user cache ───────────────────────────────────────
let _allUsers  = [];   // cached user list from API
const _userById = {};  // user_id → user object

// ── Load all users (fetch + render) ──────────────────────────────
async function loadUsers() {
  // Fetch users and roles in parallel (only on real load, not search)
  const [users, roles] = await Promise.all([
    api('/users?limit=200'),
    _roles.length ? Promise.resolve(_roles) : api('/users/roles'),
  ]);

  if (roles && !Array.isArray(roles)) {
    // api returned null on roles error — keep existing _roles
  } else if (roles) {
    _roles = roles;
  }

  // Build role dropdowns ONCE (only when roles first populated)
  _buildRoleDropdown('user-role', _roles);
  _buildRolePills(_roles);
  _syncEditRoleDropdown(_roles);

  // Cache users
  _allUsers = users || [];
  _allUsers.forEach(u => { _userById[String(u.user_id)] = u; });

  // Stats (always show full totals, not filtered)
  const active   = _allUsers.filter(u =>  u.is_active);
  const inactive = _allUsers.filter(u => !u.is_active);
  const elTotal    = document.getElementById('stat-total');
  const elActive   = document.getElementById('stat-active');
  const elInactive = document.getElementById('stat-inactive');
  if (elTotal)    elTotal.textContent    = String(_allUsers.length).padStart(2, '0');
  if (elActive)   elActive.textContent   = String(active.length).padStart(2, '0');
  if (elInactive) elInactive.textContent = String(inactive.length).padStart(2, '0');

  // Render table (with current search term if any)
  _renderUserTable(document.getElementById('user-search')?.value || '');
}

// ── Render table from cache (client-side filter) ─────────────────
function _renderUserTable(search) {
  const q = (search || '').toLowerCase();
  const visible = q
    ? _allUsers.filter(u =>
        `${u.first_name} ${u.last_name} ${u.username} ${u.email}`.toLowerCase().includes(q))
    : _allUsers;

  const tbody  = document.getElementById('users-tbody');
  const footer = document.getElementById('users-footer');
  if (!tbody) return;

  if (!visible.length) {
    tbody.innerHTML = `<tr><td colspan="7"><div class="empty">No staff members found</div></td></tr>`;
    if (footer) footer.textContent = '';
    return;
  }

  tbody.innerHTML = visible.map(u => {
    const uid      = String(u.user_id);
    const initials = _avInitials(u.first_name, u.last_name);
    const avClass  = _avColor(u.first_name + u.last_name);
    const badge    = `<span class="badge-role ${_roleCss(u.role?.role_name)}">${_roleLabel(u.role?.role_name)}</span>`;
    const toggle   = `<label class="toggle-sw" title="${u.is_active ? 'Active' : 'Inactive'}">
      <input type="checkbox" ${u.is_active ? 'checked' : ''}
        onchange="toggleUserStatus('${uid}', this.checked)">
      <span class="toggle-track"><span class="toggle-thumb"></span></span>
    </label>`;
    return `<tr>
      <td>
        <div style="display:flex;align-items:center;gap:8px">
          <div class="user-av ${avClass}">${initials}</div>
          <div style="font-weight:600;font-size:13px">${u.first_name} ${u.last_name}</div>
        </div>
      </td>
      <td><span style="color:var(--text3);font-size:13px">@${u.username}</span></td>
      <td>${badge}</td>
      <td style="font-size:13px;color:var(--text2)">${u.email || '—'}</td>
      <td>${toggle}</td>
      <td style="font-size:12px;color:var(--text3);white-space:nowrap">${_relTime(u.last_login)}</td>
      <td>
        <div style="display:flex;gap:4px">
          <button class="action-icon" title="Edit" onclick="openEditUser('${uid}')">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
          </button>
          <button class="action-icon del" title="${u.is_active ? 'Deactivate' : 'Activate'}" onclick="deactivateUser('${uid}', ${!u.is_active})">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6"/><path d="M10 11v6"/><path d="M14 11v6"/><path d="M9 6V4a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2"/></svg>
          </button>
        </div>
      </td>
    </tr>`;
  }).join('');

  if (footer) {
    footer.innerHTML = `Showing <strong>1–${visible.length}</strong> of <strong>${_allUsers.length}</strong> staff members`;
  }
}

function _buildRoleDropdown(id, roles) {
  const sel = document.getElementById(id);
  if (!sel) return;
  sel.innerHTML = `<option value="">Select a role…</option>` +
    roles.map(r => `<option value="${r.role_id}">${r.role_name.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}</option>`).join('');
}

function _syncEditRoleDropdown(roles) {
  const sel = document.getElementById('edit-role');
  if (!sel) return;
  sel.innerHTML = roles.map(r =>
    `<option value="${r.role_id}">${r.role_name.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase())}</option>`
  ).join('');
  sel.onchange = () => _updateEditRoleInfo(sel.value, roles);
}

function _updateEditRoleInfo(roleId, roles) {
  const role = (roles || _roles).find(r => r.role_id === roleId);
  const box  = document.getElementById('edit-role-info');
  if (!box || !role) return;
  const key = _roleKey(role.role_name);
  box.innerHTML = `<span class="badge-role ${ROLE_CSS[key] || 'badge-role-rec'}" style="flex-shrink:0">ACTIVE ROLE: ${_roleLabel(role.role_name)}</span>
    <span>${_roleDesc(role.role_name)}</span>`;
}

function _buildRolePills(roles) {
  const container = document.getElementById('role-pills');
  if (!container) return;
  container.innerHTML = roles.map(r => {
    const key = _roleKey(r.role_name);
    return `<span class="role-pill ${ROLE_CSS[key] || ''}" data-role-id="${r.role_id}"
      onclick="selectRolePill(this,'${r.role_id}')">${ROLE_PILL_ICON[key] || ''} ${_roleLabel(r.role_name)}</span>`;
  }).join('');
}

function selectRolePill(el, roleId) {
  document.querySelectorAll('#role-pills .role-pill').forEach(p => p.classList.remove('active'));
  el.classList.add('active');
  document.getElementById('user-role').value = roleId;
}

// ── Toggle status inline ──────────────────────────────────────────
async function toggleUserStatus(uid, makeActive) {
  await api(`/users/${uid}`, { method: 'PATCH', body: JSON.stringify({ is_active: makeActive }) });
  const label = makeActive ? 'activated' : 'deactivated';
  toast(`Account ${label}`, makeActive ? 'success' : 'info');
  await loadUsers();  // re-fetch to sync cache
}

// ── Deactivate (trash icon) ───────────────────────────────────────
async function deactivateUser(uid, activate) {
  const msg = activate ? 'Reactivate this staff account?' : 'Deactivate this staff account?';
  if (!confirm(msg)) return;
  await api(`/users/${uid}`, { method: 'PATCH', body: JSON.stringify({ is_active: activate }) });
  toast(`Account ${activate ? 'activated' : 'deactivated'}`, 'success');
  loadUsers();
}

// ── Open edit modal (accepts user_id string) ────────────────────
function openEditUser(userId) {
  const u = _userById[String(userId)];
  if (!u) { toast('User not found', 'error'); return; }
  document.getElementById('edit-user-id').value   = u.user_id;
  document.getElementById('edit-fname').value     = u.first_name || '';
  document.getElementById('edit-lname').value     = u.last_name  || '';
  document.getElementById('edit-username').value  = u.username   || '';
  document.getElementById('edit-email').value     = u.email      || '';
  document.getElementById('edit-password').value  = '';
  document.getElementById('edit-confirm-pw').value = '';

  // Avatar
  const initials = _avInitials(u.first_name, u.last_name);
  const av = document.getElementById('edit-staff-av');
  av.className = `edit-staff-avatar ${_avColor(u.first_name + u.last_name)}`;
  av.textContent = initials;

  // Meta
  const joined = u.created_at ? `Joined ${new Date(u.created_at).toLocaleDateString('en-US',{month:'short',year:'numeric'})}` : '';
  document.getElementById('edit-staff-meta').textContent = `ID: STF-${u.user_id.slice(0,8).toUpperCase()} • ${joined}`;

  // Role dropdown
  const sel = document.getElementById('edit-role');
  if (sel && u.role?.role_id) {
    // Ensure roles are loaded
    if (!_roles.length) {
      api('/users/roles').then(roles => {
        _roles = roles || [];
        _syncEditRoleDropdown(_roles);
        sel.value = u.role.role_id;
        _updateEditRoleInfo(u.role.role_id, _roles);
      });
    } else {
      sel.value = u.role.role_id;
      _updateEditRoleInfo(u.role.role_id, _roles);
    }
  }

  // Status toggle
  const chk = document.getElementById('edit-is-active');
  chk.checked = !!u.is_active;
  document.getElementById('edit-status-title').textContent = u.is_active ? 'Active Account' : 'Inactive Account';
  const lastLogin = u.last_login ? `Last login was ${_relTime(u.last_login)}` : 'Never logged in';
  document.getElementById('edit-status-sub').textContent = lastLogin;

  // Deactivate button label
  const btn = document.getElementById('btn-deactivate-staff');
  btn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:-2px;margin-right:4px"><path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><line x1="17" y1="8" x2="23" y2="14"/><line x1="23" y1="8" x2="17" y2="14"/></svg>${u.is_active ? 'Deactivate Staff' : 'Reactivate Staff'}`;

  openModal('modal-edit-user');
}

// ── Save edit ─────────────────────────────────────────────────────
async function saveEditUser() {
  const uid = document.getElementById('edit-user-id').value;
  const pw  = document.getElementById('edit-password').value;
  const cpw = document.getElementById('edit-confirm-pw').value;

  if (pw && pw !== cpw) { toast('Passwords do not match', 'error'); return; }

  const body = {
    first_name: document.getElementById('edit-fname').value  || undefined,
    last_name:  document.getElementById('edit-lname').value  || undefined,
    email:      document.getElementById('edit-email').value  || undefined,
    role_id:    document.getElementById('edit-role').value   || undefined,
    is_active:  document.getElementById('edit-is-active').checked,
  };
  if (pw) body.password = pw;

  const r = await api(`/users/${uid}`, { method: 'PATCH', body: JSON.stringify(body) });
  if (r) {
    toast('Staff member updated', 'success');
    closeModal('modal-edit-user');
    loadUsers();
  }
}

// ── Password strength meter ───────────────────────────────────────
function _calcStrength(pw) {
  let s = 0;
  if (pw.length >= 8)  s++;
  if (/[A-Z]/.test(pw)) s++;
  if (/[0-9]/.test(pw)) s++;
  if (/[^A-Za-z0-9]/.test(pw)) s++;
  return s;
}
function updatePwStrength(value) {
  const wrap  = document.getElementById('pw-strength-wrap');
  const fill  = document.getElementById('pw-strength-fill');
  const label = document.getElementById('pw-strength-label');
  if (!value) { wrap.style.display = 'none'; return; }
  wrap.style.display = '';
  const s = _calcStrength(value);
  const levels = [
    { pct: '20%', color: '#ef4444', text: 'WEAK',    textColor: '#ef4444' },
    { pct: '45%', color: '#f97316', text: 'FAIR',    textColor: '#f97316' },
    { pct: '70%', color: '#f59e0b', text: 'GOOD',    textColor: '#f59e0b' },
    { pct: '100%',color: '#22c55e', text: 'STRONG',  textColor: '#22c55e' },
  ];
  const lv = levels[Math.max(0, s - 1)];
  fill.style.width      = lv.pct;
  fill.style.background = lv.color;
  label.textContent     = lv.text;
  label.style.color     = lv.textColor;
}

