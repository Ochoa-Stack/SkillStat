async function listBackups(page = 1, perPage = 10) {
  return apiGet(`/admin/backups?page=${page}&per_page=${perPage}`);
}

async function createBackup() {
  return apiPost("/admin/backup", {});
}

async function listUsers(page = 1, perPage = 10) {
  return apiGet(`/admin/users?page=${page}&per_page=${perPage}`);
}
