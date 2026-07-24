// Configuración de entorno del frontend. En desarrollo (localhost / 127.0.0.1) apunta al servidor Flask local. En producción apunta al Web Service desplegado en Render. El placeholder [PENDIENTE-URL-REAL-DE-RENDER] debe reemplazarse con la URL real una vez que el servicio esté creado en Render.
const API_BASE_URL =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:5000/api"
    : "https://[PENDIENTE-URL-REAL-DE-RENDER]/api";
