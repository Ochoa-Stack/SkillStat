async function createAlert(skillId, thresholdValue) {
  return apiPost("/alerts/", {
    skill_id: skillId,
    threshold_value: thresholdValue,
  });
}

async function listAlerts() {
  return apiGet("/alerts/");
}

async function deleteAlert(alertId) {
  return apiDelete(`/alerts/${alertId}`);
}
