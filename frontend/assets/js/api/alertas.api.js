async function createAlert(
  skillId,
  alertType,
  thresholdValue,
  thresholdPercentage,
) {
  const payload = { skill_id: skillId, alert_type: alertType };
  if (alertType === "ABSOLUTE") {
    payload.threshold_value = thresholdValue;
  } else {
    payload.threshold_percentage = thresholdPercentage;
  }
  return apiPost("/alerts/", payload);
}

async function listAlerts() {
  return apiGet("/alerts/");
}

async function deleteAlert(alertId) {
  return apiDelete(`/alerts/${alertId}`);
}
