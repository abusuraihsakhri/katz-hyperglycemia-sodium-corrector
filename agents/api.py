"""
FastAPI REST API Server for Katz Hyperglycemia Sodium Corrector.
"""
from typing import Dict, Any, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from .base import AuditLogger, PHIGuard
from .models import SystemTaskPayload, ConsensusDossier
from .supervisor import SystemSupervisor
from katz_sodium import calculate_metrics

supervisor = SystemSupervisor(model_provider="mock")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Fail fast rather than reporting a healthy service with an unsigned
    # or development-key audit ledger.
    AuditLogger.get_trail()
    yield


app = FastAPI(
    lifespan=lifespan,
    title="Katz Hyperglycemia Sodium Corrector API",
    description="Enterprise Distributed Component Platform (Clinical & Biomedical AI)",
    version="3.0.0-ENTERPRISE",
)


class ChatRequest(BaseModel):
    query: str


class SodiumRequest(BaseModel):
    sodium: float
    glucose: float


@app.post("/api/corrected-sodium")
def api_corrected_sodium(payload: SodiumRequest):
    try:
        return calculate_metrics(sodium=payload.sodium, glucose=payload.glucose)
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/health")
def health():
    return {"status": "HEALTHY", "service": "katz-hyperglycemia-sodium-corrector", "domain": "Clinical & Biomedical AI", "standard": "CAP / CLSI / ISO Standards", "version": "3.0.0-ENTERPRISE"}


@app.get("/metrics")
def metrics():
    return {
        "dossiers_processed_total": len(supervisor.dossier_registry),
        "audit_blocks_total": len(AuditLogger.get_trail()),
        "system_status": "NOMINAL_OPTIMAL"
    }


@app.post("/api/audit")
def api_audit(payload: SystemTaskPayload):
    dossier = supervisor.process_task(payload)
    return dossier.to_dict()


@app.post("/api/chat")
def api_chat(req: ChatRequest):
    try:
        ans = supervisor.query_supervisory_chat(req.query)
        return {"response": ans}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/audit/logs")
def api_audit_logs():
    return {"audit_trail": AuditLogger.get_trail(), "verified": AuditLogger.verify_integrity()}
