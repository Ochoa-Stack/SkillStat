async function handleForgotSubmit(event) {
  event.preventDefault();

  const form = event.target;
  const submitButton = form.querySelector("[data-forgot-submit]");
  const messageBox = document.querySelector("[data-forgot-message]");
  const originalText = submitButton.textContent;

  const emailValue = form.email.value.trim();

  if (!emailValue) {
    messageBox.textContent = "Por favor ingresa tu correo.";
    messageBox.hidden = false;
    messageBox.style.color = "";
    messageBox.style.borderColor = "";
    return;
  }

  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailRegex.test(emailValue)) {
    messageBox.textContent = "Ingresa un formato de correo válido.";
    messageBox.hidden = false;
    messageBox.style.color = "";
    messageBox.style.borderColor = "";
    return;
  }

  messageBox.hidden = true;
  submitButton.disabled = true;
  submitButton.textContent = "Enviando...";

  try {
    const response = await apiPost("/auth/forgot-password", {
      email: emailValue,
    });
    messageBox.textContent =
      response.message ||
      "Si el correo existe, recibirás un enlace de recuperación.";
    messageBox.style.color = "var(--color-accent-green)";
    messageBox.style.borderColor = "var(--color-accent-green)";
    messageBox.hidden = false;
    form.reset();
  } catch (error) {
    messageBox.textContent = error.message;
    messageBox.style.color = "";
    messageBox.style.borderColor = "";
    messageBox.hidden = false;
  } finally {
    submitButton.disabled = false;
    submitButton.textContent = originalText;
  }
}

function initAuthClose() {
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
  initAuthClose();
  const form = document.querySelector("[data-forgot-form]");
  if (form) {
    form.addEventListener("submit", handleForgotSubmit);
  }
});
