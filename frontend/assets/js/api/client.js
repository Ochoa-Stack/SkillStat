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

async function ensureCsrfToken() {
  // Retorna el token cacheado si ya existe en sessionStorage — evita una peticion de red en cada mutacion despues de la primera.
  const cached = sessionStorage.getItem("csrf_token");
  if (cached) return cached;

  // El frontend no puede leer csrf_access_token desde document.cookie porque backend y frontend viven en subdominios distintos de onrender.com, que esta en la Public Suffix List. Solicitamos el claim csrf directamente al backend via un GET autenticado con la cookie httpOnly que el navegador si envia automaticamente en peticiones cross-site con credentials: "include".
  const response = await fetch(`${API_BASE_URL}/auth/csrf-token`, {
    credentials: "include",
  });

  if (!response.ok) {
    // Si no hay sesion activa (ej. durante login, register o google auth), el endpoint devuelve 401. No es una falla critica — retornamos null para que la peticion original continue sin el header CSRF, tal como funciona correctamente para los endpoints que no tienen @jwt_required().
    console.warn(
      "[ensureCsrfToken] No se pudo obtener el token CSRF (sin sesion activa), continuando sin el header.",
    );
    return null;
  }

  const json = await response.json();
  const token = json.data?.csrf_token;
  if (token) {
    sessionStorage.setItem("csrf_token", token);
  }
  return token || null;
}

async function apiPost(endpoint, body) {
  const headers = { "Content-Type": "application/json" };
  const csrfToken = await ensureCsrfToken();
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
  const csrfToken = await ensureCsrfToken();
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
  const csrfToken = await ensureCsrfToken();
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
