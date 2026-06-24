async function initIndexPage() {
  try {
    const [summary, topSkills] = await Promise.all([
      getSummary(),
      getTopSkills(5),
    ]);

    const topSkill = topSkills[0];

    document.querySelector('[data-metric="top-skill"]').textContent =
      topSkill.name;
    document.querySelector('[data-metric="top-skill-detail"]').textContent =
      `${formatNumber(topSkill.demand_count)} vacantes la mencionan`;

    document.querySelector('[data-metric="skills-tracked"]').textContent =
      formatNumber(summary.total_skills_tracked);
    document.querySelector(
      '[data-metric="skills-tracked-detail"]',
    ).textContent = "Catalogadas y actualizadas a diario";

    document.querySelector('[data-metric="total-jobs"]').textContent =
      formatNumber(summary.total_jobs);
    document.querySelector('[data-metric="total-jobs-detail"]').textContent =
      "Vacantes tecnológicas reales en México";

    document.querySelector('[data-metric="preview-jobs"]').textContent =
      formatNumber(summary.total_jobs);
    document.querySelector('[data-metric="preview-skill"]').textContent =
      topSkill.name;
  } catch (error) {
    console.error("No se pudieron cargar los datos del Panorama:", error);

    document.querySelectorAll("[data-metric]").forEach((element) => {
      if (element.textContent.trim() === "Cargando datos...") {
        element.textContent = "No disponible";
      }
    });
  }
}

document.addEventListener("DOMContentLoaded", initIndexPage);
