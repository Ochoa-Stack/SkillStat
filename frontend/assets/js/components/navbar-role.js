(function () {
  async function injectAdminLink() {
    let user;
    try {
      user = await apiGet("/auth/me");
    } catch {
      // Si /auth/me falla (401, red, lo que sea), simplemente no se inyecta el link. Cada página ya maneja su propio guard de sesión por separado; este script solo decide visibilidad.
      return;
    }
    if (user.role !== "ADMIN") return;
    if (window.location.pathname.includes("/views/admin/")) return;
    const navbarList = document.querySelector(".navbar__links");
    const drawerList = document.querySelector(".nav-drawer__links");
    if (navbarList) {
      const li = document.createElement("li");
      li.innerHTML =
        '<a href="admin/respaldos.html" class="navbar__link">Admin</a>';
      navbarList.appendChild(li);
    }
    if (drawerList) {
      const li = document.createElement("li");
      li.innerHTML =
        '<a href="admin/respaldos.html" class="nav-drawer__link">Admin</a>';
      drawerList.appendChild(li);
    }
  }
  document.addEventListener("DOMContentLoaded", injectAdminLink);
})();
