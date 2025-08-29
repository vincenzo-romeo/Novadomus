document.addEventListener("DOMContentLoaded", () => {
  const sel = document.getElementById("paziente");
  if (sel) sel.addEventListener("change", () => sel.form.submit());
});
