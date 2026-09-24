"""Dependency-free HTTP API and static-file server for the local MVP."""

import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

from .analyzer import analyze
from ..database.session import database_is_healthy
from .config import CORS_ORIGINS, DATASET_PATH, EXPERIMENTS_PATH, MODEL_ARTIFACT_PATH, MODEL_METADATA_PATH, MODEL_VERSION
from .storage import AnalysisStore

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "src" / "frontend"
STORE = AnalysisStore()
SHAP_EXPLAINER = None


def _get_shap_explainer():
    global SHAP_EXPLAINER
    if SHAP_EXPLAINER is None:
        from ..ml_model.shap_explainer import BenchmarkShapExplainer
        SHAP_EXPLAINER = BenchmarkShapExplainer(MODEL_ARTIFACT_PATH, MODEL_METADATA_PATH, DATASET_PATH)
    return SHAP_EXPLAINER


class RequestHandler(BaseHTTPRequestHandler):
    def _send(self, status: int, body: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        origin = self.headers.get("Origin")
        self.send_header("Access-Control-Allow-Origin", origin if origin in CORS_ORIGINS else CORS_ORIGINS[0])
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", CORS_ORIGINS[0])
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.split("?", 1)[0]
        if path == "/api/health":
            healthy = database_is_healthy()
            self._json(200 if healthy else 503, {"status": "healthy" if healthy else "unhealthy", "database": "connected" if healthy else "unavailable", "model": "not_loaded", "version": "1.0.0"})
            return
        if path == "/api/history":
            self._json(200, {"results": STORE.history()})
            return
        if path == "/api/statistics":
            self._json(200, STORE.statistics())
            return
        if path == "/api/model/info":
            if MODEL_METADATA_PATH.exists():
                self._json(200, json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8")))
            else:
                self._json(200, {"loaded": False, "model_version": MODEL_VERSION, "status": "not_loaded", "message": "No trained benchmark model is installed; prototype trust indicators remain available."})
            return
        if path == "/api/ml/feature-importance":
            try:
                self._json(200, _get_shap_explainer().global_importance(EXPERIMENTS_PATH))
            except (ImportError, FileNotFoundError, ValueError, OSError) as error:
                self._json(503, {"error": f"Benchmark SHAP unavailable: {error}"})
            return
        if path.startswith("/api/ml/explanation/"):
            try:
                self._json(200, _get_shap_explainer().explain_sample(unquote(path.rsplit("/", 1)[-1])))
            except ValueError as error:
                self._json(404, {"error": str(error)})
            except (ImportError, FileNotFoundError, OSError) as error:
                self._json(503, {"error": f"Benchmark SHAP unavailable: {error}"})
            return
        if path.startswith("/api/analysis/"):
            analysis_id = unquote(path.rsplit("/", 1)[-1])
            result = STORE.get(analysis_id)
            self._json(200, result) if result else self._json(404, {"error": "Analysis not found"})
            return
        if path.startswith("/api/features/") or path.startswith("/api/explanation/"):
            analysis_id = unquote(path.rsplit("/", 1)[-1])
            result = STORE.get(analysis_id)
            if not result:
                self._json(404, {"error": "Analysis not found"})
            elif "/features/" in path:
                self._json(200, {"analysis_id": analysis_id, "features": result["features"]})
            else:
                self._json(200, {"analysis_id": analysis_id, "explanation": result["explanation"]})
            return
        if path in {"/", "/index.html"}:
            self._file(FRONTEND / "index.html", "text/html; charset=utf-8")
            return
        if path == "/styles.css":
            self._file(FRONTEND / "styles.css", "text/css; charset=utf-8")
            return
        if path == "/app.js":
            self._file(FRONTEND / "app.js", "text/javascript; charset=utf-8")
            return
        self._json(404, {"error": "Not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in {"/api/analyze", "/api/score"}:
            self._json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length > 10000:
                raise ValueError("Request body is too large")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict) or not isinstance(payload.get("url"), str):
                raise ValueError("Request body must contain a string URL")
            result = analyze(payload["url"])
            STORE.save(result)
            self._json(200, result)
        except (ValueError, json.JSONDecodeError, TypeError, UnicodeDecodeError) as error:
            self._json(400, {"error": str(error)})

    def _json(self, status: int, value: dict) -> None:
        self._send(status, json.dumps(value).encode("utf-8"), "application/json")

    def _file(self, path: Path, content_type: str) -> None:
        try:
            self._send(200, path.read_bytes(), content_type)
        except FileNotFoundError:
            self._json(404, {"error": "Frontend file not found"})

    def log_message(self, format: str, *args: object) -> None:
        return


def run(host: str = "127.0.0.1", port: int = 8000) -> None:
    server = ThreadingHTTPServer((host, port), RequestHandler)
    print(f"Digital Trust Score running at http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()