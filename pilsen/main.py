import os
from typing import Optional, List
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
import datetime

from database import get_db, engine, Base
import models

# Garante criação de tabelas
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Pielsen Reconciliation & Feedback Portal API",
    description="API para o Portal de Reconciliação e Feedback Pielsen (PoC)",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Schemas Pydantic
class ProgrammeApproveRequest(BaseModel):
    proposed_harmonized_title: Optional[str] = None
    proposed_category: Optional[str] = None
    status: str = "Accepted"
    feedback_comments: Optional[str] = None

class ProgrammeUpdateRequest(BaseModel):
    harmonized_title: Optional[str] = None
    subtitle: Optional[str] = None
    category: Optional[str] = None
    repeat_code: Optional[str] = None
    reconciliation_key: Optional[str] = None
    status: Optional[str] = None
    feedback_comments: Optional[str] = None

class SpotFeedbackRequest(BaseModel):
    status: str
    comments: Optional[str] = None

class SpotUpdateRequest(BaseModel):
    spot_title: Optional[str] = None
    advertiser: Optional[str] = None
    planned_time: Optional[str] = None
    monitored_time: Optional[str] = None
    discrepancy_type: Optional[str] = None
    status: Optional[str] = None
    comments: Optional[str] = None

# --- Endpoints da API ---

@app.get("/api/channels")
def list_channels(db: Session = Depends(get_db)):
    return db.query(models.Channel).all()

@app.get("/api/cycles")
def list_cycles():
    return [
        {"id": "Initial Delivery", "name": "Initial Delivery"},
        {"id": "First Redelivery", "name": "First Redelivery"},
        {"id": "Final Redelivery", "name": "Final Redelivery"},
    ]

@app.get("/api/programmes/new")
def get_new_programmes(
    channel_code: Optional[str] = None,
    status: Optional[str] = None,
    cycle: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Programme).filter(models.Programme.is_new_programme == 1)
    if channel_code:
        query = query.filter(models.Programme.channel_code == channel_code)
    if status:
        query = query.filter(models.Programme.status == status)
    if cycle:
        query = query.filter(models.Programme.delivery_cycle == cycle)
    return query.all()

@app.post("/api/programmes/{prog_id}/approve")
def approve_new_programme(
    prog_id: int,
    req: ProgrammeApproveRequest,
    db: Session = Depends(get_db)
):
    prog = db.query(models.Programme).filter(models.Programme.id == prog_id).first()
    if not prog:
        raise HTTPException(status_code=404, detail="Programa não encontrado")
    
    if req.proposed_harmonized_title:
        prog.proposed_harmonized_title = req.proposed_harmonized_title
        prog.harmonized_title = req.proposed_harmonized_title
    if req.proposed_category:
        prog.proposed_category = req.proposed_category
        prog.category = req.proposed_category
    
    prog.status = req.status
    if req.feedback_comments:
        prog.feedback_comments = req.feedback_comments
        
    db.commit()
    db.refresh(prog)
    return prog

@app.get("/api/programmes/differences")
def get_programme_differences(
    channel_code: Optional[str] = None,
    cycle: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Programme).filter(models.Programme.programme_before_title.isnot(None))
    if channel_code:
        query = query.filter(models.Programme.channel_code == channel_code)
    if cycle:
        query = query.filter(models.Programme.delivery_cycle == cycle)
    if status:
        query = query.filter(models.Programme.status == status)
    return query.all()

@app.get("/api/programmes/all")
def get_all_programmes(
    channel_code: Optional[str] = None,
    cycle: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Programme)
    if channel_code:
        query = query.filter(models.Programme.channel_code == channel_code)
    if cycle:
        query = query.filter(models.Programme.delivery_cycle == cycle)
    if search:
        pattern = f"%{search}%"
        query = query.filter(
            (models.Programme.original_title.ilike(pattern)) |
            (models.Programme.harmonized_title.ilike(pattern)) |
            (models.Programme.reconciliation_key.ilike(pattern))
        )
    return query.all()

@app.put("/api/programmes/{prog_id}")
def update_programme(
    prog_id: int,
    req: ProgrammeUpdateRequest,
    db: Session = Depends(get_db)
):
    prog = db.query(models.Programme).filter(models.Programme.id == prog_id).first()
    if not prog:
        raise HTTPException(status_code=404, detail="Programa não encontrado")
    
    if req.harmonized_title is not None:
        prog.harmonized_title = req.harmonized_title
    if req.subtitle is not None:
        prog.subtitle = req.subtitle
    if req.category is not None:
        prog.category = req.category
    if req.repeat_code is not None:
        prog.repeat_code = req.repeat_code
    if req.reconciliation_key is not None:
        prog.reconciliation_key = req.reconciliation_key
    if req.status is not None:
        prog.status = req.status
    if req.feedback_comments is not None:
        prog.feedback_comments = req.feedback_comments
        
    db.commit()
    db.refresh(prog)
    return prog

@app.get("/api/spots/differences")
def get_spot_differences(
    channel_code: Optional[str] = None,
    cycle: Optional[str] = None,
    discrepancy_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.SpotDifference)
    if channel_code:
        query = query.filter(models.SpotDifference.channel_code == channel_code)
    if cycle:
        query = query.filter(models.SpotDifference.delivery_cycle == cycle)
    if discrepancy_type:
        query = query.filter(models.SpotDifference.discrepancy_type == discrepancy_type)
    return query.all()

@app.post("/api/spots/{spot_id}/feedback")
def update_spot_feedback(
    spot_id: int,
    req: SpotFeedbackRequest,
    db: Session = Depends(get_db)
):
    spot = db.query(models.SpotDifference).filter(models.SpotDifference.id == spot_id).first()
    if not spot:
        raise HTTPException(status_code=404, detail="Spot não encontrado")
    
    spot.status = req.status
    if req.comments:
        spot.comments = req.comments
        
    db.commit()
    db.refresh(spot)
    return spot

@app.put("/api/spots/{spot_id}")
def update_spot(
    spot_id: int,
    req: SpotUpdateRequest,
    db: Session = Depends(get_db)
):
    spot = db.query(models.SpotDifference).filter(models.SpotDifference.id == spot_id).first()
    if not spot:
        raise HTTPException(status_code=404, detail="Spot não encontrado")
    
    if req.spot_title is not None:
        spot.spot_title = req.spot_title
    if req.advertiser is not None:
        spot.advertiser = req.advertiser
    if req.planned_time is not None:
        spot.planned_time = req.planned_time
    if req.monitored_time is not None:
        spot.monitored_time = req.monitored_time
    if req.discrepancy_type is not None:
        spot.discrepancy_type = req.discrepancy_type
    if req.status is not None:
        spot.status = req.status
    if req.comments is not None:
        spot.comments = req.comments
        
    db.commit()
    db.refresh(spot)
    return spot

@app.get("/api/kpis")
def get_kpi_dashboard(db: Session = Depends(get_db)):
    metrics = db.query(models.KpiMetric).all()
    
    # Contagens em tempo real do banco de dados
    new_programmes_count = db.query(models.Programme).filter(models.Programme.is_new_programme == 1).count()
    prog_diffs_count = db.query(models.Programme).filter(models.Programme.programme_before_title.isnot(None), models.Programme.status != 'Closed').count()
    spot_diffs_count = db.query(models.SpotDifference).filter(models.SpotDifference.status != 'Closed').count()
    
    return {
        "summary": {
            "new_programmes": new_programmes_count,
            "prog_differences_open": prog_diffs_count,
            "spot_differences_open": spot_diffs_count,
            "sla_compliance": 94.5,
            "asrun_success_rate": 98.2,
            "spot_match_rate": 96.8
        },
        "metrics_list": metrics
    }

# Monta arquivos estáticos da pasta static/
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def read_root():
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)
