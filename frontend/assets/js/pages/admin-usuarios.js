let currentPage = 1;
const perPage = 10;

function formatRole(role) {
  if (role === "ADMIN") {
    return `<span style="color: var(--color-accent-orange); font-weight: 500;">Admin</span>`;
  }
  // REGISTERED u otro valor
  return `<span style="color: var(--color-text-secondary);">${role}</span>`;
}

function renderUsers(data) {
  const tbody = document.getElementById("admin-tbody");
  const empty = document.getElementById("admin-empty");
  const wrapper = document.getElementById("admin-table-wrapper");
  const pageInfo = document.getElementById("admin-page-info");
  const btnPrev = document.getElementById("admin-btn-prev");
  const btnNext = document.getElementById("admin-btn-next");

  const { items, total_pages } = data;

  // Actualizar controles de paginación
  pageInfo.textContent = `Página ${data.page} de ${total_pages || 0}`;
  btnPrev.disabled = data.page <= 1;
  btnNext.disabled = data.page >= total_pages || total_pages === 0;

  if (!items || items.length === 0) {
    wrapper.hidden = true;
    empty.hidden = false;
    return;
  }

  empty.hidden = true;
  wrapper.hidden = false;
  tbody.innerHTML = "";

  items.forEach((user) => {
    const nombre =
      [user.first_name, user.last_name].filter(Boolean).join(" ") || "—";
    const fecha = user.created_at
      ? new Date(user.created_at).toLocaleDateString("es-ES", {
          day: "2-digit",
          month: "2-digit",
          year: "numeric",
        })
      : "—";

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td data-label="ID">${user.id}</td>
      <td data-label="Nombre completo">${nombre}</td>
      <td data-label="Correo">${user.email || "—"}</td>
      <td data-label="Rol">${formatRole(user.role)}</td>
      <td data-label="Registrado el">${fecha}</td>
    `;
    tbody.appendChild(tr);
  });
}

async function loadPage(page) {
  currentPage = page;
  const data = await listUsers(currentPage, perPage);
  renderUsers(data);
}

function bindControls() {
  document.getElementById("admin-btn-prev").addEventListener("click", () => {
    if (currentPage > 1) loadPage(currentPage - 1);
  });

  document.getElementById("admin-btn-next").addEventListener("click", () => {
    loadPage(currentPage + 1);
  });
}

async function initAdminUsuariosPage() {
  try {
    const data = await listUsers(1, perPage);

    document.getElementById("admin-loading").style.display = "none";
    document.getElementById("admin-main").hidden = false;

    renderUsers(data);
    bindControls();
  } catch (error) {
    if (error.status === 401) {
      window.location.href = "../register.html";
    } else if (error.status === 403) {
      // Sesión válida pero sin rol ADMIN: redirige silenciosamente sin mensaje
      window.location.href = "../panorama.html";
    } else {
      console.error("Error cargando usuarios:", error);
      document.getElementById("admin-loading").innerHTML =
        `<p class="form-error">No se pudieron cargar los usuarios.</p>`;
    }
  }
}

document.addEventListener("DOMContentLoaded", initAdminUsuariosPage);
