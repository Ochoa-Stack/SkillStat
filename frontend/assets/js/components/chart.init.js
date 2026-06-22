// Construimos las barras con divs en vez de una libreria de graficas, porque los colores deben reaccionar al cambio de tema via CSS, y una grafica en canvas no se actualiza sola cuando el usuario cambia el tema.
function renderSkillsChart(container, skills) {
  const maxDemand = Math.max(...skills.map((skill) => skill.demand_count));

  container.innerHTML = '';

  skills.forEach((skill, index) => {
    const heightPercent = (skill.demand_count / maxDemand) * 100;

    const column = document.createElement('div');
    column.className = 'skills-chart__column';

    const value = document.createElement('span');
    value.className = 'skills-chart__value text-label';
    value.textContent = skill.demand_count;

    const bar = document.createElement('div');
    bar.className =
      index === 0 ? 'skills-chart__bar skills-chart__bar--top' : 'skills-chart__bar';
    bar.style.height = `${heightPercent}%`;
    bar.setAttribute('aria-hidden', 'true');

    const label = document.createElement('span');
    label.className = 'skills-chart__label text-label';
    label.textContent = skill.name;

    column.append(value, bar, label);
    container.appendChild(column);
  });
}
