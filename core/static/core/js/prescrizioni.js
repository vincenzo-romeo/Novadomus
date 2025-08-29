document.addEventListener("DOMContentLoaded", () => {
  const addBtn = document.getElementById("add-row");
  const container = document.getElementById("righe-container");
  const tmpl = document.getElementById("empty-form");
  if (!addBtn || !container || !tmpl) return;

  // ---------- Helpers ----------
  function findRow(el) {
    return el.closest('.card[data-form-index]');
  }

  // Salva le option originali del select farmaco per quella riga
  function ensureCache(row) {
    const selFarmaco = row.querySelector('select[name$="-farmaco"]');
    if (!selFarmaco) return;
    if (!selFarmaco._allOptions) {
      selFarmaco._allOptions = Array.from(selFarmaco.options).map(o => ({
        value: o.value,
        text: o.text,
        code: (window.FARMACI_FORMA_CODE && window.FARMACI_FORMA_CODE[o.value]) || ""
      }));
    }
  }

  // Re-render delle option del farmaco filtrando per "code" (forma)
  function renderFarmaciByForma(row, code) {
    const selFarmaco = row.querySelector('select[name$="-farmaco"]');
    if (!selFarmaco) return;
    ensureCache(row);
    const cur = selFarmaco.value;
    const list = selFarmaco._allOptions;

    // ricostruisci le option
    selFarmaco.innerHTML = "";
    (code ? list.filter(o => o.code === code) : list).forEach(o => {
      const opt = document.createElement('option');
      opt.value = o.value;
      opt.textContent = o.text;
      selFarmaco.appendChild(opt);
    });

    // preserva la selezione se ancora valida, altrimenti nessuna
    if ([...selFarmaco.options].some(o => o.value === cur)) {
      selFarmaco.value = cur;
    } else {
      selFarmaco.value = "";
    }
  }

  // Quando cambia il farmaco → aggiorna la select forma
  function updateFormaFromFarmaco(row) {
    const selFarmaco = row.querySelector('select[name$="-farmaco"]');
    const selForma = row.querySelector('select[name$="-farmaco_forma_vis"]');
    if (!selFarmaco || !selForma) return;
    const fid = selFarmaco.value || "";
    const code = (window.FARMACI_FORMA_CODE && window.FARMACI_FORMA_CODE[fid]) || "";
    selForma.value = code || "";
    // opzionale: allinea anche il filtro dei farmaci alla forma corrente
    renderFarmaciByForma(row, selForma.value || "");
  }

  // Quando cambia la forma → filtra la lista dei farmaci
  function onFormaChange(row) {
    const selForma = row.querySelector('select[name$="-farmaco_forma_vis"]');
    if (!selForma) return;
    renderFarmaciByForma(row, selForma.value || "");
  }

  // ---------- Init righe già presenti ----------
  container.querySelectorAll('.card[data-form-index]').forEach(row => {
    ensureCache(row);
    updateFormaFromFarmaco(row); // imposta la forma iniziale dalla selezione del farmaco
  });

  // Deleghe
  document.addEventListener('change', (e) => {
    if (e.target && e.target.matches('select[name$="-farmaco"]')) {
      updateFormaFromFarmaco(findRow(e.target));
    } else if (e.target && e.target.matches('select[name$="-farmaco_forma_vis"]')) {
      onFormaChange(findRow(e.target));
    }
  });

  // Observer per righe aggiunte dinamicamente
  new MutationObserver((muts) => {
    muts.forEach(m => {
      m.addedNodes.forEach(node => {
        if (node.nodeType === 1 && node.matches('.card[data-form-index]')) {
          ensureCache(node);
          updateFormaFromFarmaco(node);
        }
      });
    });
  }).observe(container, {childList: true});

  // ---------- Pulsante "Aggiungi riga" ----------
  addBtn.addEventListener("click", (e) => {
    e.preventDefault();
    const totalInput = document.querySelector('input[name$="-TOTAL_FORMS"]');
    if (!totalInput) return;
    const index = parseInt(totalInput.value, 10);

    const html = tmpl.innerHTML.replace(/__prefix__/g, index);
    const wrap = document.createElement("div");
    wrap.innerHTML = html.trim();
    const node = wrap.firstElementChild;

    if (node && node.matches('.card') && !node.getAttribute('data-form-index')) {
      node.setAttribute('data-form-index', String(index));
    }

    container.appendChild(node);
    totalInput.value = index + 1;

    ensureCache(node);
    updateFormaFromFarmaco(node);
  });
});
