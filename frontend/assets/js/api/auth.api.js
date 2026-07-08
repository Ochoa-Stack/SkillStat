async function registerUser(payload) {
  return apiPost("/auth/register", payload);
}

async function loginUser(credentials) {
  return apiPost("/auth/login", credentials);
}

async function verifyEmailToken(token) {
  return apiGet(`/auth/verify-email?token=${encodeURIComponent(token)}`);
}

async function confirmEmailVerification(token) {
  return apiPost("/auth/verify-email", { token });
}

async function resendVerificationEmail(email) {
  return apiPost("/auth/resend-verification", { email });
}

async function requestPasswordReset(email) {
  return apiPost("/auth/forgot-password", { email });
}

async function resetPassword(token, newPassword) {
  return apiPost("/auth/reset-password", { token, new_password: newPassword });
}