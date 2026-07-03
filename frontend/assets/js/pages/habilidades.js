let allSkills = [];
let activeCategory = "all";
let activeDemand = "all";
let searchQuery = "";
let maxDemand = 0;
let demandChecks = {};

async function initHabilidadesPage() {
  const loadingEl = document.getElementById("habilidades-loading");
  const errorEl = document.getElementById("habilidades-error");

  try {
    const skills = await getTopSkills(50);
    allSkills = skills;

    if (skills.length > 0) {
      maxDemand = Math.max(...skills.map((s) => s.demand_count));
    }

    loadingEl.hidden = true;

    setupFilters(skills);
    setupDemandFilters(skills);
    setupSearch();
    renderSkills();
  } catch (error) {
    console.error("Error al cargar habilidades:", error);
    loadingEl.innerHTML =
      '<p class="form-error">No se pudieron cargar las habilidades en este momento. Intenta de nuevo más tarde.</p>';
  }
}

function setupFilters(skills) {
  const filterContainer = document.getElementById("category-filters");

  // Extraemos categorías únicas (ignorando nulls)
  const categories = [
    ...new Set(skills.map((s) => s.category).filter((c) => c)),
  ].sort();

  categories.forEach((category) => {
    const btn = document.createElement("button");
    btn.className = "pill";
    btn.type = "button";
    btn.dataset.category = category;
    btn.textContent = category;

    btn.addEventListener("click", () => {
      // Removemos clase activa de todos
      filterContainer
        .querySelectorAll(".pill")
        .forEach((p) => p.classList.remove("pill--active"));
      // Agregamos al actual
      btn.classList.add("pill--active");

      activeCategory = category;
      renderSkills();
    });

    filterContainer.appendChild(btn);
  });

  // Agregamos evento al botón "Todas"
  const allBtn = filterContainer.querySelector('[data-category="all"]');
  if (allBtn) {
    allBtn.addEventListener("click", () => {
      filterContainer
        .querySelectorAll(".pill")
        .forEach((p) => p.classList.remove("pill--active"));
      allBtn.classList.add("pill--active");
      activeCategory = "all";
      renderSkills();
    });
  }
}

function setupDemandFilters(skills) {
  if (skills.length === 0) return;

  // Calculamos umbrales de demanda basados en el array real
  const demands = skills.map((s) => s.demand_count).sort((a, b) => a - b);
  const p33 = demands[Math.floor(demands.length * 0.33)];
  const p67 = demands[Math.floor(demands.length * 0.67)];

  const ranges = [
    { label: "Todas", value: "all", check: () => true },
    { label: "Alta demanda", value: "high", check: (d) => d >= p67 },
    {
      label: "Demanda media",
      value: "medium",
      check: (d) => d >= p33 && d < p67,
    },
    { label: "Baja demanda", value: "low", check: (d) => d < p33 },
  ];

  const toolbar = document.querySelector(".habilidades-toolbar");
  const categoryFilters = document.getElementById("category-filters");

  const demandFilters = document.createElement("div");
  demandFilters.id = "demand-filters";
  demandFilters.className = "habilidades-filters habilidades-filters--demand";
  demandFilters.setAttribute("role", "group");
  demandFilters.setAttribute("aria-label", "Filtrar por nivel de demanda");

  ranges.forEach((range, idx) => {
    demandChecks[range.value] = range.check;

    const btn = document.createElement("button");
    btn.className = "pill" + (idx === 0 ? " pill--active" : "");
    btn.type = "button";
    btn.dataset.demand = range.value;
    btn.textContent = range.label;

    btn.addEventListener("click", () => {
      demandFilters
        .querySelectorAll(".pill")
        .forEach((p) => p.classList.remove("pill--active"));
      btn.classList.add("pill--active");

      activeDemand = range.value;
      renderSkills();
    });

    demandFilters.appendChild(btn);
  });

  if (categoryFilters && categoryFilters.parentNode) {
    categoryFilters.parentNode.insertBefore(
      demandFilters,
      categoryFilters.nextSibling,
    );
  } else {
    toolbar.appendChild(demandFilters);
  }
}

function setupSearch() {
  const searchInput = document.getElementById("skill-search");
  if (searchInput) {
    searchInput.addEventListener("input", (e) => {
      searchQuery = e.target.value.toLowerCase().trim();
      renderSkills();
    });
  }
}

function renderSkills() {
  const listContainer = document.getElementById("habilidades-list");
  const emptyState = document.getElementById("habilidades-empty");

  listContainer.innerHTML = "";

  // Filtramos habilidades según categoría activa, búsqueda y demanda activa
  const filtered = allSkills.filter((skill) => {
    const matchesCategory =
      activeCategory === "all" || skill.category === activeCategory;
    const matchesSearch = skill.name.toLowerCase().includes(searchQuery);
    const matchesDemand = demandChecks[activeDemand]
      ? demandChecks[activeDemand](skill.demand_count)
      : true;
    return matchesCategory && matchesSearch && matchesDemand;
  });

  if (filtered.length === 0) {
    emptyState.hidden = false;
    listContainer.hidden = true;
    return;
  }

  emptyState.hidden = true;
  listContainer.hidden = false;

  const fragment = document.createDocumentFragment();

  filtered.forEach((skill) => {
    const item = document.createElement("article");
    item.className = "skill-item surface";

    // Aplicamos cálculo del ancho proporcional
    const percentage =
      maxDemand > 0 ? (skill.demand_count / maxDemand) * 100 : 0;

    item.innerHTML = `
      <div class="skill-item__header">
        <h2 class="skill-item__name">${skill.name}</h2>
        ${skill.category ? `<span class="skill-item__category">${skill.category}</span>` : ""}
      </div>
      
      <div class="skill-item__metrics">
        <div class="skill-item__bar-track">
          <div class="skill-item__bar-fill" style="width: ${percentage}%"></div>
        </div>
        <span class="skill-item__count text-metric">${formatNumber(skill.demand_count)}</span>
      </div>
      
      <div class="skill-item__actions">
        <a href="perfil.html" class="btn btn--secondary btn--sm">Agregar a mi perfil</a>
      </div>
    `;

    fragment.appendChild(item);
  });

  listContainer.appendChild(fragment);

  // Re-inicializamos iconos de Lucide (si se agregaran íconos dinámicamente)
  if (window.lucide) {
    window.lucide.createIcons();
  }
}

document.addEventListener("DOMContentLoaded", initHabilidadesPage);
