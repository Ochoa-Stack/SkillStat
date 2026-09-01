let allSkills = [];

async function initSalariosPage() {
  const container = document.getElementById("salarios-filters");
  const errorContainer = document.getElementById("salarios-error-container");

  try {
    const skills = await getTopSkills(50);
    allSkills = skills;

    skills.forEach((skill) => {
      const btn = document.createElement("button");
      btn.className = "pill";
      btn.type = "button";
      btn.textContent = skill.name;
      btn.dataset.skillId = skill.skill_id;

      btn.addEventListener("click", () => handleSkillSelection(btn, skill));
      container.appendChild(btn);
    });
  } catch (error) {
    console.error("Error al cargar skills para salarios:", error);
    errorContainer.innerHTML =
      '<p class="form-error">No se pudieron cargar las habilidades. Intenta recargar la página.</p>';
  }
}

async function handleSkillSelection(btn, skill) {
  const container = document.getElementById("salarios-filters");
  container
    .querySelectorAll(".pill")
    .forEach((p) => p.classList.remove("pill--active"));
  btn.classList.add("pill--active");

  const loadingEl = document.getElementById("salarios-loading");
  const resultEl = document.getElementById("salary-result");
  const emptyEl = document.getElementById("salary-empty");

  loadingEl.hidden = false;
  resultEl.hidden = true;
  emptyEl.hidden = true;

  try {
    const data = await apiGet(`/panorama/salaries?skill_id=${skill.skill_id}`);

    if (
      !data ||
      data.sample_size === 0 ||
      (data.avg_salary_min === null && data.avg_salary_max === null)
    ) {
      showEmptyState();
      return;
    }

    const minMonthly = Math.round(data.avg_salary_min / 12);
    const maxMonthly = Math.round(data.avg_salary_max / 12);

    document.getElementById("salary-skill-name").textContent = data.skill_name;
    document.getElementById("salary-range-value").textContent =
      `$${formatNumber(minMonthly)} - $${formatNumber(maxMonthly)}`;
    document.getElementById("salary-sample").textContent =
      `basado en ${data.sample_size} vacantes con salario declarado`;

    loadingEl.hidden = true;
    resultEl.hidden = false;
  } catch (error) {
    console.error("Error al obtener salario:", error);
    showEmptyState(); // Según las instrucciones, fallar el fetch se presenta igual que no tener datos.
  }
}

function showEmptyState() {
  document.getElementById("salarios-loading").hidden = true;
  document.getElementById("salary-result").hidden = true;
  document.getElementById("salary-empty").hidden = false;
}

document.addEventListener("DOMContentLoaded", initSalariosPage);
