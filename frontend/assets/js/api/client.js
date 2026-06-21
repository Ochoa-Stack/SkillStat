const API_BASE_URL = "http://127.0.0.1:5000/api";

async function apiGet(endpoint) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);

  if (!response.ok) {
    throw new Error(`Error ${response.status} al consultar ${endpoint}`);
  }

  const json = await response.json();
  return json.data;
}
