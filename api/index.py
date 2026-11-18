"""
Subak-Soil Serverless REST API (`api/index.py`).

Exposes optimization, field-level soil urgency inference, and spatial
cross-validation endpoints for Vercel deployment.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from subak_soil_scheduler import (
    ICAR_CONSTANTS,
    ICAR_THRESHOLDS,
    evaluate_ai_models_unbiased,
    load_subak_dataset,
    predict_single_cluster_ai,
    solve_subak_schedule,
)

app = FastAPI(
    title="Subak-Soil Dispatch API",
    version="2.0.0",
    description="REST API for regional Super Seeder scheduling and soil carbon modeling.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class PredictRequest(BaseModel):
    soc_percent: float = 0.44
    nitrogen_kg_ha: float = 82.0
    phosphorus_kg_ha: float = 38.0
    potassium_kg_ha: float = 145.0
    soil_ph: float = 7.85
    soil_type: str = "Sandy Loam"
    paddy_area_ha: float = 165.0
    harvest_days_left: int = 4
    chc_machines: int = 1


@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "subak-soil-api",
        "constants": ICAR_CONSTANTS,
        "thresholds": ICAR_THRESHOLDS,
    }


@app.get("/api/optimize")
def api_optimize(
    district: str = Query(default="Sangrur", description="Target Punjab district"),
    max_machines: int = Query(default=15, ge=5, le=30),
    sharing_radius_km: float = Query(default=18.0, ge=5.0, le=40.0),
) -> Dict[str, Any]:
    # Unwrap default value if called directly as a Python function
    dist_val = getattr(district, "default", district)
    dist_str = str(dist_val if dist_val is not ... else "Sangrur")

    mm_val = getattr(max_machines, "default", max_machines)
    mm_int = int(mm_val if mm_val is not ... else 15)

    sr_val = getattr(sharing_radius_km, "default", sharing_radius_km)
    sr_float = float(sr_val if sr_val is not ... else 18.0)

    df = load_subak_dataset()
    schedule_df, summary = solve_subak_schedule(
        df,
        district=dist_str,
        max_machines_per_cluster_day=mm_int,
        sharing_radius_km=sr_float,
    )
    return {
        "summary": summary,
        "clusters": schedule_df.to_dict(orient="records"),
    }


@app.post("/api/predict")
def api_predict(req: PredictRequest) -> Dict[str, Any]:
    return predict_single_cluster_ai(
        soc_percent=req.soc_percent,
        nitrogen_kg_ha=req.nitrogen_kg_ha,
        phosphorus_kg_ha=req.phosphorus_kg_ha,
        potassium_kg_ha=req.potassium_kg_ha,
        soil_ph=req.soil_ph,
        soil_type=req.soil_type,
        paddy_area_ha=req.paddy_area_ha,
        harvest_days_left=req.harvest_days_left,
        chc_machines=req.chc_machines,
    )


@app.get("/api/evaluate")
def api_evaluate() -> Dict[str, Any]:
    df = load_subak_dataset()
    return evaluate_ai_models_unbiased(df)
