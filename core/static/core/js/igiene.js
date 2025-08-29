document.addEventListener("DOMContentLoaded", () => {
  const dt = document.querySelector('input[type="datetime-local"]');
  if (dt && !dt.value) {
    const now = new Date();
    const pad = n => String(n).padStart(2, "0");
    dt.value = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
  }
});
