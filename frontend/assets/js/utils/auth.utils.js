const PASSWORD_RULES = {
  length: (value) => value.length >= 8,
  upper: (value) => /[A-Z]/.test(value),
  number: (value) => /\d/.test(value),
  special: (value) => /[^A-Za-z0-9]/.test(value),
};

function updatePasswordChecklist(password) {
  Object.entries(PASSWORD_RULES).forEach(([rule, check]) => {
    const item = document.querySelector(`[data-rule="${rule}"]`);
    if (!item) return;
    item.classList.toggle("is-valid", check(password));
  });
}

function initAuthClose() {
  // Esta pantalla no es un overlay real sobre otra pagina, asi que cerrar
  // significa volver al historial si existe, o caer a index.html si el
  // usuario llego aqui directamente (ej. por un enlace compartido).
  const closeButton = document.querySelector("[data-auth-close]");
  if (!closeButton) return;
  closeButton.addEventListener("click", () => {
    if (window.history.length > 1) {
      window.history.back();
    } else {
      window.location.href = "index.html";
    }
  });
}