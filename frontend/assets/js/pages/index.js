async function initIndexPage() {
  try {
    const [summary, topSkills] = await Promise.all([
      getSummary(),
      getTopSkills(10),
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

    renderTopSkillsChips(topSkills);
  } catch (error) {
    console.error("No se pudieron cargar los datos del Panorama:", error);

    document.querySelectorAll("[data-metric]").forEach((element) => {
      if (element.textContent.trim() === "Cargando datos...") {
        element.textContent = "No disponible";
      }
    });

    // La seccion de top skills es aditiva; si falla, se oculta sin romper el resto.
    const topSkillsSection = document.getElementById("top-skills-section");
    if (topSkillsSection) topSkillsSection.hidden = true;
  }
}

function renderTopSkillsChips(skills) {
  const container = document.getElementById("top-skills-chips");
  if (!container || !Array.isArray(skills) || skills.length === 0) {
    const section = document.getElementById("top-skills-section");
    if (section) section.hidden = true;
    return;
  }

  const fragment = document.createDocumentFragment();
  skills.slice(0, 10).forEach(function (skill) {
    const chip = document.createElement("div");
    chip.className = "chip";
    chip.setAttribute("role", "listitem");

    const name = document.createElement("span");
    name.textContent = skill.name;

    const badge = document.createElement("span");
    badge.className = "chip__badge";
    badge.textContent = formatNumber(skill.demand_count);
    badge.setAttribute("aria-label", `${formatNumber(skill.demand_count)} vacantes`);

    chip.appendChild(name);
    chip.appendChild(badge);
    fragment.appendChild(chip);
  });

  container.appendChild(fragment);
}

document.addEventListener("DOMContentLoaded", initIndexPage);
