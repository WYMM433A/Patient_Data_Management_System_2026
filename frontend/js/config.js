/* ============================================================
   PDMS — Config & Global State
   All modules share these variables via the global (window) scope.
   ============================================================ */

const BASE = "http://localhost:8000";

let _token       = localStorage.getItem("access_token") || "";
let _currentUser = null;

// Routing state
let _currentPage        = null;
let _currentEncounterId = null;
let _currentPatientId   = null;
let _currentLabOrderId  = null;
let _encIsOpen          = true;

// Module-level caches
let _roles           = [];   // user roles list (admin page)
let _apptSearchTimer = null; // debounce timer for appointment patient search

try {
  _currentUser = JSON.parse(localStorage.getItem("user") || "null");
} catch (e) {
  _currentUser = null;
}
