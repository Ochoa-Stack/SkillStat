let currentPage = 1;
const perPage = 10;
// Id del admin autenticado; se carga en initAdminUsuariosPage y se usa en renderUsers para deshabilitar los controles de la propia fila del actor.
let currentAdminId = null;

function showRowError(spanEl, message) {
  spanEl.textContent = message;
  spanEl.hidden = false;
  setTimeout(() => {
    spanEl.hidden = true;
    spanEl.textContent = "";
  }, 4000);
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

    const isSelf = user.id === currentAdminId;
    const selfTitle = isSelf
      ? ' title="No puedes modificar tu propia cuenta"'
      : "";
    const disabledAttr = isSelf ? " disabled" : "";

    const nombreSeguro = escapeHtml(nombre);
    const emailSeguro = escapeHtml(user.email || "—");

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td data-label="ID">${user.id}</td>
      <td data-label="Nombre completo">${nombreSeguro}</td>
      <td data-label="Correo">${emailSeguro}</td>
      <td data-label="Rol">
        <select
          class="admin-role-select"
          data-user-id="${user.id}"
          data-user-name="${nombreSeguro}"
          aria-label="Rol de ${nombreSeguro}"
          ${disabledAttr}${selfTitle}
        >
          <option value="REGISTERED"${user.role === "REGISTERED" ? " selected" : ""}>Registered</option>
          <option value="ADMIN"${user.role === "ADMIN" ? " selected" : ""}>Admin</option>
        </select>
      </td>
      <td data-label="Activo">
        <label class="admin-status-label"${selfTitle}>
          <input
            type="checkbox"
            class="admin-status-checkbox"
            data-user-id="${user.id}"
            data-user-name="${nombreSeguro}"
            ${user.is_active !== false ? "checked" : ""}
            ${disabledAttr}
            aria-label="Estado activo de ${nombreSeguro}"
          />
          <span class="admin-status-text">${user.is_active !== false ? "Activo" : "Inactivo"}</span>
        </label>
      </td>
      <td data-label="Registrado el">${fecha}</td>
      <td data-label="">
        <span class="form-error admin-row-error" hidden></span>
      </td>
    `;
    tbody.appendChild(tr);

    // Listeners de mutación, aplica solo para filas que no son el propio admin
    if (!isSelf) {
      const roleSelect = tr.querySelector(".admin-role-select");
      const statusCheckbox = tr.querySelector(".admin-status-checkbox");
      const errorSpan = tr.querySelector(".admin-row-error");

      roleSelect.addEventListener("change", async () => {
        const newRole = roleSelect.value;
        const previousRole = newRole === "ADMIN" ? "REGISTERED" : "ADMIN";
        const confirmed = window.confirm(
          `¿Cambiar el rol de ${nombre} a ${newRole === "ADMIN" ? "Admin" : "Registered"}?`,
        );
        if (!confirmed) {
          roleSelect.value = previousRole;
          return;
        }
        roleSelect.disabled = true;
        try {
          await updateUserRole(user.id, newRole);
        } catch (err) {
          roleSelect.value = previousRole;
          showRowError(errorSpan, err.message);
        } finally {
          roleSelect.disabled = false;
        }
      });

      statusCheckbox.addEventListener("change", async () => {
        const newStatus = statusCheckbox.checked;
        const statusLabel = tr.querySelector(".admin-status-text");
        const confirmed = window.confirm(
          `¿${newStatus ? "Activar" : "Desactivar"} la cuenta de ${nombre}?`,
        );
        if (!confirmed) {
          statusCheckbox.checked = !newStatus;
          return;
        }
        statusCheckbox.disabled = true;
        try {
          await updateUserStatus(user.id, newStatus);
          statusLabel.textContent = newStatus ? "Activo" : "Inactivo";
        } catch (err) {
          statusCheckbox.checked = !newStatus;
          statusLabel.textContent = !newStatus ? "Activo" : "Inactivo";
          showRowError(errorSpan, err.message);
        } finally {
          statusCheckbox.disabled = false;
        }
      });
    }
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
    // Obtenemos el usuario actual con el mismo patrón que navbar-role.js para saber el id del admin logueado y deshabilitar su propia fila.
    const [me, data] = await Promise.all([
      apiGet("/auth/me"),
      listUsers(1, perPage),
    ]);
    currentAdminId = me.id;

    document.getElementById("admin-loading").style.display = "none";
    document.getElementById("admin-main").hidden = false;

    renderUsers(data);
    bindControls();
  } catch (error) {
    if (error.status === 401) {
      window.location.href = "/views/register.html";
    } else if (error.status === 403) {
      // Sesión válida pero sin rol ADMIN que redirige silenciosamente sin mensaje
      window.location.href = "/views/panorama.html";
    } else {
      console.error("Error cargando usuarios:", error);
      document.getElementById("admin-loading").innerHTML =
        `<p class="form-error">No se pudieron cargar los usuarios.</p>`;
    }
  }
}

document.addEventListener("DOMContentLoaded", initAdminUsuariosPage);
