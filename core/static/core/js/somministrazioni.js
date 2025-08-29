document.addEventListener("DOMContentLoaded", () => {
  const selPaz  = document.getElementById("id_sel_paziente");
  const stato   = document.getElementById("id_stato");
  const dose    = document.getElementById("id_dose_erogata");
  const datao   = document.getElementById("id_data_ora");
  const riga    = document.getElementById("id_riga");
  const udmVis  = document.getElementById("id_dose_udm_vis");
  const formaSel = document.getElementById("id_forma_vis"); // <-- nuovo

  // Cambio paziente: ricarica con querystring ?paziente=...
  if (selPaz) {
    selPaz.addEventListener("change", () => {
      const id = selPaz.value || "";
      const u = new URL(window.location.href);
      if (id) u.searchParams.set("paziente", id);
      else u.searchParams.delete("paziente");
      window.location.href = u.toString();
    });
  }

  function toggleObblighi() {
    const ok = stato && stato.value === "SOMMINISTRATO";
    if (dose)  dose.required  = ok;
    if (datao) datao.required = ok;
  }

  function applyRigaDefaults() {
    if (!riga) return;
    const meta = (window.RIGHE_META || {})[riga.value];
    if (!meta) {
      if (udmVis)  udmVis.value  = "";
      if (dose)    dose.placeholder = "";
      if (formaSel) formaSel.value = "";
      return;
    }
    // UDM e dose
    if (udmVis) udmVis.value = meta.udm || "";
    if (dose && (!dose.value || dose.value.trim() === "")) {
      dose.value = meta.dose || "";
    }
    if (dose && meta.dose) dose.placeholder = meta.dose;

    // --- NUOVO: Forma dalla riga selezionata (codice: "cpr", "bust", "F", "FL", "gtt") ---
    if (formaSel) formaSel.value = meta.forma || "";
  }

  if (stato) {
    toggleObblighi();
    stato.addEventListener("change", toggleObblighi);
  }
  if (riga) {
    applyRigaDefaults();                  // iniziale (se riga già selezionata)
    riga.addEventListener("change", applyRigaDefaults);
  }
});
