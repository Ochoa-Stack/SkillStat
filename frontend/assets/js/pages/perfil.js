// Datos de estado global para comparar si hay cambios en el formulario "Mis datos"
let originalProfileData = {};

const PASSWORD_RULES = {
  length: (value) => value.length >= 8,
  upper: (value) => /[A-Z]/.test(value),
  number: (value) => /\d/.test(value),
  special: (value) => /[^A-Za-z0-9]/.test(value),
};

function updatePasswordChecklist(password) {
  Object.entries(PASSWORD_RULES).forEach(([rule, check]) => {
    const item = document.querySelector(`[data-rule="${rule}"]`);
    if (!item) return;
    item.classList.toggle("is-valid", check(password));
  });
}

function updatePasswordSubmitState() {
  const form = document.getElementById("seguridad-form");
  if (!form) return;

  const password = form.new_password.value;
  const allRulesPass = Object.values(PASSWORD_RULES).every((check) =>
    check(password),
  );
  const passwordsMatch =
    password.length > 0 && password === form.confirm_password.value;

  const btn = document.getElementById("btn-save-password");
  if (btn) {
    btn.disabled = !(allRulesPass && passwordsMatch);
  }
}

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

async function initProfilePage() {
  try {
    const profileData = await apiGet("/profile/me");
    originalProfileData = profileData;

    // Poblar Mis datos
    const form = document.getElementById("datos-form");
    form.first_name.value = profileData.first_name || "";
    form.last_name.value = profileData.last_name || "";
    form.intent.value = profileData.intent || "";

    // Poblar tarjeta contextual
    const emailEl = document.querySelector("[data-profile-email]");
    if (emailEl) emailEl.textContent = profileData.email || "No disponible";

    const roleEl = document.querySelector("[data-profile-role]");
    if (roleEl) {
      const rolesMap = { REGISTERED: "Registrado", ADMIN: "Administrador" };
      roleEl.textContent =
        rolesMap[profileData.role] || profileData.role || "Desconocido";
    }

    const sinceEl = document.querySelector("[data-profile-since]");
    if (sinceEl && profileData.created_at) {
      const date = new Date(profileData.created_at);
      sinceEl.textContent = date.toLocaleDateString("es-ES", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      });
    } else if (sinceEl) {
      sinceEl.textContent = "No disponible";
    }

    // Ocultar loader y mostrar pagina principal
    document.getElementById("profile-loading").style.display = "none";
    document.getElementById("profile-main").hidden = false;

    // Cargar habilidades
    await loadSkills();
  } catch (error) {
    if (error.status === 401) {
      window.location.href = "register.html";
    } else {
      console.error("Error cargando perfil:", error);
      // Fallback
      document.getElementById("profile-loading").innerHTML =
        `<p class="form-error">No se pudo cargar el perfil.</p>`;
    }
  }
}

async function handleDatosSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const btn = document.getElementById("btn-save-datos");
  const msg = document.getElementById("datos-msg");

  const currentData = {
    first_name: form.first_name.value,
    last_name: form.last_name.value,
    intent: form.intent.value || null,
  };

  const changes = {};
  for (const key in currentData) {
    if (currentData[key] !== originalProfileData[key]) {
      changes[key] = currentData[key];
    }
  }

  if (Object.keys(changes).length === 0) {
    showInlineMessage(msg, "No hay cambios que guardar.", true);
    return;
  }

  const originalText = btn.textContent;
  btn.textContent = "Guardando...";
  btn.disabled = true;
  msg.hidden = true;

  try {
    const response = await apiPatch("/profile/me", changes);
    originalProfileData = response; // Actualizar con nueva data (incluye los campos modificados)
    showInlineMessage(msg, "Perfil actualizado correctamente.", true);
  } catch (error) {
    showInlineMessage(msg, error.message, false);
  } finally {
    btn.textContent = originalText;
    btn.disabled = false;
  }
}

async function handlePasswordSubmit(e) {
  e.preventDefault();
  const form = e.target;
  const btn = document.getElementById("btn-save-password");
  const msg = document.getElementById("seguridad-msg");

  const originalText = btn.textContent;
  btn.textContent = "Actualizando...";
  btn.disabled = true;
  msg.hidden = true;

  try {
    await apiPost("/profile/change-password", {
      current_password: form.current_password.value,
      new_password: form.new_password.value,
    });

    showInlineMessage(msg, "Contraseña actualizada. Redirigiendo...", true);

    setTimeout(() => {
      window.location.href = "register.html";
    }, 2000);
  } catch (error) {
    if (error.code === "INVALID_CREDENTIALS") {
      showInlineMessage(msg, "La contraseña actual no es correcta", false);
    } else {
      showInlineMessage(msg, error.message, false);
    }
    btn.disabled = false;
    btn.textContent = originalText;
  }
}

async function loadSkills() {
  try {
    const gapData = await apiGet("/profile/skill-gap");
    renderSkills(gapData.mis_habilidades, gapData.brechas);
  } catch (error) {
    console.error("Error cargando habilidades:", error);
  }
}

function renderSkills(misHabilidades, brechas) {
  const misContainer = document.getElementById("mis-habilidades-container");
  const misEmpty = document.getElementById("mis-habilidades-empty");
  const brechasContainer = document.getElementById("brechas-container");
  const brechasEmpty = document.getElementById("brechas-empty");

  misContainer.innerHTML = "";
  brechasContainer.innerHTML = "";

  if (misHabilidades.length === 0) {
    misEmpty.hidden = false;
  } else {
    misEmpty.hidden = true;
    misHabilidades.forEach((skill) => {
      const chip = document.createElement("div");
      chip.className = "chip";
      chip.innerHTML = `
        ${skill.name}
        <button type="button" aria-label="Eliminar ${skill.name}" data-action="remove-skill" data-id="${skill.skill_id}">
          <i data-lucide="x" style="width:14px; height:14px;"></i>
        </button>
      `;
      misContainer.appendChild(chip);
    });
  }

  if (brechas.length === 0) {
    brechasEmpty.hidden = false;
  } else {
    brechasEmpty.hidden = true;
    brechas.forEach((skill) => {
      const chip = document.createElement("div");
      chip.className = "chip";
      chip.innerHTML = `
        ${skill.name}
        <button type="button" aria-label="Agregar ${skill.name}" data-action="add-skill" data-id="${skill.skill_id}">
          <i data-lucide="plus" style="width:14px; height:14px;"></i>
        </button>
      `;
      brechasContainer.appendChild(chip);
    });
  }

  // Re-inicializar iconos despues de inyectar HTML si lucide existe globalmente
  if (window.lucide && window.lucide.createIcons) {
    window.lucide.createIcons();
  }

  // Bind events for buttons
  misContainer
    .querySelectorAll('[data-action="remove-skill"]')
    .forEach((btn) => {
      btn.addEventListener("click", () =>
        handleRemoveSkill(btn.dataset.id, btn),
      );
    });

  brechasContainer
    .querySelectorAll('[data-action="add-skill"]')
    .forEach((btn) => {
      btn.addEventListener("click", () => handleAddSkill(btn.dataset.id, btn));
    });
}

async function handleAddSkill(skillId, btnElement) {
  btnElement.disabled = true;
  try {
    await apiPost("/profile/skills", { skill_id: parseInt(skillId) });
    await loadSkills();
  } catch (error) {
    console.error("Error agregando habilidad:", error);
    btnElement.disabled = false;
  }
}

async function handleRemoveSkill(skillId, btnElement) {
  btnElement.disabled = true;
  try {
    await apiDelete(`/profile/skills/${skillId}`);
    await loadSkills();
  } catch (error) {
    console.error("Error eliminando habilidad:", error);
    btnElement.disabled = false;
  }
}

function bindNavigation() {
  const tabs = document.querySelectorAll("[data-nav-section]");
  const sections = document.querySelectorAll("[data-section]");

  tabs.forEach((tab) => {
    tab.addEventListener("click", () => {
      // Activar pill
      tabs.forEach((t) => t.classList.remove("pill--active"));
      tab.classList.add("pill--active");

      // Mostrar seccion
      const targetId = `section-${tab.dataset.navSection}`;
      sections.forEach((sec) => {
        sec.hidden = sec.id !== targetId;
      });
    });
  });
}

document.addEventListener("DOMContentLoaded", () => {
  bindNavigation();
  initProfilePage();

  const datosForm = document.getElementById("datos-form");
  if (datosForm) {
    datosForm.addEventListener("submit", handleDatosSubmit);
  }

  const seguridadForm = document.getElementById("seguridad-form");
  if (seguridadForm) {
    seguridadForm.addEventListener("submit", handlePasswordSubmit);
    seguridadForm.new_password.addEventListener("input", () => {
      updatePasswordChecklist(seguridadForm.new_password.value);
      updatePasswordSubmitState();
    });
    seguridadForm.confirm_password.addEventListener(
      "input",
      updatePasswordSubmitState,
    );
  }
});
