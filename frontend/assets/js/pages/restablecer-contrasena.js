function updateResetSubmitState() {
  const form = document.querySelector("[data-reset-form]");
  if (!form) return;

  const password = form.password.value;
  const allRulesPass = Object.values(PASSWORD_RULES).every((check) =>
    check(password),
  );
  const passwordsMatch =
    password.length > 0 && password === form.confirmPassword.value;

  document.querySelector("[data-reset-submit]").disabled = !(
    allRulesPass && passwordsMatch
  );
}

function showTerminalState(message, isSuccess = false) {
  document.getElementById("reset-form-container").hidden = true;

  const statusContainer = document.getElementById("reset-status-container");
  const statusMessage = document.getElementById("reset-status-message");
  const actionButton = document.getElementById("reset-status-action");

  statusContainer.hidden = false;
  statusMessage.textContent = message;
  statusMessage.hidden = false;

  if (isSuccess) {
    statusMessage.style.color = "var(--color-accent-green)";
    statusMessage.style.borderColor = "var(--color-accent-green)";
    actionButton.textContent = "Iniciar sesión";
    actionButton.href = "register.html";
    actionButton.className = "btn btn--primary";
  } else {
    statusMessage.style.color = "";
    statusMessage.style.borderColor = "";
    actionButton.textContent = "Solicitar nuevo enlace";
    actionButton.href = "olvide-contrasena.html";
    actionButton.className = "btn btn--secondary";
  }
}

async function handleResetSubmit(event) {
  event.preventDefault();

  const form = event.target;
  const submitButton = form.querySelector("[data-reset-submit]");
  const errorBox = form.querySelector("[data-reset-error]");
  const originalText = submitButton.textContent;

  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get("token");

  errorBox.hidden = true;
  submitButton.disabled = true;
  submitButton.textContent = "Actualizando...";

  try {
    const response = await resetPassword(token, form.password.value);

    // Si todo sale bien solo ocultamos form y mostramos link de login
    showTerminalState(
      response.message || "Contraseña actualizada correctamente.",
      true,
    );
  } catch (error) {
    // Si el error es de token invalido o expirado, mostramos estado terminal
    if (error.code === "INVALID_TOKEN") {
      showTerminalState(error.message, false);
    } else {
      // Otros errores se muestran en el form
      errorBox.textContent = error.message;
      errorBox.hidden = false;
      submitButton.disabled = false;
      submitButton.textContent = originalText;
    }
  }
}

function initResetForm() {
  const urlParams = new URLSearchParams(window.location.search);
  const token = urlParams.get("token");

  if (!token) {
    showTerminalState("Enlace inválido o incompleto", false);
    return;
  }

  const form = document.querySelector("[data-reset-form]");
  if (!form) return;

  form.addEventListener("submit", handleResetSubmit);
  form.password.addEventListener("input", () => {
    updatePasswordChecklist(form.password.value);
    updateResetSubmitState();
  });
  form.confirmPassword.addEventListener("input", updateResetSubmitState);
}

document.addEventListener("DOMContentLoaded", () => {
  initAuthClose();
  initResetForm();
});
