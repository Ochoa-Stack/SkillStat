// Controla el toggle de tema claro/oscuro y persiste la eleccion del usuario en localStorage. La persistencia importa porque el tema por defecto del sistema es light, y forzar al usuario a re-elegir dark en cada visita seria una mala experiencia.

(function () {
  const STORAGE_KEY = 'skillstat-theme';
  const root = document.documentElement;
  const toggleButton = document.querySelector('[data-theme-toggle]');

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
  }

  const storedTheme = localStorage.getItem(STORAGE_KEY);
  if (storedTheme) {
    applyTheme(storedTheme);
  }

  if (toggleButton) {
    toggleButton.addEventListener('click', function () {
      const current = root.getAttribute('data-theme');
      const next = current === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      localStorage.setItem(STORAGE_KEY, next);
    });
  }
})();
