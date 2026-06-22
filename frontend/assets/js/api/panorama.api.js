async function getSummary() {
  return apiGet("/panorama/summary");
}

async function getTopSkills(limit = 5) {
  return apiGet(`/panorama/skills/top?limit=${limit}`);
}
