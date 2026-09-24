"""Optional FastAPI deployment adapter over the shared analysis services.

The stdlib server remains the zero-install local fallback. Install requirements.txt
and run `uvicorn src.backend.fastapi_app:app` for the production-shaped API.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .analyzer import analyze
from ..database.session import database_is_healthy
from .config import CORS_ORIGINS, DATASET_PATH, EXPERIMENTS_PATH, MODEL_ARTIFACT_PATH, MODEL_METADATA_PATH, MODEL_VERSION
from .storage import AnalysisStore

app = FastAPI(title="TrustGuard Digital Trust API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=list(CORS_ORIGINS), allow_credentials=False, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Content-Type"])
store = AnalysisStore()
shap_explainer = None


class AnalyzeRequest(BaseModel):
    url: str = Field(min_length=4, max_length=2048)


@app.get("/api/health")
def health():
    healthy = database_is_healthy()
    return {"status": "healthy" if healthy else "unhealthy", "database": "connected" if healthy else "unavailable", "model": "not_loaded", "version": "1.0.0"}


@app.get("/api/model/info")
def model_info():
    if MODEL_METADATA_PATH.exists():
        import json
        return json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))
    return {"loaded": False, "model_version": MODEL_VERSION, "status": "not_loaded"}


def get_shap_explainer():
    global shap_explainer
    if shap_explainer is None:
        from ..ml_model.shap_explainer import BenchmarkShapExplainer
        shap_explainer = BenchmarkShapExplainer(MODEL_ARTIFACT_PATH, MODEL_METADATA_PATH, DATASET_PATH)
    return shap_explainer


@app.get("/api/ml/feature-importance")
def feature_importance():
    try:
        return get_shap_explainer().global_importance(EXPERIMENTS_PATH)
    except (ImportError, FileNotFoundError, ValueError, OSError) as error:
        raise HTTPException(status_code=503, detail=f"Benchmark SHAP unavailable: {error}") from error


@app.get("/api/ml/explanation/{sample_id}")
def explanation(sample_id: str):
    try:
        return get_shap_explainer().explain_sample(sample_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (ImportError, FileNotFoundError, OSError) as error:
        raise HTTPException(status_code=503, detail=f"Benchmark SHAP unavailable: {error}") from error


@app.post("/api/analyze")
def create_analysis(request: AnalyzeRequest):
    try:
        result = analyze(request.url)
        return store.save(result)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/api/score")
def compatibility_score(request: AnalyzeRequest):
    return create_analysis(request)


@app.get("/api/analysis/{analysis_id}")
def get_analysis(analysis_id: str):
    result = store.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return result


@app.get("/api/history")
def history():
    return {"results": store.history()}


@app.get("/api/features/{analysis_id}")
def features(analysis_id: str):
    result = store.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {"analysis_id": analysis_id, "features": result["features"]}


@app.get("/api/explanation/{analysis_id}")
def analysis_explanation(analysis_id: str):
    result = store.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return {"analysis_id": analysis_id, "explanation": result["explanation"]}


@app.get("/api/statistics")
def statistics():
    return store.statistics()