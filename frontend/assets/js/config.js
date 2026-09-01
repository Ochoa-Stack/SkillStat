// Configuración de entorno del frontend. En desarrollo (localhost / 127.0.0.1) apunta al servidor Flask local. En producción apunta al Web Service desplegado en Render.
const API_BASE_URL =
  window.location.hostname === "localhost" ||
  window.location.hostname === "127.0.0.1"
    ? "http://127.0.0.1:5000/api"
    : "https://skillstat.onrender.com/api";

