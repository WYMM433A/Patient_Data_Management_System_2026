/* ============================================================
   PDMS — Utilities
   Pure helper functions with no side-effects.
   ============================================================ */

function formatDate(dt) {
  if (!dt) return "—";
  try {
    return new Date(dt).toLocaleDateString("en-GB", {
      day: "2-digit", month: "short", year: "numeric"
    });
  } catch { return dt; }
}

function formatDateTime(dt) {
  if (!dt) return "—";
  try {
    return new Date(dt).toLocaleString("en-GB", {
      day: "2-digit", month: "short", year: "numeric",
      hour: "2-digit", minute: "2-digit"
    });
  } catch { return dt; }
}

function formatTime(dt) {
  if (!dt) return "—";
  try {
    return new Date(dt).toLocaleTimeString("en-GB", {
      hour: "2-digit", minute: "2-digit"
    });
  } catch { return dt; }
}

function statusBadge(s) {
  const map = {
    scheduled:  "badge-gray",
    confirmed:  "badge-blue",
    checked_in: "badge-orange",
    completed:  "badge-green",
    cancelled:  "badge-red",
    open:       "badge-blue",
    closed:     "badge-gray"
  };
  return `<span class="badge ${map[s] || "badge-gray"}">${s?.replace(/_/g, " ") || "—"}</span>`;
}

function toast(msg, type = "info") {
  const c = document.getElementById("toast-container");
  const t = document.createElement("div");
  t.className = `toast ${type}`;
  t.textContent = msg;
  c.appendChild(t);
  setTimeout(() => t.remove(), 3500);
}

function openModal(id)  { document.getElementById(id).classList.add("open"); }
function closeModal(id) { document.getElementById(id).classList.remove("open"); }
