// Inicializamos el boton y el One Tap de Google Identity Services
const GOOGLE_CLIENT_ID = "891817364914-fpq222eqf2jk1ticoldkuq5u74h5lurt.apps.googleusercontent.com";

function getCurrentGoogleTheme() {
  return document.documentElement.dataset.theme === "dark"
    ? "filled_black"
    : "outline";
}

function renderGoogleButton() {
  const container = document.querySelector("[data-google-button]");
  if (!container || typeof google === "undefined") return;

  container.innerHTML = "";

  // La libreria exige un ancho fijo en pixeles, no soporta porcentajes, asi que leemos el ancho real disponible para que el boton nunca se desborde en pantallas angostas.
  const availableWidth = Math.min(container.offsetWidth || 360, 360);

  google.accounts.id.renderButton(container, {
    type: "standard",
    theme: getCurrentGoogleTheme(),
    size: "large",
    text: "continue_with",
    shape: "rectangular",
    locale: "es",
    width: availableWidth,
  });
}
window.refreshGoogleButtonTheme = renderGoogleButton;

function handleGoogleCredential(response) {
  const errorBox = document.querySelector("[data-google-error]");
  if (errorBox) errorBox.hidden = true;

  apiPost("/auth/google", { credential: response.credential })
    .then(() => {
      window.location.href = "panorama.html";
    })
    .catch((error) => {
      console.error(
        "No se pudo completar el inicio de sesión con Google:",
        error,
      );
      if (errorBox) {
        errorBox.textContent = error.message;
        errorBox.hidden = false;
      }
    });
}

function initGoogleAuth() {
  if (typeof google === "undefined") return;

  google.accounts.id.initialize({
    client_id: GOOGLE_CLIENT_ID,
    callback: handleGoogleCredential,
    use_fedcm_for_prompt: true,
    use_fedcm_for_button: true,
    itp_support: true,
  });

  renderGoogleButton();

  // One Tap se dispara una sola vez por carga de pagina; no se vuelve a mandar llamar cuando el usuario alterna entre los modos login/registro dentro de la misma pagina.
  google.accounts.id.prompt();

  let resizeTimeout;
  window.addEventListener("resize", () => {
    clearTimeout(resizeTimeout);
    resizeTimeout = setTimeout(renderGoogleButton, 200);
  });
}

window.addEventListener("load", initGoogleAuth);
