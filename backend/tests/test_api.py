import struct
import zlib

from fastapi.testclient import TestClient

from app.main import app
from app import scenarios

client = TestClient(app)


def _png() -> bytes:
    def chunk(t, d):
        c = struct.pack(">I", len(d)) + t + d
        return c + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    raw = b"\x00\xff\x00\x00"
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)) + \
        chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b"")


def test_health():
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["ai_provider"] == "offline"
    assert "X-Request-ID" in r.headers


def test_analyze_text_and_history_and_feedback():
    r = client.post("/api/analyze", json={"text": scenarios.BY_ID["bank-suspension"]["text"]})
    assert r.status_code == 200
    rep = r.json()
    assert rep["risk"]["risk_level"] == "high_risk"
    assert {"risk_score", "confidence_score", "top_factors", "uncertainty_notes"} <= rep["risk"].keys()
    assert "disclaimer" in rep and rep["timeline"]

    assert any(i["id"] == rep["id"] for i in client.get("/api/incidents").json())
    got = client.get(f"/api/incidents/{rep['id']}").json()
    assert got["id"] == rep["id"]
    fb = client.post(f"/api/incidents/{rep['id']}/feedback", json={"outcome": "was_scam"})
    assert fb.status_code == 200
    assert client.get(f"/api/incidents/{rep['id']}").json()["feedback"] == "was_scam"
    assert client.post("/api/incidents/nope/feedback", json={"outcome": "was_scam"}).status_code == 404


def test_scenario_endpoint_and_gallery():
    sc = client.get("/api/scenarios").json()
    assert len(sc) >= 6
    r = client.post("/api/analyze", json={"scenario_id": "job-registration-fee"})
    assert r.status_code == 200 and r.json()["category"] == "job_offer"
    assert client.post("/api/analyze", json={"scenario_id": "nope"}).status_code == 404


def test_validation_errors():
    assert client.post("/api/analyze", json={}).status_code == 422
    assert client.post("/api/analyze", json={"text": "  "}).status_code == 422
    assert client.post("/api/analyze", json={"text": "x" * 30000}).status_code == 422
    assert client.post("/api/analyze", content=b"not json", headers={"content-type": "application/json"}).status_code == 422


def test_url_input():
    r = client.post("/api/analyze", json={"url": "http://203.0.113.9/login"})
    assert r.status_code == 200
    assert "ip_literal_host" in {s["id"] for s in r.json()["technical_signals"]}
    r = client.post("/api/analyze", json={"url": "file:///etc/passwd"})
    assert r.status_code == 200  # analysed statically, never fetched


def test_upload_rejects_unsafe_files():
    assert client.post("/api/analyze/upload", files={"file": ("a.exe", b"MZ\x90\x00" + b"\x00" * 50)}).status_code == 415
    assert client.post("/api/analyze/upload", files={"file": ("a.txt", b"")}).status_code == 422
    assert client.post("/api/analyze/upload", files={"file": ("a.svg", b"<svg onload=alert(1)>")}).status_code == 415
    assert client.post("/api/analyze/upload", files={"file": ("big.txt", b"a" * 300_000)}).status_code == 413
    assert client.post("/api/analyze/upload", files={"file": ("x.txt", b"ab\x00cd" * 10)}).status_code == 415


def test_upload_text_document():
    body = scenarios.BY_ID["delivery-fee"]["text"].encode()
    r = client.post("/api/analyze/upload", files={"file": ("msg.txt", body)})
    assert r.status_code == 200 and r.json()["input"]["kind"] == "document"


def test_image_without_ocr_fails_clearly_not_silently():
    r = client.post("/api/analyze/upload", files={"file": ("shot.png", _png())})
    assert r.status_code == 422
    assert "paste" in r.json()["detail"].lower()


def test_demo_fixture_screenshot_path(tmp_path, monkeypatch):
    from app import ocr
    img = _png()
    (tmp_path / "demo.png").write_bytes(img)
    (tmp_path / "demo.txt").write_text(scenarios.BY_ID["bank-suspension"]["text"])
    monkeypatch.setattr(ocr, "DEMO_DIR", tmp_path)
    r = client.post("/api/analyze/upload", files={"file": ("shot.png", img)})
    assert r.status_code == 200
    rep = r.json()
    assert rep["input"]["ocr_method"] == "demo_fixture" and "fixture" in rep["input"]["ocr_note"].lower()
    assert rep["risk"]["risk_level"] == "high_risk"


def test_errors_do_not_leak_internals():
    r = client.get("/api/incidents/does-not-exist")
    assert r.status_code == 404 and "Traceback" not in r.text


def test_history_is_isolated_per_client_id():
    a = {"X-Client-Id": "a" * 24}
    b = {"X-Client-Id": "b" * 24}
    rep = client.post("/api/analyze", json={"text": "Your account is suspended, verify now at http://x.top"}, headers=a).json()
    assert any(i["id"] == rep["id"] for i in client.get("/api/incidents", headers=a).json())
    assert not any(i["id"] == rep["id"] for i in client.get("/api/incidents", headers=b).json())
    assert client.get(f"/api/incidents/{rep['id']}", headers=b).status_code == 404
    assert client.post(f"/api/incidents/{rep['id']}/feedback", json={"outcome": "was_scam"}, headers=b).status_code == 404
    assert client.post(f"/api/incidents/{rep['id']}/retry-ai", headers=b).status_code == 404
    assert client.delete("/api/incidents", headers=b).json()["deleted"] == 0
    assert client.get(f"/api/incidents/{rep['id']}", headers=a).status_code == 200
    # malformed ids fall back to the shared 'anon' bucket, never to someone else's
    assert client.get(f"/api/incidents/{rep['id']}", headers={"X-Client-Id": "short"}).status_code == 404


def test_rate_limit_blocks_bursts(monkeypatch):
    from app import main
    from app.config import settings
    main._hits.clear()
    monkeypatch.setattr(settings, "rate_limit", 3)
    h = {"X-Forwarded-For": "203.0.113.77"}
    codes = [client.post("/api/analyze", json={"text": "hello there friend"}, headers=h).status_code for _ in range(5)]
    assert codes[:3] == [200, 200, 200] and codes[3:] == [429, 429]
    assert client.get("/api/health", headers=h).status_code == 200  # only analysis endpoints are limited
    main._hits.clear()


def test_root_returns_friendly_info():
    r = client.get("/")
    assert r.status_code == 200 and r.json()["health"] == "/api/health"
