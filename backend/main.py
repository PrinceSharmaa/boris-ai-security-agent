from fastapi import FastAPI, UploadFile, File, Depends, HTTPException
from pydantic import BaseModel, Field
from backend.security import verify_key
from backend.graph import graph
from backend.knowledge import ingest, list_docs, delete_doc
from backend.config import settings
from backend.live_data import list_events, get_event, summary, generate, seed_if_empty

app=FastAPI(title="BORIS Local API",version="0.1.0")

class ChatRequest(BaseModel):
    message: str = Field(min_length=1,max_length=12000)

@app.get("/api/health")
def health():return {"status":"ok","service":"boris-local"}

@app.get("/api/models",dependencies=[Depends(verify_key)])
def models():return {"default_model":settings.ollama_model,"embedding_model":settings.embedding_model}

@app.post("/api/chat",dependencies=[Depends(verify_key)])
def chat(body:ChatRequest):
    try:return graph.invoke({"query":body.message})
    except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc))

@app.post("/api/documents/upload",dependencies=[Depends(verify_key)])
async def upload(file:UploadFile=File(...)):
    if not file.filename:raise HTTPException(status_code=400,detail="Missing filename")
    # Limit memory use by reading at most 15MB + 1 byte.
    content=await file.read(15*1024*1024+1)
    try:return ingest(file.filename,content)
    except (ValueError,RuntimeError) as exc:raise HTTPException(status_code=400,detail=str(exc))

@app.get("/api/documents",dependencies=[Depends(verify_key)])
def documents():return list_docs()

@app.delete("/api/documents/{document_id}",dependencies=[Depends(verify_key)])
def delete(document_id:str):return {"deleted_chunks":delete_doc(document_id)}


class GenerateEventsRequest(BaseModel):
    count: int = Field(default=20,ge=1,le=250)

@app.post("/api/demo/seed",dependencies=[Depends(verify_key)])
def seed_demo():return seed_if_empty()

@app.post("/api/demo/generate",dependencies=[Depends(verify_key)])
def generate_demo(body:GenerateEventsRequest):return generate(body.count)

@app.get("/api/events",dependencies=[Depends(verify_key)])
def events(limit:int=50,severity:str|None=None,source:str|None=None,status:str|None=None,hours:int|None=None):
    return {"events":list_events(limit,severity,source,status,hours),"simulated":True}

@app.get("/api/events/summary",dependencies=[Depends(verify_key)])
def event_summary():return summary()

@app.get("/api/events/{event_id}",dependencies=[Depends(verify_key)])
def event_detail(event_id:str):
    result=get_event(event_id)
    if result is None:raise HTTPException(status_code=404,detail="Event not found")
    return result

from backend.triage import score_event, correlate_events, draft_ticket

@app.get('/api/incidents/correlations',dependencies=[Depends(verify_key)])
def incident_correlations():
    return {'correlations':correlate_events(),'simulated':True}

@app.get('/api/incidents/{event_id}/score',dependencies=[Depends(verify_key)])
def incident_score(event_id:str):
    event=get_event(event_id)
    if event is None:raise HTTPException(status_code=404,detail='Event not found')
    return score_event(event)

@app.post('/api/tickets/{event_id}/draft',dependencies=[Depends(verify_key)])
def ticket_draft(event_id:str):
    draft=draft_ticket(event_id)
    if draft is None:raise HTTPException(status_code=404,detail='Event not found')
    return draft

from backend.approvals import list_approvals, decide

class ApprovalDecision(BaseModel):
    decision: str
    reviewer: str = Field(min_length=1,max_length=100)
    reason: str = Field(default='',max_length=1000)

@app.get('/api/approvals',dependencies=[Depends(verify_key)])
def approvals(status:str|None=None):
    try:return {'approvals':list_approvals(status),'simulated':True}
    except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc))

@app.post('/api/approvals/{approval_id}/decision',dependencies=[Depends(verify_key)])
def approval_decision(approval_id:str,body:ApprovalDecision):
    try:result=decide(approval_id,body.decision,body.reviewer,body.reason)
    except ValueError as exc:raise HTTPException(status_code=400,detail=str(exc))
    if result is None:raise HTTPException(status_code=404,detail='Approval not found')
    if not result['updated']:raise HTTPException(status_code=409,detail='Approval already decided')
    return result
