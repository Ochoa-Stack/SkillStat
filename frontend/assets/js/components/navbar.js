// Controla el toggle de tema claro/oscuro y persiste la eleccion del usuario en localStorage. La persistencia importa porque el tema por defecto del sistema es light, y forzar al usuario a re-elegir dark en cada visita seria una mala experiencia.
(function () {
  const STORAGE_KEY = "skillstat-theme";
  const root = document.documentElement;
  const toggleButtons = document.querySelectorAll("[data-theme-toggle]");

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
  }

  const storedTheme = localStorage.getItem(STORAGE_KEY);
  if (storedTheme) {
    applyTheme(storedTheme);
  }

  toggleButtons.forEach(function (button) {
    button.addEventListener("click", function () {
      const current = root.getAttribute("data-theme");
      const next = current === "dark" ? "light" : "dark";
      applyTheme(next);
      localStorage.setItem(STORAGE_KEY, next);
    });
  });
})();

// Controla el drawer de navegacion en mobile. Usamos una clase en vez de display:none directo para poder animar la entrada y salida con CSS.
(function () {
  const drawer = document.querySelector("[data-nav-drawer]");
  const openButton = document.querySelector("[data-nav-drawer-open]");
  const closeTriggers = document.querySelectorAll("[data-nav-drawer-close]");

  if (!drawer || !openButton) return;

  function openDrawer() {
    drawer.classList.add("nav-drawer--open");
    drawer.setAttribute("aria-hidden", "false");
    openButton.setAttribute("aria-expanded", "true");
    document.body.style.overflow = "hidden";
  }

  function closeDrawer() {
    drawer.classList.remove("nav-drawer--open");
    drawer.setAttribute("aria-hidden", "true");
    openButton.setAttribute("aria-expanded", "false");
    document.body.style.overflow = "";
    openButton.focus();
  }

  openButton.addEventListener("click", openDrawer);

  closeTriggers.forEach(function (trigger) {
    trigger.addEventListener("click", closeDrawer);
  });

  document.addEventListener("keydown", function (event) {
    if (
      event.key === "Escape" &&
      drawer.classList.contains("nav-drawer--open")
    ) {
      closeDrawer();
    }
  });
})();
