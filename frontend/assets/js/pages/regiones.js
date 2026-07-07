// Construimos las barras con divs
function renderRegionsChart(container, distribution) {
  const unmappedContainer = document.querySelector("[data-regions-unmapped]");

  if (!distribution || distribution.length === 0) {
    container.innerHTML =
      '<p class="text-body-sm" style="width:100%; text-align:center;">No hay datos disponibles</p>';
    if (unmappedContainer) unmappedContainer.style.display = "none";
    return;
  }

  // Filtramos el caso base que no tiene ubicación geográfica específica (Nacional)
  const nationalData = distribution.find((item) => item.is_fallback === true);
  const competitiveData = distribution.filter(
    (item) => item.is_fallback !== true,
  );

  container.innerHTML = "";

  if (competitiveData.length > 0) {
    const maxDemand = Math.max(
      ...competitiveData.map((item) => item.demand_count),
    );

    competitiveData.forEach((item) => {
      const heightPercent = (item.demand_count / maxDemand) * 100;

      const column = document.createElement("div");
      column.className = "regions-chart__column";

      const value = document.createElement("span");
      value.className = "regions-chart__value text-label";
      value.textContent = item.demand_count;

      const bar = document.createElement("div");
      bar.className =
        item.demand_count === maxDemand
          ? "regions-chart__bar regions-chart__bar--top"
          : "regions-chart__bar";
      bar.style.height = `${heightPercent}%`;
      bar.setAttribute("aria-hidden", "true");

      const label = document.createElement("span");
      label.className = "regions-chart__label text-label";
      label.textContent = item.state;

      column.append(value, bar, label);
      container.appendChild(column);
    });
  } else {
    container.innerHTML =
      '<p class="text-body-sm" style="width:100%; text-align:center;">No hay datos regionales específicos</p>';
  }

  if (unmappedContainer) {
    if (nationalData && nationalData.demand_count > 0) {
      unmappedContainer.textContent = `* Adicionalmente existen ${nationalData.demand_count} vacantes sin ubicación geográfica específica a nivel estatal.`;
      unmappedContainer.style.display = "block";
    } else {
      unmappedContainer.style.display = "none";
    }
  }
}

async function initRegionesPage() {
  const chartContainer = document.querySelector("[data-regions-chart]");

  try {
    const geoResponse = await getGeoDistribution("state");
    renderRegionsChart(chartContainer, geoResponse.distribution);
  } catch (error) {
    console.error("No se pudieron cargar los datos de regiones:", error);
    if (chartContainer) {
      chartContainer.innerHTML =
        '<p class="text-body-sm" style="width:100%; text-align:center;">No disponible</p>';
    }
  }
}

document.addEventListener("DOMContentLoaded", initRegionesPage);
