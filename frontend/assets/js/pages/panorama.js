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

    renderMarketMetrics(summary, {
      activeJobs: '[data-metric="active-jobs"]',
      activeJobsDetail: '[data-metric="active-jobs-detail"]',
      activeCompanies: '[data-metric="active-companies"]',
      activeCompaniesDetail: '[data-metric="active-companies-detail"]',
      skillsTracked: '[data-metric="skills-tracked-panorama"]',
      skillsTrackedDetail: '[data-metric="skills-tracked-panorama-detail"]',
    });

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
