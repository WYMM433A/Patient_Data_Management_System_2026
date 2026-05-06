/* ============================================================
   PDMS — Navigation & Page Routing
   ============================================================ */

const NAV_CONFIG = {
  system_admin: [
    { label: "Staff Management", page: "users",     icon: "people"   },
    { label: "Audit Logs",       page: "audit",     icon: "history"  }
  ],
  doctor: [
    { label: "Dashboard",    page: "dashboard",   icon: "dashboard" },
    { label: "Patients",     page: "patients",    icon: "person"    },
    { label: "Appointments", page: "appointments",icon: "calendar"  },
    { label: "Care Plans",   page: "care-plans",  icon: "medical"   }
  ],
  nurse: [
    { label: "Patients",     page: "patients",    icon: "person"   },
    { label: "Appointments", page: "appointments",icon: "calendar" }
  ],
  receptionist: [
    { label: "Patients",     page: "patients",    icon: "person"   },
    { label: "Appointments", page: "appointments",icon: "calendar" }
  ],
  lab_technician: [
    { label: "Lab Orders",   page: "lab-orders",  icon: "lab" }
  ],
  pharmacist: [
    { label: "Prescriptions", page: "prescriptions", icon: "rx" }
  ]
};

const ICONS = {
  dashboard: `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z"/></svg>`,
  person:    `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M12 12c2.7 0 4.8-2.1 4.8-4.8S14.7 2.4 12 2.4 7.2 4.5 7.2 7.2 9.3 12 12 12zm0 2.4c-3.2 0-9.6 1.6-9.6 4.8V21.6h19.2v-2.4c0-3.2-6.4-4.8-9.6-4.8z"/></svg>`,
  calendar:  `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19 3h-1V1h-2v2H8V1H6v2H5C3.9 3 3 3.9 3 5v16c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 18H5V8h14v13z"/></svg>`,
  people:    `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>`,
  history:   `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M13 3c-4.97 0-9 4.03-9 9H1l3.89 3.89.07.14L9 12H6c0-3.87 3.13-7 7-7s7 3.13 7 7-3.13 7-7 7c-1.93 0-3.68-.79-4.94-2.06l-1.42 1.42C8.27 19.99 10.51 21 13 21c4.97 0 9-4.03 9-9s-4.03-9-9-9zm-1 5v5l4.28 2.54.72-1.21-3.5-2.08V8H12z"/></svg>`,
  lab:       `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M19.8 18.4L14 10.67V6.5l1.35-1.69c.26-.33.03-.81-.39-.81H9.04c-.42 0-.65.48-.39.81L10 6.5v4.17L4.2 18.4c-.49.66-.02 1.6.8 1.6h14c.82 0 1.29-.94.8-1.6z"/></svg>`,
  medical:   `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 6h-2.18c.07-.44.18-.88.18-1.36C18 2.53 15.47 0 12.82 0 11.34 0 10 .73 9.18 1.85 8.36.73 7.02 0 5.55 0 2.89 0 .36 2.53.36 5.18.36 5.66.47 6.1.54 6.54H2c-1.1 0-2 .9-2 2v13c0 1.1.9 2 2 2h18c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-7 13h-2v-4H7v-2h4v-4h2v4h4v2h-4v4z"/></svg>`,
  rx:        `<svg viewBox="0 0 24 24" fill="currentColor"><path d="M20 3H4v10c0 2.21 1.79 4 4 4h6c2.21 0 4-1.79 4-4v-3h2c1.11 0 2-.89 2-2V5c0-1.11-.89-2-2-2zm0 5h-2V5h2v3zM4 19h16v2H4z"/></svg>`
};

function showPage(id) {
  document.querySelectorAll(".page").forEach(p => p.classList.remove("active"));
  const p = document.getElementById("page-" + id);
  if (p) p.classList.add("active");
  _currentPage = id;

  const titles = {
    dashboard:        "Dashboard",
    patients:         "Patients",
    appointments:     "Appointments",
    users:            "Staff Management",
    audit:            "Audit Logs",
    "lab-orders":     "Lab Orders",
    prescriptions:    "Prescriptions",
    "care-plans":     "Care Plans",
    "patient-profile":"Patient Profile",
    encounter:        "Encounter Detail"
  };
  document.getElementById("topbar-title").textContent = titles[id] || id;

  document.querySelectorAll(".nav-item").forEach(n => {
    n.classList.toggle("active", n.dataset.page === id);
  });
}

async function loadPage(page) {
  if      (page === "dashboard")     await loadDashboard();
  else if (page === "patients")      await loadPatients();
  else if (page === "appointments")  await loadAppointments();
  else if (page === "users")         await loadUsers();
  else if (page === "audit")         await loadAudit();
  else if (page === "lab-orders")    await loadLabOrders();
  else if (page === "prescriptions") await loadPharmRx();
  else if (page === "care-plans")    await loadCarePlans();
}
