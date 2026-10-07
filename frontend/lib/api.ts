import type { AnalysisReport, Health, IncidentRow, Scenario } from "./types";

export class ApiError extends Error {
  constructor(message: string, public status: number) { super(message); }
}

async function parse<T>(r: Response): Promise<T> {
  if (!r.ok) {
    let msg = `Request failed (${r.status})`;
    try {
      const j = await r.json();
      if (typeof j.detail === "string") msg = j.detail;
      else if (Array.isArray(j.detail) && j.detail[0]?.msg) msg = j.detail[0].msg;
    } catch { /* non-JSON error body */ }
    if (r.status >= 500 || r.status === 0) msg = "The analysis service is unavailable. Is the backend running?";
    throw new ApiError(msg, r.status);
  }
  return r.json() as Promise<T>;
}

// Random per-browser id so each visitor only sees their own history on a shared deployment. Not authentication.
let memoryId: string | null = null;
function clientId(): string {
  const KEY = "veritas-client-id";
  try {
    let id = localStorage.getItem(KEY);
    if (!id) {
      id = (crypto.randomUUID?.() ?? `${Date.now()}${Math.random().toString(16).slice(2)}`).replace(/[^A-Za-z0-9_-]/g, "");
      localStorage.setItem(KEY, id);
    }
    return id;
  } catch {
    // storage blocked: fall back to an id that lasts for this page load
    if (!memoryId) memoryId = `m${Date.now()}${Math.random().toString(16).slice(2)}`.padEnd(20, "0");
    return memoryId;
  }
}

async function safeFetch(input: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  headers.set("X-Client-Id", clientId());
  try { return await fetch(input, { ...init, headers }); }
  catch { throw new ApiError("Cannot reach the VERITAS backend. Start it with `uvicorn app.main:app --port 8000`.", 0); }
}

export const api = {
  health: () => safeFetch("/api/health").then((r) => parse<Health>(r)),
  scenarios: () => safeFetch("/api/scenarios").then((r) => parse<Scenario[]>(r)),
  analyzeText: (text: string) =>
    safeFetch("/api/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ text }) }).then((r) => parse<AnalysisReport>(r)),
  analyzeUrl: (url: string) =>
    safeFetch("/api/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ url }) }).then((r) => parse<AnalysisReport>(r)),
  analyzeScenario: (scenario_id: string) =>
    safeFetch("/api/analyze", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ scenario_id }) }).then((r) => parse<AnalysisReport>(r)),
  analyzeFile: (file: File | Blob, name?: string) => {
    const fd = new FormData();
    fd.append("file", file, name || (file as File).name || "upload");
    return safeFetch("/api/analyze/upload", { method: "POST", body: fd }).then((r) => parse<AnalysisReport>(r));
  },
  incidents: () => safeFetch("/api/incidents").then((r) => parse<IncidentRow[]>(r)),
  incident: (id: string) => safeFetch(`/api/incidents/${encodeURIComponent(id)}`).then((r) => parse<AnalysisReport>(r)),
  feedback: (id: string, outcome: "was_scam" | "was_legitimate" | "not_sure") =>
    safeFetch(`/api/incidents/${encodeURIComponent(id)}/feedback`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ outcome }) }).then((r) => parse<{ ok: boolean }>(r)),
  retryAi: (id: string) =>
    safeFetch(`/api/incidents/${encodeURIComponent(id)}/retry-ai`, { method: "POST" }).then((r) => parse<AnalysisReport>(r)),
  clearIncidents: () => safeFetch("/api/incidents", { method: "DELETE" }).then((r) => parse<{ deleted: number }>(r)),
};
