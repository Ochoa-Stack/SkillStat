let currentPage = 1;
const perPage = 10;

function showInlineMessage(msgElement, text, isSuccess) {
  msgElement.textContent = text;
  msgElement.hidden = false;
  if (isSuccess) {
    msgElement.style.color = "var(--color-accent-green)";
    msgElement.style.borderColor = "var(--color-accent-green)";
    msgElement.style.backgroundColor = "rgba(33, 166, 117, 0.1)";
  } else {
    msgElement.style.color = "";
    msgElement.style.borderColor = "";
    msgElement.style.backgroundColor = "";
  }
}

function formatStatus(status) {
  if (status === "COMPLETED") {
    return `<span style="color: var(--color-accent-green); font-weight: 500;">Completado</span>`;
  }
  if (status === "FAILED") {
    return `<span style="color: var(--color-semantic-error); font-weight: 500;">Fallido</span>`;
  }
  // PENDING u otro valor desconocido
  return `<span style="color: var(--color-text-secondary);">${status}</span>`;
}

function renderBackups(data) {
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

  items.forEach((backup) => {
    const fecha = backup.created_at
      ? new Date(backup.created_at).toLocaleDateString("es-ES", {
          day: "2-digit",
          month: "2-digit",
          year: "numeric",
        })
      : "—";

    const filenameSeguro = escapeHtml(backup.filename || "—");
    const userEmailSeguro = escapeHtml(
      backup.user_email || `Usuario #${backup.user_id}`,
    );

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td data-label="ID">${backup.id}</td>
      <td data-label="Archivo">${filenameSeguro}</td>
      <td data-label="Estado">${formatStatus(backup.status)}</td>
      <td data-label="Generado por">${userEmailSeguro}</td>
      <td data-label="Fecha">${fecha}</td>
      <td data-label="Acciones">
        ${
          backup.status === "COMPLETED"
            ? `<button class="btn btn--ghost btn--sm" data-action="restore-backup" data-id="${backup.id}" data-filename="${escapeHtml(backup.filename)}">Restaurar</button>`
            : ""
        }
      </td>
    `;
    tbody.appendChild(tr);
  });

  tbody.querySelectorAll('[data-action="restore-backup"]').forEach((btn) => {
    btn.addEventListener("click", () =>
      openRestoreDialog(btn.dataset.id, btn.dataset.filename),
    );
  });
}

async function loadPage(page) {
  currentPage = page;
  const data = await listBackups(currentPage, perPage);
  renderBackups(data);
}

async function handleGenerarRespaldo() {
  const btn = document.getElementById("btn-generar-respaldo");
  const msg = document.getElementById("admin-action-msg");

  const originalText = btn.textContent;
  btn.textContent = "Generando...";
  btn.disabled = true;
  msg.hidden = true;

  try {
    await createBackup();
    showInlineMessage(msg, "Respaldo generado correctamente.", true);
    // Recarga la página actual para que el nuevo backup aparezca
    await loadPage(currentPage);
  } catch (error) {
    showInlineMessage(
      msg,
      error.message || "No se pudo generar el respaldo.",
      false,
    );
  } finally {
    btn.textContent = originalText;
    btn.disabled = false;
  }
}

function openRestoreDialog(backupId, filename) {
  const dialog = document.getElementById("restore-confirm-dialog");
  const filenameEl = document.getElementById("restore-dialog-filename");
  const input = document.getElementById("restore-confirm-input");
  const confirmBtn = document.getElementById("restore-dialog-confirm");
  const msg = document.getElementById("restore-dialog-msg");

  filenameEl.textContent = filename;
  input.value = "";
  confirmBtn.disabled = true;
  msg.hidden = true;
  dialog.dataset.backupId = backupId;
  dialog.dataset.filename = filename;

  input.oninput = () => {
    confirmBtn.disabled = input.value !== filename;
  };

  dialog.showModal();
}

async function handleConfirmRestore() {
  const dialog = document.getElementById("restore-confirm-dialog");
  const confirmBtn = document.getElementById("restore-dialog-confirm");
  const msg = document.getElementById("restore-dialog-msg");
  const backupId = dialog.dataset.backupId;
  const filename = dialog.dataset.filename;

  const originalText = confirmBtn.textContent;
  confirmBtn.textContent = "Restaurando...";
  confirmBtn.disabled = true;
  msg.hidden = true;

  try {
    const result = await restoreBackup(backupId, filename);
    dialog.close();
    showInlineMessage(
      document.getElementById("admin-action-msg"),
      `Restauración completada. Se generó un respaldo de seguridad: ${result.safety_backup}.`,
      true,
    );
    await loadPage(currentPage);
  } catch (error) {
    msg.textContent = error.message || "No se pudo completar la restauración.";
    msg.hidden = false;
    confirmBtn.disabled = false;
  } finally {
    confirmBtn.textContent = originalText;
  }
}

function bindControls() {
  document
    .getElementById("btn-generar-respaldo")
    .addEventListener("click", handleGenerarRespaldo);

  document.getElementById("admin-btn-prev").addEventListener("click", () => {
    if (currentPage > 1) loadPage(currentPage - 1);
  });

  document.getElementById("admin-btn-next").addEventListener("click", () => {
    loadPage(currentPage + 1);
  });

  document
    .getElementById("restore-dialog-cancel")
    .addEventListener("click", () => {
      document.getElementById("restore-confirm-dialog").close();
    });
  document
    .getElementById("restore-dialog-confirm")
    .addEventListener("click", handleConfirmRestore);
}

async function initAdminRespaldosPage() {
  try {
    const data = await listBackups(1, perPage);

    document.getElementById("admin-loading").style.display = "none";
    document.getElementById("admin-main").hidden = false;

    renderBackups(data);
    bindControls();
  } catch (error) {
    if (error.status === 401) {
      window.location.href = "../register.html";
    } else if (error.status === 403) {
      // Sesión válida pero sin rol ADMIN: redirige silenciosamente sin mensaje
      window.location.href = "../panorama.html";
    } else {
      console.error("Error cargando respaldos:", error);
      document.getElementById("admin-loading").innerHTML =
        `<p class="form-error">No se pudieron cargar los respaldos.</p>`;
    }
  }
}

document.addEventListener("DOMContentLoaded", initAdminRespaldosPage);
