async function loadSkillsChart(limit) {
  const skills = await getTopSkills(limit);
  const chartContainer = document.querySelector("[data-skills-chart]");
  renderSkillsChart(chartContainer, skills);
}

function bindSkillsFilters() {
  document.querySelectorAll("[data-skills-limit]").forEach((button) => {
    button.addEventListener("click", async () => {
      document
        .querySelectorAll("[data-skills-limit]")
        .forEach((btn) => btn.classList.remove("pill--active"));
      button.classList.add("pill--active");

      const limit = Number(button.dataset.skillsLimit);
      await loadSkillsChart(limit);
    });
  });
}

async function initPanoramaPage() {
  try {
    const summary = await getSummary();

    document.querySelector('[data-metric="active-jobs"]').textContent =
      formatNumber(summary.total_jobs);
    document.querySelector('[data-metric="active-jobs-detail"]').textContent =
      "Tecnología · México";

    document.querySelector('[data-metric="active-companies"]').textContent =
      formatNumber(summary.total_companies);
    document.querySelector(
      '[data-metric="active-companies-detail"]',
    ).textContent = "Empresas únicas registradas";

    document.querySelector(
      '[data-metric="skills-tracked-panorama"]',
    ).textContent = formatNumber(summary.total_skills_tracked);
    document.querySelector(
      '[data-metric="skills-tracked-panorama-detail"]',
    ).textContent = "Catalogadas y actualizadas a diario";

    await loadSkillsChart(5);
    bindSkillsFilters();
  } catch (error) {
    console.error("No se pudieron cargar los datos del Panorama:", error);

    document.querySelectorAll("[data-metric]").forEach((element) => {
      if (element.textContent.trim() === "Cargando datos...") {
        element.textContent = "No disponible";
      }
    });
  }
}

document.addEventListener("DOMContentLoaded", initPanoramaPage);
