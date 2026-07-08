/* Separamos el flujo de verificación en dos pasos (GET para validar y POST para confirmar) porque los escáneres automáticos de correo suelen seguir los enlaces y si el GET mutara el estado, los tokens se consumirían antes de que el usuario realmente hiciera clic */

const ALL_STATES = [
  "verify-loading",
  "verify-confirm",
  "verify-success",
  "verify-resend",
  "verify-already-used",
];

function showState(stateId) {
  ALL_STATES.forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.hidden = id !== stateId;
  });
  if (typeof lucide !== "undefined") lucide.createIcons();
}

function configureResendState(isExpired) {
  const icon = document.getElementById("verify-resend-icon");
  const title = document.getElementById("verify-resend-title");
  const subtitle = document.getElementById("verify-resend-subtitle");

  if (isExpired) {
    if (icon) icon.setAttribute("data-lucide", "clock-alert");
    if (title) title.textContent = "El enlace expiró";
    if (subtitle)
      subtitle.textContent =
        "Los enlaces de verificación son válidos por 24 horas. Solicita uno nuevo y revisa tu bandeja.";
  } else {
    if (icon) icon.setAttribute("data-lucide", "link-2-off");
    if (title) title.textContent = "Enlace inválido";
    if (subtitle)
      subtitle.textContent =
        "Este enlace de verificación no es válido o ya no existe. Puedes solicitar uno nuevo ingresando tu correo.";
  }
}

// Aplicamos GET para validación segura sin mutación
async function verifyToken() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("token");

  if (!token) {
    configureResendState(false);
    showState("verify-resend");
    return;
  }

  try {
    // Consumimos el endpoint con GET para asegurar que no se produzcan efectos secundarios; la librería cliente extrae el payload automáticamente
    const result = await verifyEmailToken(token);

    const subtitle = document.getElementById("verify-confirm-subtitle");
    if (subtitle && result.email) {
      subtitle.textContent = `Tu enlace es válido para ${result.email}. Haz clic en el botón para activar tu cuenta.`;
    }

    const confirmBtn = document.getElementById("verify-confirm-btn");
    if (confirmBtn) {
      confirmBtn.addEventListener("click", () => confirmVerification(token), {
        once: true, // Aplicamos un solo clic para evitar múltiples envíos
      });
    }

    showState("verify-confirm");
  } catch (error) {
    const code = error.code || "";

    if (code === "TOKEN_EXPIRED") {
      configureResendState(true);
      showState("verify-resend");
    } else if (code === "TOKEN_ALREADY_USED") {
      showState("verify-already-used");
    } else {
      configureResendState(false);
      showState("verify-resend");
    }
  }
}

async function confirmVerification(token) {
  const confirmBtn = document.getElementById("verify-confirm-btn");
  const errorBox = document.getElementById("verify-confirm-error");
  const originalText = confirmBtn ? confirmBtn.textContent : "";

  if (errorBox) errorBox.hidden = true;
  if (confirmBtn) {
    confirmBtn.disabled = true;
    confirmBtn.textContent = "Verificando...";
  }

  try {
    await confirmEmailVerification(token);
    showState("verify-success");
  } catch (error) {
    // Capturamos el error específico por si el token se consumió en paralelo durante el intervalo entre la validación inicial y el clic manual.
    const code = error.code || "";

    if (code === "TOKEN_ALREADY_USED") {
      showState("verify-already-used");
    } else if (code === "TOKEN_EXPIRED") {
      configureResendState(true);
      showState("verify-resend");
    } else {
      if (errorBox) {
        errorBox.textContent =
          error.message || "No se pudo verificar. Intenta de nuevo.";
        errorBox.hidden = false;
      }
      if (confirmBtn) {
        confirmBtn.disabled = false;
        confirmBtn.textContent = originalText;
        // Restauramos el escuchador de eventos porque la bandera de un solo clic lo consumió durante el intento fallido.
        confirmBtn.addEventListener("click", () => confirmVerification(token), {
          once: true,
        });
      }
    }
  }
}

async function handleResendSubmit(event) {
  event.preventDefault();

  const form = event.target;
  const submitBtn = document.getElementById("verify-resend-submit");
  const errorBox = document.getElementById("verify-resend-error");
  const okBox = document.getElementById("verify-resend-ok");
  const originalText = submitBtn.textContent;

  errorBox.hidden = true;
  okBox.hidden = true;
  submitBtn.disabled = true;
  submitBtn.textContent = "Enviando...";

  try {
    // Asumimos un resultado exitoso constante para prevenir que un atacante descubra cuáles correos están registrados en nuestro sistema.
    const result = await resendVerificationEmail(form.email.value.trim());
    okBox.textContent =
      result.message ||
      "Si el correo existe y no ha sido verificado, se envió un nuevo enlace.";
    okBox.hidden = false;
    form.email.value = "";
  } catch (error) {
    errorBox.textContent =
      error.message || "No se pudo enviar el enlace. Intenta más tarde.";
    errorBox.hidden = false;
  } finally {
    submitBtn.disabled = false;
    submitBtn.textContent = originalText;
  }
}

document.addEventListener("DOMContentLoaded", () => {
  initAuthClose();

  const resendForm = document.getElementById("verify-resend-form");
  if (resendForm) resendForm.addEventListener("submit", handleResendSubmit);

  verifyToken();
});
