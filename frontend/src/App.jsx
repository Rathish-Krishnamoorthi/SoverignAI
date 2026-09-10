import React, { useEffect, useState } from "react";
import {
  analyzeDocument, deleteDocument, generateApproval, getAudit, getDocumentLogs, getLlmStatus, getSovereignty, inspectDocument, listDocuments, submitReview, uploadDocument,
} from "./services/api";

const demoFileName = "Inspection_Report.pdf";
const modules = [
  ["overview", "Overview", "◈"],
  ["document", "Document Intake", "▣"],
  ["pipeline", "Processing Pipeline", "⇢"],
  ["finding", "Engineering Finding", "◆"],
  ["verification", "Verification", "✓"],
  ["review", "Engineer Review", "▤"],
  ["audit", "Audit Timeline", "◷"],
];

function Header({ sovereignty, demo }) {
  return <header className="topbar"><div><div className="eyebrow">SOVEREIGN ENGINEERING INTELLIGENCE</div><h1>SOVEREIGN-X</h1><p>Evidence-backed refinery document decisions</p></div><div className="status-pill"><span className="pulse" /> {demo ? "DEMO MODE" : sovereignty?.system || "LOCAL / OFFLINE"}<small>{demo ? "Synthetic Engineering Data" : "On-premise execution"}</small></div></header>;
}

function Sidebar({ active, setActive, result, file }) {
  return <aside className="sidebar"><div className="sidebar-label">WORKSPACE MODULES</div>{modules.map(([id, label, icon], index) => <button className={`nav-item ${active === id ? "selected" : ""}`} key={id} onClick={() => setActive(id)}><span className="nav-index">0{index + 1}</span><span className="nav-icon">{icon}</span><span>{label}</span>{id === "document" && file && <i className="nav-dot" />}{id === "finding" && result && <i className="nav-dot" />}</button>)}<div className="sidebar-footer"><span className="pulse" /> LOCAL WORKSPACE<small>No cloud data egress</small></div></aside>;
}

function ModuleTitle({ number, eyebrow, title, description }) {
  return <div className="module-title"><div className="eyebrow">{number} / {eyebrow}</div><h2>{title}</h2>{description && <p className="muted">{description}</p>}</div>;
}

function SovereigntyDashboard({ data, llm }) {
  const items = [["Internet Calls", data?.internet_calls ?? 0], ["Cloud API Calls", data?.cloud_api_calls ?? 0], ["Data Egress", data?.data_egress ?? 0], ["External AI APIs", data?.external_ai_apis ?? 0]];
  return <section className="card sovereignty"><div className="section-heading"><span className="icon">◈</span><div><div className="eyebrow">TRUST & EXECUTION</div><h3>Sovereignty Status</h3></div><span className="badge good">● SOVEREIGN / OFFLINE</span></div><div className="metric-grid">{items.map(([label, value]) => <div className="metric" key={label}><b>{value}</b><span>{label}</span></div>)}</div><div className="local-grid">{[["OCR", data?.ocr], ["Embeddings", data?.embeddings], ["Vector DB", data?.vector_db], ["LLM", data?.llm]].map(([label, value]) => <div key={label}><span>{label}</span><b>{value || "LOCAL"}</b></div>)}</div><div className={`model-banner ${llm?.available ? "active" : ""}`}><span>◉</span><div><b>{llm?.model || "qwen2.5vl:3b"} / Ollama</b><small>{llm?.available ? "ACTIVE · local model detected" : "READY FOR LOCAL MODEL · Demo fallback enabled"}</small></div></div></section>;
}

function UploadPanel({ file, setFile, onAnalyze, loading, error, onDemo }) {
  const selectedType = file?.type || "";
  const looksSupported = file && /\.(pdf|png|jpe?g)$/i.test(file.name) && (selectedType === "" || selectedType === "application/pdf" || selectedType.startsWith("image/"));
  return <section className="card upload-card"><div className="eyebrow">LOCAL-ONLY SOURCE</div><h3>Confidential Engineering Document</h3><p className="muted">PDF, PNG, JPG accepted. Files remain on this machine.</p><label className="dropzone"><input type="file" accept=".pdf,.png,.jpg,.jpeg,application/pdf,image/png,image/jpeg" onChange={(event) => setFile(event.target.files?.[0])} /><span className="upload-icon">↑</span><b>{file ? file.name : "Drop inspection report here"}</b><small>{file ? "Document ready for analysis" : "or select a document from this device"}</small></label>{file && <div className="file-row"><span>▣</span><b>{file.name}</b><span className="uploaded">Uploaded ✓</span></div>}{file && !looksSupported && <div className="error">This file is not a supported PDF/image. Select the original PDF or image instead of renaming a text file.</div>}<div className="actions"><button className="primary" disabled={!looksSupported || loading} onClick={onAnalyze}>{loading ? "Processing locally…" : "Analyze Report →"}</button><button className="secondary" onClick={onDemo}>Run Demo Mode</button></div>{error && <div className="error">{error}</div>}</section>;
}

function DocumentLibrary({ documents, selectedId, onSelect, onDelete, inspection, onInspect }) {
  return <div className="document-library"><div className="library-heading"><div><div className="eyebrow">LOCAL DOCUMENT STORE</div><h3>Saved Documents</h3></div><span className="badge">{documents.length} saved</span></div>{documents.length === 0 && <p className="muted">No documents saved yet. Each upload receives its own local folder and record.</p>}{documents.map((document) => <div className={`document-row ${selectedId === document.document_id ? "selected" : ""}`} key={document.document_id} onClick={() => onSelect(document)}><div><b>{document.filename}</b><small>{new Date(document.uploaded_at).toLocaleString()} · {Math.round(document.size_bytes / 1024)} KB</small><span className={`doc-status ${document.extraction_status}`}>{document.extraction_status}</span></div><div className="document-actions"><button className="secondary" onClick={(event) => { event.stopPropagation(); onInspect(document.document_id); }}>Inspect</button><button className="ghost" onClick={(event) => { event.stopPropagation(); onDelete(document.document_id); }}>Remove</button></div></div>)}{inspection && <div className={`inspection-report ${inspection.ocr_status}`}><div className="eyebrow">EXTRACTION DIAGNOSTICS</div><h4>{inspection.ocr_status === "success" ? "Document readable" : "Document could not be fully extracted"}</h4>{inspection.issues.map((issue) => <p className="error-line" key={issue}>Reason: {issue}</p>)}{inspection.extracted_fields && Object.keys(inspection.extracted_fields).length > 0 && <div className="extracted-fields">{Object.entries(inspection.extracted_fields).map(([key, value]) => <span key={key}><b>{key.replaceAll("_", " ")}</b>{String(value)}</span>)}</div>}<small>Recommended format: {inspection.recommended_format}</small></div>}</div>;
}

function Pipeline({ stages }) {
  const names = stages || ["OCR", "Evidence Extraction", "SOP Retrieval", "Qwen2-VL", "Python Verification", "Evidence Chain"];
  return <section className="card"><ModuleTitle number="03" eyebrow="TRACEABLE PROCESSING" title="Processing Pipeline" description="Every stage is visible and independently traceable." /><div className="pipeline vertical-pipeline">{names.map((stage, index) => <div className="pipeline-step complete" key={stage}><span>✓</span><div><b>{stage}</b><small>{index === 3 ? "Local multimodal reasoning" : "Completed locally"}</small></div></div>)}</div></section>;
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

export default function App() {
  const [active, setActive] = useState("overview");
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

  useEffect(() => { Promise.all([getSovereignty(), getLlmStatus(), listDocuments()]).then(([s, l, docs]) => { setSovereignty(s.data); setLlm(l.data); setDocuments(docs.data); }).catch(() => setError("Backend unavailable. Start FastAPI on port 8001.")); }, []);
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

  const renderModule = () => {
    if (active === "overview") return <><ModuleTitle number="01" eyebrow="COMMAND CENTER" title="Sovereignty Overview" description="A local control surface for confidential engineering analysis." /><SovereigntyDashboard data={sovereignty} llm={llm} /><div className="card principle"><div className="eyebrow">DESIGN PRINCIPLE</div><h3>Evidence over assertion.</h3><p>The document provides evidence. RAG provides the applicable SOP. Qwen2.5-VL provides contextual reasoning. Python verifies numerical claims. The engineer makes the final decision.</p></div></>;
    if (active === "document") return <><ModuleTitle number="02" eyebrow="SOURCE DOCUMENT" title="Document Intake" description="Upload, inspect, analyze, and remove each confidential document independently." /><UploadPanel file={file} setFile={setFile} onAnalyze={() => analyze()} loading={loading} error={error} onDemo={runDemo} /><DocumentLibrary documents={documents} selectedId={documentId} onSelect={selectDocument} onDelete={removeDocument} inspection={inspection} onInspect={inspect} /></>;
    if (!result && ["pipeline", "finding", "verification", "review", "audit"].includes(active)) return <><ModuleTitle number="03" eyebrow="WORKFLOW" title={modules.find(([id]) => id === active)?.[1]} /><EmptyModule title="Module awaiting analysis" /></>;
    if (active === "pipeline") return <Pipeline stages={result.pipeline?.map((item) => item.stage)} />;
    if (active === "finding") return <><ModuleTitle number="04" eyebrow="ENGINEERING FINDING" title="Evidence Chain" description="The primary traceability view for the identified finding." /><Finding result={result} /></>;
    if (active === "verification") return <Verification result={result} />;
    if (active === "review") return <Review documentId={documentId} recommendation={result.ai_analysis.recommendation} onGenerate={approval} generated={generated} onReview={review} />;
    return <AuditTimeline events={events} logs={logs} />;
  };

  return <main><Header sovereignty={sovereignty} demo={result?.processing_mode === "DEMO"} /><div className="workspace"><Sidebar active={active} setActive={setActive} result={result} file={file} /><div className="module-content">{renderModule()}</div></div></main>;
}
