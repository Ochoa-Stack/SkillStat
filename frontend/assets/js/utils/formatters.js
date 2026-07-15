const numberFormatter = new Intl.NumberFormat("es-MX");

function formatNumber(value) {
  return numberFormatter.format(value);
}

const currencyFormatter = new Intl.NumberFormat("es-MX", {
  style: "currency",
  currency: "MXN",
  maximumFractionDigits: 0,
});

function formatCurrency(value) {
  return currencyFormatter.format(value);
}

function renderMarketMetrics(summary, selectors) {
  document.querySelector(selectors.activeJobs).textContent = formatNumber(
    summary.total_jobs,
  );
  document.querySelector(selectors.activeJobsDetail).textContent =
    "Tecnología · México";
  document.querySelector(selectors.activeCompanies).textContent = formatNumber(
    summary.total_companies,
  );
  document.querySelector(selectors.activeCompaniesDetail).textContent =
    "Empresas únicas registradas";
  document.querySelector(selectors.skillsTracked).textContent = formatNumber(
    summary.total_skills_tracked,
  );
  document.querySelector(selectors.skillsTrackedDetail).textContent =
    "Catalogadas y actualizadas a diario";
}

function escapeHtml(str) {
  if (str === null || str === undefined) return "";
  const div = document.createElement("div");
  div.textContent = String(str);
  return div.innerHTML;
}
