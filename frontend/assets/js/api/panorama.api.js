async function getSummary() {
  return apiGet("/panorama/summary");
}

async function getTopSkills(limit = 5) {
  return apiGet(`/panorama/skills/top?limit=${limit}`);
}

async function getCatalogs() {
  return apiGet("/panorama/catalogs");
}

async function getCompareSkills(skillIds) {
  // La respuesta de /compare viene envuelta en { skills: [...] }, a diferencia de otros endpoints que devuelven el array directo.
  const result = await apiGet(
    `/panorama/compare?skill_ids=${skillIds.join(",")}`,
  );
  return result.skills;
}
