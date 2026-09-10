import axios from "axios";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL || "http://localhost:8001/api" });
export const uploadDocument = (file) => {
  const data = new FormData();
  data.append("file", file);
  return api.post("/upload", data);
};
export const analyzeDocument = (id) => api.post(`/analyze/${id}`);
export const getSovereignty = () => api.get("/sovereignty");
export const getLlmStatus = () => api.get("/llm/status");
export const generateApproval = (id) => api.post(`/approval/${id}`);
export const submitReview = (id, action) => api.post(`/review/${id}`, { action });
export const getAudit = (id) => api.get(`/audit/${id}`);
export const getDocumentLogs = (id) => api.get(`/logs/${id}`);
export const listDocuments = () => api.get("/documents");
export const deleteDocument = (id) => api.delete(`/documents/${id}`);
export const inspectDocument = (id) => api.get(`/documents/${id}/inspection`);
