// Salva preferenza tema in localStorage e applica data-theme su <html>
(function() {
    const KEY = "rsa-theme";
    const html = document.documentElement;
    const saved = localStorage.getItem(KEY);
    if (saved === "light" || saved === "dark") html.setAttribute("data-theme", saved);

    window.toggleTheme = function() {
        const current = html.getAttribute("data-theme");
        const next = current === "dark" ? "light" : "dark";
        html.setAttribute("data-theme", next);
        localStorage.setItem(KEY, next);
    };
})();