function setAuthMode(mode) {
  const screen = document.querySelector("[data-auth-screen]");
  screen.dataset.authMode = mode;

  document.querySelectorAll("[data-auth-form]").forEach((panel) => {
    panel.hidden = panel.dataset.authForm !== mode;
  });

  document.querySelectorAll("[data-auth-marketing]").forEach((panel) => {
    panel.hidden = panel.dataset.authMarketing !== mode;
  });
}

function initAuthToggle() {
  document.querySelectorAll("[data-auth-switch]").forEach((trigger) => {
    trigger.addEventListener("click", () => {
      setAuthMode(trigger.dataset.authSwitch);
    });
  });
}

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

function splitFullName(fullName) {
  const trimmed = fullName.trim();
  const firstSpaceIndex = trimmed.indexOf(" ");

  // Si no hay espacio, usamos el nombre completo como first_name y dejamos last_name vacio en blanco no es opcion porque el backend lo exige; en ese caso repetimos el nombre como apellido temporal.
  if (firstSpaceIndex === -1) {
    return { firstName: trimmed, lastName: trimmed };
  }

  return {
    firstName: trimmed.slice(0, firstSpaceIndex),
    lastName: trimmed.slice(firstSpaceIndex + 1),
  };
}

function updateRegisterSubmitState() {
  const form = document.querySelector("[data-register-form]");
  if (!form) return;

  const password = form.password.value;
  const allRulesPass = Object.values(PASSWORD_RULES).every((check) =>
    check(password),
  );
  const passwordsMatch =
    password.length > 0 && password === form.confirmPassword.value;
  const termsAccepted = form.acceptTerms.checked;

  document.querySelector("[data-register-submit]").disabled = !(
    allRulesPass &&
    passwordsMatch &&
    termsAccepted
  );
}

async function handleRegisterSubmit(event) {
  event.preventDefault();

  const form = event.target;
  const submitButton = form.querySelector("[data-register-submit]");
  const errorBox = document.querySelector("[data-register-error]");
  const originalText = submitButton.textContent;

  errorBox.hidden = true;
  submitButton.disabled = true;
  submitButton.textContent = "Creando cuenta...";

  const { firstName, lastName } = splitFullName(form.fullName.value);

  try {
    await apiPost("/auth/register", {
      first_name: firstName,
      last_name: lastName,
      email: form.email.value,
      password: form.password.value,
    });
    window.location.href = "panorama.html";
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.hidden = false;
    submitButton.disabled = false;
    submitButton.textContent = originalText;
  }
}

function initRegisterForm() {
  const form = document.querySelector("[data-register-form]");
  if (!form) return;

  form.addEventListener("submit", handleRegisterSubmit);
  form.password.addEventListener("input", () => {
    updatePasswordChecklist(form.password.value);
    updateRegisterSubmitState();
  });
  form.confirmPassword.addEventListener("input", updateRegisterSubmitState);
  form.acceptTerms.addEventListener("change", updateRegisterSubmitState);
}

async function handleLoginSubmit(event) {
  event.preventDefault();

  const form = event.target;
  const submitButton = form.querySelector("[data-login-submit]");
  const errorBox = document.querySelector("[data-login-error]");
  const originalText = submitButton.textContent;

  errorBox.hidden = true;
  submitButton.disabled = true;
  submitButton.textContent = "Iniciando sesión...";

  try {
    await apiPost("/auth/login", {
      email: form.email.value,
      password: form.password.value,
    });
    window.location.href = "panorama.html";
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.hidden = false;
    submitButton.disabled = false;
    submitButton.textContent = originalText;
  }
}

function initLoginForm() {
  const form = document.querySelector("[data-login-form]");
  if (!form) return;
  form.addEventListener("submit", handleLoginSubmit);
}

function initAuthClose() {
  // Esta pantalla no es un overlay real sobre otra pagina, asi que cerrar significa volver al historial si existe, o caer a index.html si el usuario llego aqui directamente (ej. por un enlace compartido).
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

document.addEventListener("DOMContentLoaded", () => {
  initAuthToggle();
  initAuthClose();
  initLoginForm();
  initRegisterForm();
});
