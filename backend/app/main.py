"""VERITAS API."""
from __future__ import annotations

import collections
import logging
import re
import time
import uuid

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

from . import ocr, pipeline, scenarios, store
from .config import settings
from .providers.base import get_provider
from .schemas import AnalyzeRequest, FeedbackRequest
from .security.sanitize import normalize_text, validate_image_magic

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("veritas")  # never log raw user content, only ids/sizes/timings

_CLIENT_ID_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


def client_id_of(request: Request) -> str:
    """Anonymous per-browser id (random, kept in the visitor's browser). Separates visitors' history; not authentication."""
    cid = request.headers.get("x-client-id", "")
    return cid if _CLIENT_ID_RE.match(cid) else "anon"


# Simple in-memory sliding-window limiter for the analysis endpoints (protects free AI quotas on a public deployment).
_hits: dict[str, "collections.deque[float]"] = {}


def rate_limit(request: Request) -> None:
    fwd = request.headers.get("x-forwarded-for", "")
    ip = (fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "?")) or "?"
    now = time.time()
    q = _hits.setdefault(ip, collections.deque())
    while q and now - q[0] > settings.rate_window_s:
        q.popleft()
    if len(q) >= settings.rate_limit:
        raise HTTPException(429, f"Too many analyses from your network. Please wait a few minutes and try again.")
    q.append(now)
    if len(_hits) > 5000:  # bound memory
        _hits.clear()

app = FastAPI(title="VERITAS API", version="1.0.0", docs_url="/api/docs", openapi_url="/api/openapi.json")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type", "X-Client-Id"],
)


@app.middleware("http")
async def request_context(request: Request, call_next):
    rid = uuid.uuid4().hex[:12]
    request.state.request_id = rid
    t0 = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        log.exception("unhandled error rid=%s path=%s", rid, request.url.path)
        return JSONResponse({"detail": "Internal error. Analysis was not completed.", "request_id": rid}, status_code=500)
    response.headers["X-Request-ID"] = rid
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Cache-Control"] = "no-store"
    log.info("rid=%s %s %s -> %s %dms", rid, request.method, request.url.path, response.status_code,
             int((time.perf_counter() - t0) * 1000))
    return response


@app.get("/", include_in_schema=False)
async def root():
    return {"service": "VERITAS API", "status": "ok", "health": "/api/health", "docs": "/api/docs",
            "note": "This is the backend API. The web app is hosted separately."}


@app.get("/api/health")
async def health():
    p = get_provider()
    return {
        "status": "ok",
        "ai_provider": p.name if p.available else "offline",
        "ai_enabled": p.available,
        "live_url_checks": settings.live_url_checks,
        "vision_ocr": p.available and p.name == "anthropic",
    }


@app.get("/api/scenarios")
async def list_scenarios():
    out = []
    for s in scenarios.SCENARIOS:
        has_img = (ocr.DEMO_DIR / f"{s['id']}.png").exists()
        out.append({k: s[k] for k in ("id", "title", "channel", "blurb", "text")} | {"has_screenshot": has_img})
    return out


@app.get("/api/scenarios/{scenario_id}/screenshot")
async def scenario_screenshot(scenario_id: str):
    if scenario_id not in scenarios.BY_ID:
        raise HTTPException(404, "Unknown scenario")
    path = ocr.DEMO_DIR / f"{scenario_id}.png"
    if not path.exists():
        raise HTTPException(404, "No demo screenshot for this scenario")
    return FileResponse(path, media_type="image/png")


@app.post("/api/analyze")
async def analyze_text(req: AnalyzeRequest, request: Request):
    rate_limit(request)
    cid = client_id_of(request)
    rid = request.state.request_id
    provider = get_provider()
    if req.scenario_id:
        sc = scenarios.BY_ID.get(req.scenario_id)
        if not sc:
            raise HTTPException(404, "Unknown scenario")
        report = await pipeline.analyze(sc["text"], "text", provider, rid)
    elif req.url and not req.text:
        url = req.url.strip()
        if not url:
            raise HTTPException(422, "Provide a URL, text, or scenario_id.")
        report = await pipeline.analyze(url, "url", provider, rid, raw_url=url)
    elif req.text and req.text.strip():
        text = normalize_text(req.text, settings.max_text_chars)
        if len(text) < 3:
            raise HTTPException(422, "Text is too short to analyze.")
        report = await pipeline.analyze(text, "text", provider, rid, raw_url=(req.url or None))
    else:
        raise HTTPException(422, "Provide text, a URL, or scenario_id.")
    store.save(report, cid)
    return report


ALLOWED_DOC_EXT = (".txt", ".eml", ".md")


@app.post("/api/analyze/upload")
async def analyze_upload(request: Request, file: UploadFile = File(...)):
    rate_limit(request)
    cid = client_id_of(request)
    rid = request.state.request_id
    provider = get_provider()
    name = (file.filename or "upload")[:120]
    data = await file.read(settings.max_image_bytes + 1)
    if len(data) == 0:
        raise HTTPException(422, "Empty file.")
    mime = validate_image_magic(data)
    if mime:
        if len(data) > settings.max_image_bytes:
            raise HTTPException(413, "Image too large (max 6 MB).")
        try:
            text, method, note = await ocr.image_to_text(data, mime, provider)
        except ocr.OCRUnavailable as e:
            raise HTTPException(422, str(e))
        text = normalize_text(text, settings.max_text_chars)
        if len(text) < 3:
            raise HTTPException(422, "No readable text was found in the image.")
        report = await pipeline.analyze(text, "image", provider, rid, source_filename=name, ocr_method=method, ocr_note=note)
        store.save(report, cid)  # saved WITHOUT the raw text
        report.extracted_text = text[:6000]
        return report
    elif name.lower().endswith(ALLOWED_DOC_EXT):
        if len(data) > settings.max_doc_bytes:
            raise HTTPException(413, "Document too large (max 200 KB).")
        if b"\x00" in data[:2000]:
            raise HTTPException(415, "Binary files are not supported. Upload a .txt/.eml file or a PNG/JPEG/WebP image.")
        text = normalize_text(data.decode("utf-8", "replace"), settings.max_text_chars)
        if len(text) < 3:
            raise HTTPException(422, "Document contains no readable text.")
        report = await pipeline.analyze(text, "document", provider, rid, source_filename=name)
    else:
        raise HTTPException(415, "Unsupported file type. Use PNG/JPEG/WebP screenshots or .txt/.eml documents.")
    store.save(report, cid)
    return report


@app.post("/api/incidents/{incident_id}/retry-ai")
async def retry_ai(incident_id: str, request: Request):
    """Re-run the full analysis (including the AI step) on the text still held in memory."""
    rate_limit(request)
    cid = client_id_of(request)
    if store.get(incident_id[:32], cid) is None:  # must be one of THIS visitor's reports
        raise HTTPException(404, "Incident not found")
    args = pipeline.recall(incident_id[:32])
    if not args:
        raise HTTPException(410, "The original text is no longer held (it is only kept in memory for ~30 minutes). Please submit it again.")
    provider = get_provider()
    if not provider.available:
        raise HTTPException(409, "No AI provider is configured.")
    report = await pipeline.analyze(args["text"], args["kind"], provider, request.state.request_id,
                                    source_filename=args["source_filename"], ocr_method=args["ocr_method"],
                                    ocr_note=args["ocr_note"], raw_url=args["raw_url"])
    store.delete(incident_id[:32], cid)
    store.save(report, cid)
    if args["kind"] == "image":
        report.extracted_text = args["text"][:6000]
    return report


@app.get("/api/incidents")
async def incidents(request: Request):
    return store.list_incidents(client_id_of(request))


@app.get("/api/incidents/{incident_id}")
async def incident(incident_id: str, request: Request):
    rep = store.get(incident_id[:32], client_id_of(request))
    if not rep:
        raise HTTPException(404, "Incident not found")
    return rep


@app.post("/api/incidents/{incident_id}/feedback")
async def feedback(incident_id: str, body: FeedbackRequest, request: Request):
    if not store.set_feedback(incident_id[:32], body.outcome, body.note, client_id_of(request)):
        raise HTTPException(404, "Incident not found")
    return {"ok": True}


@app.delete("/api/incidents")
async def clear_incidents(request: Request):
    return {"deleted": store.clear(client_id_of(request))}
