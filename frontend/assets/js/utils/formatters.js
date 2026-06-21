const numberFormatter = new Intl.NumberFormat("es-MX");

function formatNumber(value) {
  return numberFormatter.format(value);
}
