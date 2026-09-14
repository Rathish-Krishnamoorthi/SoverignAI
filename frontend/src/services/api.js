import axios from "axios";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://127.0.0.1:8001/api" });
api.interceptors.request.use((config) => {
  const token = window.localStorage.getItem("sovereign_x_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
export const login = (username, password) => {
  const body = new URLSearchParams({ username, password });
  return api.post("/auth/token", body, { headers: { "Content-Type": "application/x-www-form-urlencoded" } });
};
export const getSystemStatus = () => api.get("/status");
export const getCurrentUser = () => api.get("/auth/me");
export const listAdminUsers = () => api.get("/admin/users");
export const createAdminUser = (payload) => api.post("/admin/users", payload);
export const updateAdminUser = (id, payload) => api.patch(`/admin/users/${id}`, payload);
export const resetAdminPassword = (id, password) => api.post(`/admin/users/${id}/reset-password`, { password });
export const deleteAdminUser = (id) => api.delete(`/admin/users/${id}`);
export const getAdminAudit = () => api.get("/admin/audit");
export const getAdminStatus = () => api.get("/admin/status");
export const getAdminSecurity = () => api.get("/admin/security");
export const updateAdminSecurity = (payload) => api.put("/admin/security", payload);
export const uploadDocument = (file) => {
  const data = new FormData();
  data.append("file", file);
  return api.post("/upload", data);
};
export const analyzeDocument = (id) => api.post(`/analyze/${id}`);
export const getSovereignty = () => api.get("/sovereignty");
export const getLlmStatus = () => api.get("/llm/status");
export const getLlmModels = () => api.get("/llm/models");
export const toggleLlmModule = (capability, enabled) => api.post(`/llm/modules/${capability}/toggle`, null, { params: { enabled } });
export const setLlmModuleModel = (capability, model) => api.post(`/llm/modules/${capability}/model`, null, { params: { model } });
export const generateApproval = (id) => api.post(`/approval/${id}`);
export const submitReview = (id, action) => api.post(`/review/${id}`, { action });
export const getAudit = (id) => api.get(`/audit/${id}`);
export const getDocumentLogs = (id) => api.get(`/logs/${id}`);
export const listDocuments = () => api.get("/documents");
export const deleteDocument = (id) => api.delete(`/documents/${id}`);
export const inspectDocument = (id) => api.get(`/documents/${id}/inspection`);
export const downloadDocument = (id) => api.get(`/documents/${id}/download`, { responseType: "blob" });
export const listSops = () => api.get("/sops");
export const uploadSop = (formData) => api.post("/sops", formData);
export const searchSops = (query) => api.post("/sops/search", { query });
export const transitionSop = (id, action) => api.post(`/sops/${id}/${action}`);
