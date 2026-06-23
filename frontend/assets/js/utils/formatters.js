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
