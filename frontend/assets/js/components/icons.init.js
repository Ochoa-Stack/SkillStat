// Inicializa los iconos de Lucide. Debe ejecutarse despues de que el script de Lucide cargue y antes de que cualquier otro script dependa de que los iconos ya esten renderizados en el DOM.
document.addEventListener("DOMContentLoaded", function () {
  if (typeof lucide !== "undefined") {
    lucide.createIcons();
  }
});
