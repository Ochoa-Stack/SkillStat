const API_BASE_URL = "http://127.0.0.1:5000/api";

async function parseErrorBody(response) {
  try {
    const json = await response.json();
    return json.error || null;
  } catch {
    return null;
  }
}

function formatErrorMessage(message, response, endpoint) {
  if (!message) {
    return `Error ${response.status} al consultar ${endpoint}`;
  }
  if (typeof message === "string") {
    return message;
  }
  // Los errores de validacion de Marshmallow llegan como un objeto {campo: [mensajes]} en vez de un string plano. Los aplanamos para que siempre haya texto legible que mostrar al usuario.
  return Object.values(message).flat().join(" ");
}

function buildApiError(errorBody, response, endpoint) {
  const error = new Error(
    formatErrorMessage(errorBody?.message, response, endpoint),
  );
  error.code = errorBody?.code || "UNKNOWN_ERROR";
  error.status = response.status;
  return error;
}

async function apiGet(endpoint) {
  // Mandamos credentials para que el navegador adjunte la cookie de sesion en endpoints protegidos (ej. /auth/me). En endpoints publicos esto no tiene efecto, no hay cookie que enviar.
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    credentials: "include",
  });

  if (!response.ok) {
    const errorBody = await parseErrorBody(response);
    throw buildApiError(errorBody, response, endpoint);
  }

  const json = await response.json();
  return json.data;
}

async function apiPost(endpoint, body) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const errorBody = await parseErrorBody(response);
    throw buildApiError(errorBody, response, endpoint);
  }

  const json = await response.json();
  return json.data;
}
