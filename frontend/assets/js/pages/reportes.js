/* Reutilizamos getSummary() y getTopSkills() de panorama.api.js. Este script no depende de chart.init.js ni de renderSkillsChart(). */

function formatReportDate(date) {
  return date.toLocaleDateString("es-MX", {
    day: "numeric",
    month: "long",
    year: "numeric",
  });
}

function renderSkillsTable(skills) {
  const tbody = document.querySelector("[data-skills-tbody]");
  if (!tbody) return;

  const maxDemand = Math.max(...skills.map((s) => s.demand_count));

  tbody.innerHTML = "";

  skills.forEach((skill, index) => {
    const pct = ((skill.demand_count / maxDemand) * 100).toFixed(1);
    const isTop = skill.demand_count === skills[0].demand_count;

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td class="reporte-table__rank">${index + 1}</td>
      <td class="reporte-table__skill${isTop ? " reporte-table__skill--top" : ""}">${skill.name}</td>
      <td class="reporte-table__mentions">${formatNumber(skill.demand_count)}</td>
      <td class="reporte-table__pct">${pct}%</td>
    `;
    tbody.appendChild(tr);
  });
}

async function initReportePage() {
  // Insertamos la fecha de generación
  const now = new Date();
  const dateStr = formatReportDate(now);
  const dateEl = document.querySelector("[data-report-date]");
  if (dateEl) dateEl.textContent = dateStr;

  // Enlazamos el botón de imprimir
  const printBtn = document.querySelector("[data-print-btn]");
  if (printBtn) {
    printBtn.addEventListener("click", () => window.print());
  }

  try {
    const [summary, skills] = await Promise.all([
      getSummary(),
      getTopSkills(15),
    ]);

    renderMarketMetrics(summary, {
      activeJobs: '[data-metric="reporte-active-jobs"]',
      activeJobsDetail: '[data-metric="reporte-active-jobs-detail"]',
      activeCompanies: '[data-metric="reporte-active-companies"]',
      activeCompaniesDetail: '[data-metric="reporte-active-companies-detail"]',
      skillsTracked: '[data-metric="reporte-skills-tracked"]',
      skillsTrackedDetail: '[data-metric="reporte-skills-tracked-detail"]',
    });
    renderSkillsTable(skills);
  } catch (error) {
    console.error("No se pudieron cargar los datos del reporte:", error);

    document.querySelectorAll("[data-metric]").forEach((el) => {
      if (el.textContent.trim() === "Cargando datos...") {
        el.textContent = "No disponible";
      }
    });

    const tbody = document.querySelector("[data-skills-tbody]");
    if (tbody) {
      tbody.innerHTML = `
        <tr>
          <td colspan="4" style="text-align:center; padding: var(--space-6); color: var(--color-text-secondary);">
            No se pudieron cargar los datos. Intenta recargar la página.
          </td>
        </tr>
      `;
    }
  }
}

document.addEventListener("DOMContentLoaded", initReportePage);
