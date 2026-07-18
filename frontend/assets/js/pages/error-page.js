document.addEventListener("DOMContentLoaded", () => {
  const urlParams = new URLSearchParams(window.location.search);
  const from = urlParams.get("from");
  const backLink = document.getElementById("error-back-link");

  if (backLink) {
    if (from === "admin") {
      backLink.href = "../admin/respaldos.html";
    } else if (from === "index") {
      backLink.href = "../index.html";
    } else {
      backLink.href = "../panorama.html";
    }
  }
});
