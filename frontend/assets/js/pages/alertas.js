// Catálogo cargado una sola vez por sesión de página, reutilizado para resolver skill_id => nombre en la tabla
let skillCatalog = [];

function showInlineMessage(msgElement, text, isSuccess) {
  msgElement.textContent = text;
  msgElement.hidden = false;
  if (isSuccess) {
    msgElement.style.color = "var(--color-accent-green)";
    msgElement.style.borderColor = "var(--color-accent-green)";
    msgElement.style.backgroundColor = "rgba(16, 185, 129, 0.1)";
  } else {
    msgElement.style.color = "";
    msgElement.style.borderColor = "";
    msgElement.style.backgroundColor = "";
  }
}

function getSkillName(skillId) {
  const skill = skillCatalog.find((s) => s.id === skillId);
  return skill ? skill.name : `Skill #${skillId}`;
}

function renderAlerts(alerts) {
  const tbody = document.getElementById("alertas-tbody");
  const empty = document.getElementById("alertas-empty");
  const wrapper = document.getElementById("alertas-table-wrapper");

  if (!alerts || alerts.length === 0) {
    wrapper.hidden = true;
    empty.hidden = false;
    return;
  }

  empty.hidden = true;
  wrapper.hidden = false;
  tbody.innerHTML = "";

  alerts.forEach((alert) => {
    const skillName = getSkillName(alert.skill_id);
    const createdAt = alert.created_at
      ? new Date(alert.created_at).toLocaleDateString("es-ES", {
          day: "2-digit",
          month: "2-digit",
          year: "numeric",
        })
      : "—";

    const thresholdLabel =
      alert.alert_type === "TREND"
        ? `≥ ${alert.threshold_percentage}% de crecimiento`
        : `≥ ${alert.threshold_value} vacantes`;

    const skillNameSeguro = escapeHtml(skillName);

    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td data-label="Habilidad">${skillNameSeguro}</td>
      <td data-label="Umbral">${thresholdLabel}</td>
      <td data-label="Creada el">${createdAt}</td>
      <td data-label="">
        <button
          class="btn btn--ghost btn--sm"
          type="button"
          data-action="delete-alert"
          data-id="${alert.id}"
          aria-label="Eliminar alerta para ${skillNameSeguro}"
        >
          <i data-lucide="trash-2" style="width:14px;height:14px;"></i>
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });

  if (window.lucide && window.lucide.createIcons) {
    window.lucide.createIcons();
  }

  tbody.querySelectorAll('[data-action="delete-alert"]').forEach((btn) => {
    btn.addEventListener("click", () => handleDeleteAlert(btn.dataset.id, btn));
  });
}

async function handleDeleteAlert(alertId, btnElement) {
  btnElement.disabled = true;
  try {
    await deleteAlert(alertId);
    await loadAlerts();
  } catch (error) {
    console.error("Error eliminando alerta:", error);
    btnElement.disabled = false;
  }
}

async function loadAlerts() {
  const alerts = await listAlerts();
  renderAlerts(alerts);
}

function validateCreateForm(form) {
  const skillId = parseInt(form.skill_id.value);
  const alertType = form.alert_type.value;
  if (!(skillId > 0)) return false;
  if (alertType === "ABSOLUTE") {
    const thresholdValue = parseInt(form.threshold_value.value);
    return Number.isInteger(thresholdValue) && thresholdValue > 0;
  }
  if (alertType === "TREND") {
    const thresholdPercentage = parseFloat(form.threshold_percentage.value);
    return !isNaN(thresholdPercentage) && thresholdPercentage > 0;
  }
  return false;
}

function bindCreateForm() {
  const form = document.getElementById("crear-alerta-form");
  const btn = document.getElementById("btn-crear-alerta");
  const msg = document.getElementById("crear-alerta-msg");

  function toggleThresholdFields(form) {
    const alertType = form.alert_type.value;
    const valueGroup = document.getElementById("threshold-value-group");
    const percentageGroup = document.getElementById(
      "threshold-percentage-group",
    );
    if (alertType === "ABSOLUTE") {
      valueGroup.hidden = false;
      percentageGroup.hidden = true;
      form.threshold_percentage.value = "";
    } else {
      valueGroup.hidden = true;
      percentageGroup.hidden = false;
      form.threshold_value.value = "";
    }
  }

  // Deshabilita el botón en tiempo real para que el usuario tenga feedback inmediato de validez del formulario antes de intentar enviarlo
  function updateSubmitState() {
    btn.disabled = !validateCreateForm(form);
  }

  form.skill_id.addEventListener("change", updateSubmitState);
  form.threshold_value.addEventListener("input", updateSubmitState);
  form.threshold_percentage.addEventListener("input", updateSubmitState);

  form.querySelectorAll('input[name="alert_type"]').forEach((radio) => {
    radio.addEventListener("change", () => {
      toggleThresholdFields(form);
      updateSubmitState();
    });
  });

  updateSubmitState();

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const skillId = parseInt(form.skill_id.value);
    const alertType = form.alert_type.value;
    const thresholdValue =
      alertType === "ABSOLUTE" ? parseInt(form.threshold_value.value) : null;
    const thresholdPercentage =
      alertType === "TREND"
        ? parseFloat(form.threshold_percentage.value)
        : null;

    const originalText = btn.textContent;
    btn.textContent = "Creando...";
    btn.disabled = true;
    msg.hidden = true;

    try {
      await createAlert(
        skillId,
        alertType,
        thresholdValue,
        thresholdPercentage,
      );
      showInlineMessage(msg, "Alerta creada correctamente.", true);
      form.reset();
      updateSubmitState();
      await loadAlerts();
    } catch (error) {
      showInlineMessage(msg, error.message, false);
      btn.disabled = false;
    } finally {
      btn.textContent = originalText;
    }
  });
}

function populateSkillSelect(skills) {
  const select = document.getElementById("alert-skill-select");
  select.innerHTML = '<option value="">Selecciona una habilidad</option>';
  skills.forEach((skill) => {
    const option = document.createElement("option");
    option.value = skill.id;
    option.textContent = skill.name;
    select.appendChild(option);
  });
}

async function initAlertasPage() {
  try {
    const [catalogData, alerts] = await Promise.all([
      getCatalogs(),
      listAlerts(),
    ]);

    skillCatalog = catalogData.skills || [];
    populateSkillSelect(skillCatalog);
    renderAlerts(alerts);

    document.getElementById("alertas-loading").style.display = "none";
    document.getElementById("alertas-main").hidden = false;

    bindCreateForm();
  } catch (error) {
    if (error.status === 401) {
      saveGuestIntent(window.location.pathname, null);
      window.location.href = "/views/register.html";
    } else {
      console.error("Error cargando alertas:", error);
      document.getElementById("alertas-loading").innerHTML =
        `<p class="form-error">No se pudieron cargar las alertas.</p>`;
    }
  }
}

document.addEventListener("DOMContentLoaded", initAlertasPage);
