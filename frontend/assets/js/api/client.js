// API_BASE_URL se define en assets/js/config.js, que debe cargarse mediante un <script> antes que este archivo en cada HTML.

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

function getCsrfToken() {
  // Flask-JWT-Extended emite la cookie csrf_access_token sin la bandera httpOnly intencionalmente. Esto nos permite leerla desde JavaScript en el navegador y adjuntarla como el header X-CSRF-TOKEN en las peticiones que mutan estado, completando el patrón Double Submit Cookie para protegernos de ataques CSRF sin requerir que nuestro backend de API mantenga estado de sesiones.
  const match = document.cookie.match(
    new RegExp("(^| )csrf_access_token=([^;]+)"),
  );
  if (match) {
    return decodeURIComponent(match[2]);
  }
  return null;
}

async function apiPost(endpoint, body) {
  const headers = { "Content-Type": "application/json" };
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers["X-CSRF-TOKEN"] = csrfToken;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "POST",
    headers: headers,
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

async function apiPatch(endpoint, body) {
  const headers = { "Content-Type": "application/json" };
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers["X-CSRF-TOKEN"] = csrfToken;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "PATCH",
    headers: headers,
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

async function apiDelete(endpoint) {
  const headers = {};
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers["X-CSRF-TOKEN"] = csrfToken;
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    method: "DELETE",
    headers: headers,
    credentials: "include",
  });

  if (!response.ok) {
    const errorBody = await parseErrorBody(response);
    throw buildApiError(errorBody, response, endpoint);
  }

  // DELETE podria devolver 204 No Content o un JSON con datos, lo manejamos sin fallar.
  try {
    const json = await response.json();
    return json.data || null;
  } catch {
    return null;
  }
}
