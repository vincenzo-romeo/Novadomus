document.addEventListener("DOMContentLoaded", () => {
  const dt = document.querySelector('input[type="datetime-local"]');
  if (dt && !dt.value) {
    const now = new Date();
    const pad = n => String(n).padStart(2, "0");
    dt.value = `${now.getFullYear()}-${pad(now.getMonth()+1)}-${pad(now.getDate())}T${pad(now.getHours())}:${pad(now.getMinutes())}`;
  }

  // consenti virgola decimale per °C
  const temp = document.getElementById("id_temp_c");
  if (temp) {
    temp.addEventListener("input", () => {
      temp.value = temp.value.replace(",", ".");
    });
  }
});
