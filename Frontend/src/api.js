const API_BASE = 'http://localhost:8000';

function getToken() {
  return localStorage.getItem('token');
}

function authHeaders() {
  const token = getToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiGet(path) {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { ...authHeaders() },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || `Error ${res.status}`);
  }
  return res.json();
}

export async function apiPost(path, data) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(data),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json.detail || `Error ${res.status}`);
  return json;
}

export async function apiPut(path, data) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(data),
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json.detail || `Error ${res.status}`);
  return json;
}

export async function apiUpload(path, file) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { ...authHeaders() },
    body: formData,
  });
  const json = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(json.detail || `Error ${res.status}`);
  return json;
}

export function avatarUrl(path) {
  return path ? `${API_BASE}${path}` : null;
}
