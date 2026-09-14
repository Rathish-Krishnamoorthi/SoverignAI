import React, { useEffect, useState } from "react";
import {
  analyzeDocument, createAdminUser, deleteAdminUser, deleteDocument, generateApproval,   getAdminAudit, getAdminSecurity, getAdminStatus, getAudit, getDocumentLogs, getLlmStatus, getSovereignty, getCurrentUser, getSystemStatus, inspectDocument, listAdminUsers, listDocuments, listSops, login, resetAdminPassword, searchSops, setLlmModuleModel, submitReview, toggleLlmModule, transitionSop, updateAdminSecurity, updateAdminUser, uploadDocument, uploadSop,
} from "./services/api";
const demoFileName = "Inspection_Report.pdf";
const modules = [
  ["overview", "Overview", "◈"],
  ["document", "Document Intake", "▣"],
  ["sops", "SOP Library", "§"],
  ["pipeline", "Processing Pipeline", "⇢"],
  ["finding", "Engineering Finding", "◆"],
  ["verification", "Verification", "✓"],
  ["review", "Engineer Review", "▤"],
  ["audit", "Audit Timeline", "◷"],
];
const adminModules = [
  ["admin-overview", "Overview", "◈"],
  ["admin-access", "Access Control", "◆"],
  ["admin-documents", "Documents", "▣"],
  ["admin-sop", "SOP Governance", "§"],
  ["admin-audit", "Audit Logs", "◷"],
  ["admin-status", "System Status", "▣"],
  ["admin-security", "Security Configuration", "⚿"],
];

function Header({ sovereignty, demo, user, sidebarOpen, onToggleSidebar, onLogout }) {
  const isAdmin = (user?.roles || []).includes("ADMIN");
  return <header className="topbar"><div className="brand-lockup"><button className={`menu-toggle ${sidebarOpen ? "is-open" : ""}`} type="button" aria-label={sidebarOpen ? "Hide workspace modules" : "Show workspace modules"} aria-expanded={sidebarOpen} onClick={onToggleSidebar}><span /><span /><span /></button><div><div className="eyebrow">SOVEREIGN ENGINEERING INTELLIGENCE</div><h1>SOVEREIGN-X</h1><p>Evidence-backed refinery document decisions</p></div></div><div className="status-pill"><span className="pulse" /> {demo ? "DEMO MODE" : sovereignty?.system || "LOCAL / OFFLINE"}<small>{isAdmin ? "Current admin · ADMIN" : `${user?.sub} · ${(user?.roles || []).join(", ")}`}</small><button className="ghost" type="button" onClick={onLogout}>Sign out</button></div></header>;
}

function Sidebar({ active, setActive, result, file, open, onClose, user }) {
  const visibleModules = (user?.roles || []).includes("ADMIN") ? adminModules : modules;
  return <><div className={`sidebar-backdrop ${open ? "visible" : ""}`} onClick={onClose} aria-hidden="true" /><aside className={`sidebar ${open ? "open" : "closed"}`} aria-label="Workspace modules"><div className="sidebar-head"><div className="sidebar-label">WORKSPACE MODULES</div><button className="sidebar-close" type="button" aria-label="Hide workspace modules" onClick={onClose}>×</button></div>{visibleModules.map(([id, label, icon], index) => <button className={`nav-item ${active === id ? "selected" : ""}`} key={id} onClick={() => { setActive(id); onClose(); }}><span className="nav-index">0{index + 1}</span><span className="nav-icon">{icon}</span><span>{label}</span>{id === "document" && file && <i className="nav-dot" />}{id === "finding" && result && <i className="nav-dot" />}</button>)}<div className="sidebar-footer"><span className="pulse" /> LOCAL WORKSPACE<small>No cloud data egress</small></div></aside></>;
}

function ModuleTitle({ number, eyebrow, title, description }) {
  return <div className="module-title"><div className="eyebrow">{number} / {eyebrow}</div><h2>{title}</h2>{description && <p className="muted">{description}</p>}</div>;
}

function Login({ onAuthenticated, onDemo }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const submit = async (event) => {
    event.preventDefault();
    try {
      const { data } = await login(email, password);
      window.localStorage.setItem("sovereign_x_token", data.access_token);
      onAuthenticated(data.user);
    } catch (err) {
      setError(err.response?.data?.detail || "Sign-in failed.");
    }
  };
  return <main className="auth-shell"><section className="card auth-card"><div className="eyebrow">LOCAL IDENTITY GATE</div><h1>SOVEREIGN-X</h1><p className="muted">Sign in to the on-premise engineering workspace.</p><form onSubmit={submit}><label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required autoComplete="username" /></label><label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required autoComplete="current-password" /></label><button className="primary" type="submit">Sign in locally</button></form>{error && <div className="error">{error}</div>}<button className="secondary" type="button" onClick={onDemo}>Continue in demo mode</button><small className="muted">Authentication and data remain inside this installation.</small></section></main>;
}

function SopLibrary({ sops, onRefresh }) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [message, setMessage] = useState("");
  const search = async (event) => {
    event.preventDefault();
    if (!query.trim()) return;
    try { setResults((await searchSops(query.trim())).data); setMessage(""); } catch (err) { setMessage(err.response?.data?.detail || "SOP search failed."); }
  };
  const upload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    const data = new FormData();
    data.append("file", file); data.append("sop_id", `SOP-${Date.now()}`); data.append("version", "1.0"); data.append("title", file.name);
    try { await uploadSop(data); setMessage("SOP uploaded locally and is awaiting review."); onRefresh(); } catch (err) { setMessage(err.response?.data?.detail || "SOP upload failed."); }
  };
  const action = async (sop, name) => { try { await transitionSop(sop.id, name); onRefresh(); } catch (err) { setMessage(err.response?.data?.detail || "Workflow action failed."); } };
  return <div className="stack"><section className="card"><ModuleTitle number="03" eyebrow="CONTROLLED KNOWLEDGE" title="SOP Library" description="Approved local procedures for grounded operational answers." /><div className="actions"><label className="secondary">Upload local SOP<input type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" hidden onChange={upload} /></label><form className="sop-search" onSubmit={search}><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search approved procedures" /><button className="primary">Search SOPs</button></form></div>{message && <div className="error">{message}</div>}</section><section className="card">{sops.length === 0 && <p className="muted">No SOPs uploaded. Add a local PDF or DOCX to begin the approval workflow.</p>}{sops.map((sop) => <div className="document-row" key={sop.id}><div><b>{sop.sop_id} · {sop.title}</b><small>Version {sop.version} · {sop.plant || "Plant not set"} · {sop.unit || "Unit not set"}</small><span className={`doc-status ${sop.status.toLowerCase()}`}>{sop.status}</span></div><div className="document-actions">{sop.status === "UPLOADED" && <button className="secondary" onClick={() => action(sop, "submit-review")}>Submit review</button>}{sop.status === "UNDER_REVIEW" && <button className="secondary" onClick={() => action(sop, "approve")}>Approve</button>}{sop.status === "APPROVED" && <button className="secondary" onClick={() => action(sop, "activate")}>Activate</button>}</div></div>)}</section>{results.length > 0 && <section className="card"><div className="eyebrow">AUTHORIZED SEARCH RESULTS</div>{results.map((item) => <div className="evidence-panel" key={item.chunk?.id}><b>{item.sop.sop_id} v{item.sop.version}</b><small>Page {item.chunk?.page_number}</small><p>{item.chunk?.content}</p></div>)}</section>}</div>;
}

function SovereigntyDashboard({ data, llm, onToggleModel, onChangeModel, isAdmin }) {
  const items = [["Internet Calls", data?.internet_calls ?? 0], ["Cloud API Calls", data?.cloud_api_calls ?? 0], ["Data Egress", data?.data_egress ?? 0], ["External AI APIs", data?.external_ai_apis ?? 0]];
  const models = llm?.configured_models || [];
  const installedModels = llm?.models || [];
  return <section className="card sovereignty"><div className="section-heading"><span className="icon">◈</span><div><div className="eyebrow">TRUST & EXECUTION</div><h3>Sovereignty Status</h3></div><span className="badge good">● SOVEREIGN / OFFLINE</span></div><div className="metric-grid">{items.map(([label, value]) => <div className="metric" key={label}><b>{value}</b><span>{label}</span></div>)}</div><div className="local-grid">{[["OCR", data?.ocr], ["Embeddings", data?.embeddings], ["Vector DB", data?.vector_db], ["LLM", data?.llm]].map(([label, value]) => <div key={label}><span>{label}</span><b>{value || "LOCAL"}</b></div>)}</div>{isAdmin && <><div className="model-banner"><span>◉</span><div><b>LOCAL AI MODEL STATUS</b><small>Choose any installed Ollama model for each route · live state refreshes every 3 seconds</small></div></div>{models.length > 0 && <div className="model-list">{models.map((model) => { const selectedModel = installedModels.includes(model.name) ? model.name : ""; return <div className={`model-row model-${model.state}`} key={model.capability}><span><b>{model.capability.replace("_", " ")}</b><small>{model.description}</small><small className="model-route">{model.name}</small></span><span className="model-controls"><select className="model-select" aria-label={`Model for ${model.capability}`} value={selectedModel} onChange={(event) => onChangeModel(model, event.target.value)}><option value="" disabled>{installedModels.length ? "Select installed model" : "No local models found"}</option>{installedModels.map((name) => <option value={name} key={name}>{name}</option>)}</select><button className={`model-toggle ${model.enabled ? "enabled" : ""}`} type="button" disabled={!model.available && !model.enabled} onClick={() => onToggleModel(model)}>{model.enabled ? "ON" : "OFF"}</button><span className={`badge ${model.state === "active" || model.state === "working" ? "good" : ""}`}>{model.state === "working" ? "◉ WORKING" : model.state === "active" ? "● ACTIVE" : model.state === "inactive" ? "○ INACTIVE" : "○ UNAVAILABLE"}</span></span></div>; })}</div>}</>}</section>;
}

function UploadPanel({ file, setFile, onAnalyze, loading, error, onDemo }) {
  const selectedType = file?.type || "";
  const supportedPattern = /\.(pdf|png|jpe?g|webp|bmp|tiff?|docx|txt|md|csv|json)$/i;
  const looksSupported = file && supportedPattern.test(file.name);
  return <section className="card upload-card"><div className="eyebrow">LOCAL-ONLY SOURCE</div><h3>Confidential Engineering Document</h3><p className="muted">PDF, DOCX, TXT, Markdown, CSV, JSON, PNG, JPG, TIFF, WEBP, or BMP. Files remain on this machine.</p><label className="dropzone"><input type="file" accept=".pdf,.docx,.txt,.md,.csv,.json,.png,.jpg,.jpeg,.webp,.bmp,.tif,.tiff,application/pdf,image/*,text/plain,text/markdown,text/csv,application/json" onChange={(event) => setFile(event.target.files?.[0])} /><span className="upload-icon">↑</span><b>{file ? file.name : "Drop inspection report here"}</b><small>{file ? "Document ready for local extraction" : "or select a document from this device"}</small></label>{file && <div className="file-row"><span>▣</span><b>{file.name}</b><span className="uploaded">Ready ✓</span></div>}{file && !looksSupported && <div className="error">Unsupported document extension. Select a PDF, office document, text file, structured data file, or image.</div>}<div className="actions"><button className="primary" disabled={!looksSupported || loading} onClick={onAnalyze}>{loading ? "Processing locally…" : "Analyze Report →"}</button><button className="secondary" onClick={onDemo}>Run Demo Mode</button></div>{error && <div className="error">{error}</div>}</section>;
}

function DocumentLibrary({ documents, selectedId, onSelect, onDelete, inspection, onInspect }) {
  return <div className="document-library"><div className="library-heading"><div><div className="eyebrow">LOCAL DOCUMENT STORE</div><h3>Saved Documents</h3></div><span className="badge">{documents.length} saved</span></div>{documents.length === 0 && <p className="muted">No documents saved yet. Each upload receives its own local folder and record.</p>}{documents.map((document) => <div className={`document-row ${selectedId === document.document_id ? "selected" : ""}`} key={document.document_id} onClick={() => onSelect(document)}><div><b>{document.filename}</b><small>{new Date(document.uploaded_at).toLocaleString()} · {Math.round(document.size_bytes / 1024)} KB</small><span className={`doc-status ${document.extraction_status}`}>{document.extraction_status}</span></div><div className="document-actions"><button className="secondary" onClick={(event) => { event.stopPropagation(); onInspect(document.document_id); }}>Inspect</button><button className="ghost" onClick={(event) => { event.stopPropagation(); onDelete(document.document_id); }}>Remove</button></div></div>)}{inspection && <div className={`inspection-report ${inspection.ocr_status}`}><div className="eyebrow">EXTRACTION DIAGNOSTICS</div><h4>{inspection.ocr_status === "success" ? "Document readable" : "Document could not be fully extracted"}</h4>{inspection.issues.map((issue) => <p className="error-line" key={issue}>Reason: {issue}</p>)}{inspection.extracted_fields && Object.keys(inspection.extracted_fields).length > 0 && <div className="extracted-fields">{Object.entries(inspection.extracted_fields).map(([key, value]) => <span key={key}><b>{key.replaceAll("_", " ")}</b>{String(value)}</span>)}</div>}<small>Recommended format: {inspection.recommended_format}</small></div>}</div>;
}

function Pipeline({ stages }) {
  const names = stages || ["OCR", "Evidence Extraction", "SOP Retrieval", "Qwen2-VL", "Python Verification", "Evidence Chain"];
  return <section className="card"><ModuleTitle number="03" eyebrow="TRACEABLE PROCESSING" title="Processing Pipeline" description="Every stage is visible and independently traceable." /><div className="pipeline vertical-pipeline">{names.map((stage, index) => { const item = typeof stage === "string" ? { stage, status: "complete" } : stage; return <div className={`pipeline-step ${item.status === "complete" ? "complete" : ""}`} key={item.stage}><span>{item.status === "complete" ? "✓" : "○"}</span><div><b>{item.stage}</b><small>{index === 3 ? `${item.provider || "local"} model · ${item.execution || "LOCAL"}` : "Completed locally"}</small></div></div>; })}</div></section>;
}

function Finding({ result }) {
  const evidence = result.finding;
  return <section className="card hero-card"><div className="finding-head"><div><div className="eyebrow">F-001 · SOURCE-BACKED CLAIM</div><h2>{result.ai_analysis.finding}</h2><p className="muted">{result.ai_analysis.reasoning_summary}</p></div><div className="chips"><span className="chip danger">{result.ai_analysis.severity}</span><span className="chip">{result.ai_analysis.confidence} CONFIDENCE</span></div></div><div className="evidence-panel single-evidence"><div className="eyebrow">INSPECTION EVIDENCE</div><h3>{evidence.document}</h3><p>Page {evidence.page} · {evidence.photo} · {evidence.equipment}</p><strong>Pit depth: {evidence.measurement} {evidence.unit}</strong><small>Source trace: document / page / photo</small></div></section>;
}

function Verification({ result }) {
  const sop = result.sop_evidence;
  return <div className="stack"><section className="card"><ModuleTitle number="05" eyebrow="RETRIEVED KNOWLEDGE" title="Applicable SOP Evidence" /><div className="evidence-panel single-evidence"><div className="eyebrow">SYNTHETIC DEMO SOP</div><h3>{sop.document}</h3><p>Section {sop.section} · Page {sop.page}</p><strong>Permitted limit: {sop.limit} {sop.unit}</strong><small>{sop.text}</small></div></section><section className="card verified-card"><ModuleTitle number="06" eyebrow="DETERMINISTIC CHECK" title="Python Verification" description="The LLM is not trusted as the authoritative calculator." /><div className="calculation">{result.calculation.measured} mm <span>{result.calculation.operator}</span> {result.calculation.limit} mm</div><div className="verified-text">✓ {result.calculation.status.replace("_", " ")}</div><p>Verified independently by {result.calculation.verified_by}</p></section><section className="card"><ModuleTitle number="07" eyebrow="LOCAL REASONING" title="Qwen2.5-VL Analysis" /><div className="ai-detail"><b>{result.ai_analysis.recommendation}</b><span>Model: {result.ai_analysis.model}</span><span>Runtime: Ollama · Execution: {result.processing_mode}</span></div></section></div>;
}

function Review({ documentId, recommendation, onGenerate, generated, onReview }) {
  return <section className="card review-module"><ModuleTitle number="08" eyebrow="HUMAN DECISION" title="Engineer Review" description="The engineer remains the final decision maker." /><div className="recommendation"><div className="eyebrow">AI RECOMMENDATION</div><h3>{recommendation}</h3><small>AI-generated draft. Engineer review required.</small></div><div className="actions"><button className="primary" onClick={() => onReview("accepted")}>Accept Recommendation</button><button className="secondary" onClick={() => onReview("review_requested")}>Request Review</button><button className="ghost" onClick={() => onReview("rejected")}>Reject</button><button className="download" onClick={onGenerate}>{generated ? "Approval_Note.docx Ready ✓" : "Generate Approval Note ↓"}</button></div></section>;
}

function AuditTimeline({ events, logs }) {
  return <section className="card"><ModuleTitle number="09" eyebrow="LOCAL AUDIT" title="Audit Timeline" description="Workflow events and persistent OCR/analysis diagnostics." /><div className="timeline">{(events || []).map((event, index) => <div className="timeline-row" key={`${event.action}-${index}`}><span className="timeline-dot" /><div><b>{event.action.replaceAll("_", " ")}</b><small>{new Date(event.timestamp).toLocaleString()} · {event.execution}</small></div></div>)}</div><div className="log-panel"><div className="eyebrow">DIAGNOSTIC LOG</div><p className="muted">Full log file: <code>{logs?.log_file || "backend/logs/sovereign-x.log"}</code></p>{logs?.entries?.length ? <pre>{logs.entries.join("\n")}</pre> : <p className="muted">No diagnostic entries for this document yet.</p>}</div></section>;
}

function EmptyModule({ title }) {
  return <section className="card empty-module"><div className="empty-icon">◌</div><h2>{title}</h2><p>Complete Document Intake to populate this module with traceable engineering data.</p></section>;
}

function AdminAccessControl({ user }) {
  const [users, setUsers] = useState([]);
  const [roles, setRoles] = useState([]);
  const [permissions, setPermissions] = useState({});
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("ENGINEER");
  const [message, setMessage] = useState("");
  const refresh = () => listAdminUsers().then(({ data }) => { setUsers(data.users); setRoles(data.roles); setPermissions(data.permissions || {}); }).catch((err) => setMessage(err.response?.data?.detail || "Could not load local users."));
  useEffect(() => { refresh(); }, []);
  const submit = async (event) => {
    event.preventDefault();
    try { await createAdminUser({ email, password, roles: [role] }); setEmail(""); setPassword(""); setMessage("User created with the selected role."); refresh(); } catch (err) { setMessage(err.response?.data?.detail || "Could not create user."); }
  };
  const changeRole = async (item, nextRole) => { try { await updateAdminUser(item.id, { roles: [nextRole] }); setMessage("Role updated."); refresh(); } catch (err) { setMessage(err.response?.data?.detail || "Could not update role."); } };
  const toggleAccount = async (item) => { if (!window.confirm(`${item.is_active ? "Disable" : "Enable"} ${item.username}?`)) return; try { await updateAdminUser(item.id, { is_active: !item.is_active }); setMessage("Account status updated."); refresh(); } catch (err) { setMessage(err.response?.data?.detail || "Could not update account."); } };
  const resetPassword = async (item) => { const next = window.prompt(`Enter a temporary password for ${item.username}:`); if (!next) return; try { await resetAdminPassword(item.id, next); setMessage("Temporary password reset."); } catch (err) { setMessage(err.response?.data?.detail || "Could not reset password."); } };
  const deleteAccount = async (item) => { if (!window.confirm(`Permanently delete ${item.username}? This cannot be undone.`)) return; try { await deleteAdminUser(item.id); setMessage("Account deleted."); refresh(); } catch (err) { setMessage(err.response?.data?.detail || "Could not delete account."); } };
  return <section className="stack"><section className="card"><ModuleTitle number="01" eyebrow="ADMINISTRATION" title="Access Control" description="Manage local identities, roles, permissions, and account status." /><div className="metric-grid"><div className="metric"><b>ACTIVE</b><span>Current admin active</span></div><div className="metric"><b>{users.length}</b><span>Local users</span></div><div className="metric"><b>{roles.length}</b><span>Supported roles</span></div></div><form className="admin-user-form" onSubmit={submit}><label>Email<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="employee@plant.local" required /></label><label>Temporary password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} minLength="8" required /></label><label>Role<select value={role} onChange={(event) => setRole(event.target.value)}>{roles.map((name) => <option value={name} key={name}>{name}</option>)}</select></label><button className="primary" type="submit">Create local account</button></form>{message && <div className="error">{message}</div>}</section><section className="card"><div className="eyebrow">LOCAL USERS</div><div className="admin-table-head"><span>USER</span><span>ROLE</span><span>STATUS</span><span>CREATED</span><span>ACTIONS</span></div>{users.map((item) => <div className="admin-user-row" key={item.id}><div><b>{item.username}</b><small>{item.last_activity ? `Last activity ${item.last_activity}` : "Last activity not recorded"}</small></div><select value={item.roles[0] || ""} onChange={(event) => changeRole(item, event.target.value)}>{roles.map((name) => <option value={name} key={name}>{name}</option>)}</select><span className={`badge ${item.is_active ? "good" : "danger"}`}>{item.is_active ? "ACTIVE" : "DISABLED"}</span><small>{new Date(item.created_at).toLocaleDateString()}</small><div className="admin-actions"><button className="ghost" onClick={() => resetPassword(item)}>Reset password</button><button className="ghost" onClick={() => toggleAccount(item)}>{item.is_active ? "Disable" : "Enable"}</button><button className="ghost danger-action" onClick={() => deleteAccount(item)}>Delete</button></div></div>)}</section><section className="card"><div className="eyebrow">ROLE & PERMISSIONS</div>{roles.map((name) => <div className="permission-row" key={name}><b>{name}</b><span>{permissions[name]?.length ? permissions[name].join(", ") : "No permissions assigned in the local store."}</span></div>)}</section></section>;
}

function AdminOverview({ users, sops, status, audit }) {
  const activeUsers = users.filter((item) => item.is_active).length;
  const services = [["API", status?.api], ["DATABASE", status?.database], ["STORAGE", status?.storage], ["LOCAL LLM", status?.llm]];
  return <section className="stack"><ModuleTitle number="00" eyebrow="ADMINISTRATION" title="Sovereign-X System Control" description="A compact governance view for local identities, controlled procedures, and platform health." /><section className="card"><div className="eyebrow">SYSTEM STATUS</div><div className="status-grid">{services.map(([label, value]) => <div className="status-row" key={label}><span>{label}</span><b className={value?.status === "ok" || value?.available ? "online" : "offline"}>● {value?.status === "ok" || value?.available ? "ONLINE" : "OFFLINE"}</b></div>)}<div className="status-row"><span>AIR-GAPPED MODE</span><b className="online">● {status?.air_gapped_mode ? "ENABLED" : "DISABLED"}</b></div></div></section><section className="card"><div className="eyebrow">ADMINISTRATIVE SUMMARY</div><div className="metric-grid"><div className="metric"><b>{users.length}</b><span>Local users</span></div><div className="metric"><b>{activeUsers}</b><span>Active users</span></div><div className="metric"><b>{sops.length}</b><span>Tracked SOPs</span></div><div className="metric"><b>{audit.length}</b><span>Audit events</span></div></div></section><section className="card"><div className="eyebrow">RECENT ADMIN ACTIVITY</div>{audit.slice(0, 5).map((event, index) => <div className="document-row" key={`${event.timestamp}-${index}`}><div><b>{event.action}</b><small>{event.resource} · {event.user}</small></div><span className="badge good">{event.status}</span></div>)}{audit.length === 0 && <p className="muted">No administrative activity recorded in this session.</p>}</section></section>;
}

function AdminSopGovernance({ sops, onRefresh }) {
  const [message, setMessage] = useState("");
  const action = async (sop, name) => { try { await transitionSop(sop.id, name); setMessage(`${name} completed for ${sop.sop_id}.`); onRefresh(); } catch (err) { setMessage(err.response?.data?.detail || "SOP governance action failed."); } };
  return <section className="stack"><ModuleTitle number="02" eyebrow="GOVERNANCE" title="SOP Governance" description="Review controlled procedure metadata and lifecycle state. This view is not for operational SOP consumption." />{message && <div className="error">{message}</div>}<section className="card">{sops.map((sop) => <div className="admin-sop-row" key={sop.id}><div><b>{sop.sop_id} · {sop.title}</b><small>v{sop.version} · {sop.department || "Department not set"} · {sop.unit || "Unit not set"}</small></div><span className="badge">{sop.status}</span><div className="admin-actions">{sop.status === "UPLOADED" && <button className="ghost" onClick={() => action(sop, "submit-review")}>Submit review</button>}{sop.status === "UNDER_REVIEW" && <button className="ghost" onClick={() => action(sop, "approve")}>Approve</button>}{sop.status === "APPROVED" && <button className="ghost" onClick={() => action(sop, "activate")}>Activate</button>}{["ACTIVE", "SUPERSEDED"].includes(sop.status) && <button className="ghost" onClick={() => action(sop, "archive")}>Archive</button>}</div></div>)}{sops.length === 0 && <p className="muted">No SOP records are available.</p>}</section></section>;
}

function AdminDocuments({ documents, onRefresh }) {
  const [query, setQuery] = useState("");
  const [message, setMessage] = useState("");
  const visible = documents.filter((document) => document.filename.toLowerCase().includes(query.toLowerCase()));
  const upload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    try { await uploadDocument(file); setMessage("Document stored locally."); onRefresh(); }
    catch (err) { setMessage(err.response?.data?.detail || "Document upload failed."); }
  };
  const remove = async (id) => {
    if (!window.confirm("Delete this local document and its processed data?")) return;
    try { await deleteDocument(id); setMessage("Document deleted locally."); onRefresh(); }
    catch (err) { setMessage(err.response?.data?.detail || "Document deletion failed."); }
  };
  return <section className="stack"><section className="card"><ModuleTitle number="02" eyebrow="LOCAL DOCUMENT CONTROL" title="Document Management" description="Administrator-only document metadata, processing, download, and deletion controls." /><div className="actions"><label className="secondary">Upload document<input type="file" hidden onChange={upload} /></label><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search filename" /></div>{message && <div className="error">{message}</div>}</section><section className="card">{visible.map((document) => <div className="document-row" key={document.document_id}><div><b>{document.filename}</b><small>{document.document_id} · {document.extraction_status} · {Math.round(document.size_bytes / 1024)} KB</small></div><div className="document-actions"><button className="ghost" onClick={() => inspectDocument(document.document_id).then(() => setMessage("Inspection completed locally.")).catch((err) => setMessage(err.response?.data?.detail || "Inspection failed."))}>Inspect</button><button className="ghost danger-action" onClick={() => remove(document.document_id)}>Delete</button></div></div>)}{visible.length === 0 && <p className="muted">No local documents match the search.</p>}</section></section>;
}

function AdminAuditLogs({ audit }) {
  const [query, setQuery] = useState("");
  const filtered = audit.filter((event) => `${event.action} ${event.user} ${event.resource} ${event.status}`.toLowerCase().includes(query.toLowerCase()));
  return <section className="stack"><ModuleTitle number="03" eyebrow="GOVERNANCE" title="Audit Logs" description="Read-only administrative and security activity from local services." /><section className="card"><input className="admin-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search action, user, or resource" />{filtered.map((event, index) => <div className="audit-admin-row" key={`${event.timestamp}-${index}`}><small>{event.timestamp ? new Date(event.timestamp).toLocaleString() : "Unknown time"}</small><b>{event.action}</b><span>{event.user}</span><span>{event.resource}</span><span className="badge good">{event.status}</span><small>{event.details}</small></div>)}{filtered.length === 0 && <p className="muted">No matching audit events.</p>}</section></section>;
}

function AdminStatus({ status }) {
  const entries = [["API", status?.api], ["DATABASE", status?.database], ["OBJECT STORAGE", status?.storage], ["VECTOR DATABASE", status?.vector_database], ["LOCAL LLM", status?.llm], ["OCR SERVICE", status?.ocr], ["AUTHENTICATION", status?.authentication]];
  return <section className="stack"><ModuleTitle number="04" eyebrow="LOCAL INFRASTRUCTURE" title="System Status" description="Live health reported by the local backend services." /><section className="card status-grid">{entries.map(([label, value]) => <div className="status-row" key={label}><span>{label}</span><div><b className={value?.status === "ok" || value?.available ? "online" : "offline"}>● {value?.status === "ok" || value?.available ? "ONLINE" : "OFFLINE"}</b>{value?.error && <small>{value.error}</small>}</div></div>)}<div className="status-row"><span>AIR-GAPPED MODE</span><b className="online">● {status?.air_gapped_mode ? "ENABLED" : "DISABLED"}</b></div></section></section>;
}

function AdminSecurity({ security }) {
  const [draft, setDraft] = useState(null);
  const [message, setMessage] = useState("");
  useEffect(() => { if (security) setDraft({ air_gapped_mode: security.air_gapped_mode, audit_logging: security.audit_logging, session_timeout_hours: security.session_timeout_hours, password_minimum_length: security.password_minimum_length }); }, [security]);
  if (!draft) return <section className="card"><p className="muted">Loading security configuration.</p></section>;
  const save = async (event) => { event.preventDefault(); try { const { data } = await updateAdminSecurity(draft); setDraft({ air_gapped_mode: data.air_gapped_mode, audit_logging: data.audit_logging, session_timeout_hours: data.session_timeout_hours, password_minimum_length: data.password_minimum_length }); setMessage("Security configuration saved locally."); } catch (err) { setMessage(err.response?.data?.detail || "Could not save security configuration."); } };
  return <section className="stack"><ModuleTitle number="05" eyebrow="SECURITY" title="Security Configuration" description="Change supported local controls. Secrets and credentials are never returned." /><form className="card security-form" onSubmit={save}><label>AIR-GAPPED MODE<select value={String(draft.air_gapped_mode)} onChange={(event) => setDraft({ ...draft, air_gapped_mode: event.target.value === "true" })}><option value="true">ENABLED</option><option value="false">DISABLED</option></select></label><label>AUDIT LOGGING<select value={String(draft.audit_logging)} onChange={(event) => setDraft({ ...draft, audit_logging: event.target.value === "true" })}><option value="true">ENABLED</option><option value="false">DISABLED</option></select></label><label>SESSION TIMEOUT (HOURS)<input type="number" min="1" max="24" value={draft.session_timeout_hours} onChange={(event) => setDraft({ ...draft, session_timeout_hours: Number(event.target.value) })} /></label><label>PASSWORD MINIMUM LENGTH<input type="number" min="8" max="128" value={draft.password_minimum_length} onChange={(event) => setDraft({ ...draft, password_minimum_length: Number(event.target.value) })} /></label><button className="primary" type="submit">Save security configuration</button>{message && <div className="error">{message}</div>}<small className="muted">Local identity store is enabled. Sensitive secrets remain hidden.</small></form></section>;
}

function AdminPanel({ user, active, users, rolesData, sops, documents, onRefreshSops, onRefreshDocuments, status, security, audit }) {
  if (active === "admin-overview") return <AdminOverview users={users} sops={sops} status={status} audit={audit} />;
  if (active === "admin-access") return <AdminAccessControl user={user} />;
  if (active === "admin-documents") return <AdminDocuments documents={documents} onRefresh={onRefreshDocuments} />;
  if (active === "admin-sop") return <AdminSopGovernance sops={sops} onRefresh={onRefreshSops} />;
  if (active === "admin-audit") return <AdminAuditLogs audit={audit} />;
  if (active === "admin-status") return <AdminStatus status={status} />;
  return <AdminSecurity security={security} />;
}

export default function App() {
  const [user, setUser] = useState(null);
  const [authReady, setAuthReady] = useState(false);
  const [active, setActive] = useState("overview");
  const [sidebarOpen, setSidebarOpen] = useState(() => window.innerWidth > 900);
  const [file, setFile] = useState(null);
  const [documentId, setDocumentId] = useState(null);
  const [result, setResult] = useState(null);
  const [events, setEvents] = useState([]);
  const [sovereignty, setSovereignty] = useState(null);
  const [llm, setLlm] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [generated, setGenerated] = useState(false);
  const [documents, setDocuments] = useState([]);
  const [inspection, setInspection] = useState(null);
  const [logs, setLogs] = useState(null);
  const [sops, setSops] = useState([]);
  const [adminUsers, setAdminUsers] = useState([]);
  const [adminStatus, setAdminStatus] = useState(null);
  const [adminSecurity, setAdminSecurity] = useState(null);
  const [adminAudit, setAdminAudit] = useState([]);

  useEffect(() => {
    const token = window.localStorage.getItem("sovereign_x_token");
    if (token) {
      getCurrentUser().then(({ data }) => { setUser(data.user); setActive(data.user.roles.includes("ADMIN") ? "admin-overview" : "overview"); }).catch(() => window.localStorage.removeItem("sovereign_x_token")).finally(() => setAuthReady(true));
      return;
    }

    getSystemStatus().then(({ data }) => {
      if (data?.processing_mode === "DEMO") {
        const demoUser = { sub: "demo", roles: ["ADMIN"] };
        setUser(demoUser);
        setActive("admin-overview");
      }
    }).catch(() => {}).finally(() => setAuthReady(true));
  }, []);

  useEffect(() => {
    if (!authReady || !user) return undefined;
    let mounted = true;
    const refresh = () => Promise.all([getSovereignty(), getLlmStatus(), listDocuments(), listSops(), ...(user.roles.includes("ADMIN") ? [listAdminUsers(), getAdminStatus(), getAdminSecurity(), getAdminAudit()] : [])]).then((responses) => {
      const [s, l, docs, sopResponse, users, status, security, audit] = responses;
      if (mounted) { setSovereignty(s.data); setLlm(l.data); setDocuments(docs.data); setSops(sopResponse.data); if (users) setAdminUsers(users.data.users); if (status) setAdminStatus(status.data); if (security) setAdminSecurity(security.data); if (audit) setAdminAudit(audit.data); }
    }).catch(() => { if (mounted) setError("Backend unavailable. Start FastAPI on port 8001."); });
    refresh();
    const timer = window.setInterval(() => { getLlmStatus().then(({ data }) => { if (mounted) setLlm(data); }).catch(() => {}); }, 3000);
    return () => { mounted = false; window.clearInterval(timer); };
  }, [authReady, user]);
  if (!authReady) return <main className="auth-shell"><section className="card auth-card"><h1>Loading local identity…</h1></section></main>;
  if (!user) return <Login onAuthenticated={(next) => { setUser(next); setActive(next.roles.includes("ADMIN") ? "admin-overview" : "overview"); }} onDemo={() => { setUser({ sub: "demo", roles: ["ADMIN"] }); setActive("admin-overview"); }} />;
  const toggleModel = async (model) => {
    try { const { data } = await toggleLlmModule(model.capability, !model.enabled); setLlm((current) => ({ ...current, routes: current.routes?.map((route) => route.capability === data.route.capability ? data.route : route), configured_models: current.configured_models?.map((route) => route.capability === data.route.capability ? data.route : route) })); } catch (err) { setError(err.response?.data?.detail || "Could not update the model route."); }
  };
  const changeModel = async (model, name) => {
    try {
      const { data } = await setLlmModuleModel(model.capability, name);
      setLlm((current) => ({ ...current, routes: current.routes?.map((route) => route.capability === data.route.capability ? data.route : route), configured_models: current.configured_models?.map((route) => route.capability === data.route.capability ? data.route : route) }));
    } catch (err) { setError(err.response?.data?.detail || "Could not change the model route."); }
  };
  const analyze = async (selectedFile = file) => {
    setError(""); setLoading(true);
    try { const upload = await uploadDocument(selectedFile); setDocumentId(upload.data.document_id); setDocuments((await listDocuments()).data); const analyzed = await analyzeDocument(upload.data.document_id); setResult(analyzed.data); setEvents((await getAudit(upload.data.document_id)).data); setLogs((await getDocumentLogs(upload.data.document_id)).data); setDocuments((await listDocuments()).data); setActive("finding"); } catch (err) { const failedId = err.config?.url?.match(/analyze\/([^/]+)/)?.[1]; if (failedId) setLogs((await getDocumentLogs(failedId)).data); setError(err.response?.data?.detail || "Analysis failed. Open Audit Timeline for diagnostics."); setDocuments((await listDocuments()).data); } finally { setLoading(false); }
  };
  const runDemo = async () => { const demo = new File(["SOVEREIGN-X synthetic engineering demonstration"], demoFileName, { type: "application/pdf" }); setFile(demo); await analyze(demo); };
  const inspect = async (id) => { setError(""); try { setInspection((await inspectDocument(id)).data); setLogs((await getDocumentLogs(id)).data); } catch (err) { setError(err.response?.data?.detail || "Document inspection failed."); } };
  const selectDocument = async (document) => { setDocumentId(document.document_id); setFile(new File([], document.filename)); setInspection(null); try { setLogs((await getDocumentLogs(document.document_id)).data); } catch { setLogs(null); } };
  const removeDocument = async (id) => { if (!window.confirm("Remove this document and its generated outputs?")) return; try { await deleteDocument(id); setDocuments((await listDocuments()).data);   if (id === documentId) { setDocumentId(null); setResult(null); setEvents([]); setLogs(null); setFile(null); setInspection(null); } } catch (err) { setError(err.response?.data?.detail || "Document removal failed."); } };
  const review = async (action) => { if (documentId) { await submitReview(documentId, action); setEvents((await getAudit(documentId)).data); setActive("audit"); } };
  const approval = async () => { if (documentId) { await generateApproval(documentId); setGenerated(true); setEvents((await getAudit(documentId)).data); setActive("audit"); } };
  const refreshSops = async () => { try { setSops((await listSops()).data); } catch (err) { setError(err.response?.data?.detail || "Could not refresh SOP library."); } };
  const refreshDocuments = async () => { try { setDocuments((await listDocuments()).data); } catch (err) { setError(err.response?.data?.detail || "Could not refresh documents."); } };

  const renderModule = () => {
    if (active === "overview") return <><ModuleTitle number="01" eyebrow="COMMAND CENTER" title="Sovereignty Overview" description="A local control surface for confidential engineering analysis." /><SovereigntyDashboard data={sovereignty} llm={llm} isAdmin={(user?.roles || []).includes("ADMIN")} onToggleModel={toggleModel} onChangeModel={changeModel} /><div className="card principle"><div className="eyebrow">DESIGN PRINCIPLE</div><h3>Evidence over assertion.</h3><p>The document provides evidence. RAG provides the applicable SOP. Qwen2.5-VL provides contextual reasoning. Python verifies numerical claims. The engineer makes the final decision.</p></div></>;
    if (active === "document") return <><ModuleTitle number="02" eyebrow="SOURCE DOCUMENT" title="Document Intake" description="Upload, inspect, analyze, and remove each confidential document independently." /><UploadPanel file={file} setFile={setFile} onAnalyze={() => analyze()} loading={loading} error={error} onDemo={runDemo} /><DocumentLibrary documents={documents} selectedId={documentId} onSelect={selectDocument} onDelete={removeDocument} inspection={inspection} onInspect={inspect} /></>;
    if (active === "sops") return <><SopLibrary sops={sops} onRefresh={refreshSops} /></>;
    if (active.startsWith("admin-")) return <AdminPanel user={user} active={active} users={adminUsers} sops={sops} documents={documents} onRefreshSops={refreshSops} onRefreshDocuments={refreshDocuments} status={adminStatus} security={adminSecurity} audit={adminAudit} />;
    if (!result && ["pipeline", "finding", "verification", "review", "audit"].includes(active)) return <><ModuleTitle number="03" eyebrow="WORKFLOW" title={modules.find(([id]) => id === active)?.[1]} /><EmptyModule title="Module awaiting analysis" /></>;
    if (active === "pipeline") return <Pipeline stages={result.pipeline} />;
    if (active === "finding") return <><ModuleTitle number="04" eyebrow="ENGINEERING FINDING" title="Evidence Chain" description="The primary traceability view for the identified finding." /><Finding result={result} /></>;
    if (active === "verification") return <Verification result={result} />;
    if (active === "review") return <Review documentId={documentId} recommendation={result.ai_analysis.recommendation} onGenerate={approval} generated={generated} onReview={review} />;
    return <AuditTimeline events={events} logs={logs} />;
  };

  return <main><Header sovereignty={sovereignty} demo={result?.processing_mode === "DEMO"} user={user} sidebarOpen={sidebarOpen} onToggleSidebar={() => setSidebarOpen((open) => !open)} onLogout={() => { window.localStorage.removeItem("sovereign_x_token"); setUser(null); setActive("overview"); }} /><div className={`workspace ${sidebarOpen ? "sidebar-visible" : "sidebar-hidden"}`}><Sidebar active={active} setActive={setActive} result={result} file={file} user={user} open={sidebarOpen} onClose={() => setSidebarOpen(false)} /><div className="module-content">{renderModule()}</div></div></main>;
}
