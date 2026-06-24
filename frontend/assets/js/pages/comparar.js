const MIN_SKILLS = 2;
const MAX_SKILLS = 5;
let selectedSkillIds = [];

function updateSelectorState() {
  const count = selectedSkillIds.length;

  document.querySelector("[data-selected-count]").textContent =
    `${count} de ${MAX_SKILLS} seleccionadas`;

  document.querySelector("[data-compare-button]").disabled =
    count < MIN_SKILLS || count > MAX_SKILLS;
}

function toggleSkillChip(chip, skillId) {
  const isActive = chip.classList.contains("pill--active");

  if (isActive) {
    chip.classList.remove("pill--active");
    selectedSkillIds = selectedSkillIds.filter((id) => id !== skillId);
  } else {
    // No dejamos seleccionar una sexta habilidad porque el endpoint de comparacion rechaza mas de 5 con un error de validacion.
    if (selectedSkillIds.length >= MAX_SKILLS) return;
    chip.classList.add("pill--active");
    selectedSkillIds.push(skillId);
  }

  updateSelectorState();

  // Ocultamos resultados previos porque ya no corresponden a la seleccion actual; evita mostrar una comparacion desincronizada.
  document.querySelector("[data-comparar-results]").hidden = true;
  document.querySelector("[data-comparar-error]").hidden = true;
}

function renderCompareResults(skills) {
  const resultsSection = document.querySelector("[data-comparar-results]");
  const container = resultsSection.querySelector(".container");

  container.innerHTML = "";

  skills.forEach((skill) => {
    const card = document.createElement("article");
    card.className = "metric-card surface comparar-results__card";

    const header = document.createElement("div");
    header.className = "card-header";

    const label = document.createElement("span");
    label.className = "metric-card__label text-label";
    label.textContent = skill.skill_name;

    header.appendChild(label);

    const value = document.createElement("p");
    value.className = "metric-card__value text-metric";
    value.textContent = formatNumber(skill.demand_count);

    const detail = document.createElement("p");
    detail.className = "metric-card__detail text-body-sm";
    detail.textContent = `${formatNumber(skill.demand_count)} vacantes la mencionan`;

    const salary = document.createElement("p");
    salary.className = "comparar-results__salary text-body-sm";
    // Adzuna entrega salary_min/salary_max como cifras anuales, pero en Mexico el salario se discute en terminos mensuales, asi que convertimos aqui en vez de mostrar el monto anual sin contexto.
    salary.textContent = skill.avg_salary
      ? `${formatCurrency(skill.avg_salary / 12)} MXN mensual aprox.`
      : "Sin datos de salario disponibles";

    card.append(header, value, detail, salary);
    container.appendChild(card);
  });

  resultsSection.hidden = false;
}

async function handleCompareClick() {
  const button = document.querySelector("[data-compare-button]");
  const originalText = button.textContent;

  button.disabled = true;
  button.textContent = "Comparando...";

  document.querySelector("[data-comparar-error]").hidden = true;

  try {
    const results = await getCompareSkills(selectedSkillIds);
    renderCompareResults(results);
  } catch (error) {
    console.error("No se pudo completar la comparación:", error);
    document.querySelector("[data-comparar-error]").hidden = false;
  } finally {
    button.textContent = originalText;
    updateSelectorState();
  }
}

async function renderSkillChips() {
  const catalogs = await getCatalogs();
  const container = document.querySelector("[data-skill-chips]");

  const sortedSkills = [...catalogs.skills].sort((a, b) =>
    a.name.localeCompare(b.name),
  );

  sortedSkills.forEach((skill) => {
    const chip = document.createElement("button");
    chip.className = "pill comparar-selector__chip";
    chip.type = "button";
    chip.textContent = skill.name;
    chip.dataset.skillId = skill.id;
    chip.addEventListener("click", () => toggleSkillChip(chip, skill.id));
    container.appendChild(chip);
  });
}

async function initComparePage() {
  try {
    await renderSkillChips();
    updateSelectorState();
    document
      .querySelector("[data-compare-button]")
      .addEventListener("click", handleCompareClick);
  } catch (error) {
    console.error(
      "No se pudieron cargar las habilidades para comparar:",
      error,
    );
  }
}

document.addEventListener("DOMContentLoaded", initComparePage);
