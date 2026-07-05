function setAuthMode(mode) {
  const screen = document.querySelector("[data-auth-screen]");
  screen.dataset.authMode = mode;

  document.querySelectorAll("[data-auth-heading]").forEach((panel) => {
    panel.hidden = panel.dataset.authHeading !== mode;
  });

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

function showRegisterConfirmation(email) {
  const registerPanel = document.querySelector('[data-auth-form="register"]');
  if (!registerPanel) return;

  registerPanel.innerHTML = `
    <div class="verify-state" style="margin-top: var(--space-6)">
      <div class="verify-state__icon verify-state__icon--success">
        <i data-lucide="mail-check"></i>
      </div>
      <h2 class="verify-state__title">¡Revisa tu correo!</h2>
      <p class="verify-state__subtitle text-body">
        Enviamos un enlace de verificación a <strong>${email}</strong>.
        Haz clic en él para activar tu cuenta.
      </p>
      <p class="text-body-sm" style="color: var(--color-text-secondary); margin-top: var(--space-2)">
        ¿No llegó? Revisa la carpeta de spam o
        <button type="button" class="auth-form-panel__switch-link" id="reg-resend-btn">
          solicita un nuevo enlace
        </button>.
      </p>
    </div>
  `;

  if (typeof lucide !== "undefined") lucide.createIcons();

  const resendBtn = document.getElementById("reg-resend-btn");
  if (resendBtn) {
    resendBtn.addEventListener("click", async () => {
      resendBtn.disabled = true;
      resendBtn.textContent = "Enviando...";
      try {
        await apiPost("/auth/resend-verification", { email });
        resendBtn.textContent = "¡Enviado!";
      } catch {
        resendBtn.textContent = "Error al reenviar";
        resendBtn.disabled = false;
      }
    });
  }
}

function showUnverifiedBanner(form, email) {
  const existing = document.getElementById("login-unverified-banner");
  if (existing) existing.remove();

  const banner = document.createElement("div");
  banner.id = "login-unverified-banner";
  banner.className = "login-unverified-banner";
  banner.setAttribute("role", "alert");
  banner.innerHTML = `
    <p class="login-unverified-banner__msg">
      Verifica tu correo antes de iniciar sesión.
      Revisa tu bandeja de entrada en <strong>${email}</strong>.
    </p>
    <button type="button" class="btn btn--secondary login-unverified-banner__btn" id="login-resend-btn">
      Reenviar correo de verificación
    </button>
  `;

  form.insertAdjacentElement("afterend", banner);

  const resendBtn = document.getElementById("login-resend-btn");
  if (resendBtn) {
    resendBtn.addEventListener("click", async () => {
      resendBtn.disabled = true;
      resendBtn.textContent = "Enviando...";
      try {
        await apiPost("/auth/resend-verification", { email });
        resendBtn.textContent = "¡Enviado! Revisa tu bandeja.";
      } catch {
        resendBtn.textContent = "Error al reenviar. Intenta de nuevo.";
        resendBtn.disabled = false;
      }
    });
  }
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
  const email = form.email.value;

  try {
    await apiPost("/auth/register", {
      first_name: firstName,
      last_name: lastName,
      email: email,
      password: form.password.value,
    });
    // No redirigimos al panorama porque el registro exitoso ya no otorga sesión; requerimos que el usuario confirme su correo primero.
    showRegisterConfirmation(email);
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
  // Limpia cualquier banner de reenvío previo
  const prevBanner = document.getElementById("login-unverified-banner");
  if (prevBanner) prevBanner.remove();

  submitButton.disabled = true;
  submitButton.textContent = "Iniciando sesión...";

  try {
    await apiPost("/auth/login", {
      email: form.email.value,
      password: form.password.value,
    });
    window.location.href = "panorama.html";
  } catch (error) {
    if (error.code === "EMAIL_NOT_VERIFIED") {
      showUnverifiedBanner(form, form.email.value);
    } else {
      errorBox.textContent = error.message;
      errorBox.hidden = false;
    }
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
