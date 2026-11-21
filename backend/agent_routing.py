"""Deterministic, auditable multi-intent planner; no autonomous tool loops."""
import re
from backend.config import settings

INTENT_TERMS={
 'ticket':('servicenow','ticket','work notes','ticket draft'),
 'incident':('incident','alert','telemetry','endpoint','triage','severity','priority','correlat','detection','security event','last 24 hours'),
 'playbook':('runbook','playbook','remediation procedure','investigation steps'),
 'knowledge':('policy','document','knowledge base','according to','pdf'),
}

def classify(query:str)->str:
    q=query.lower()
    for intent,terms in INTENT_TERMS.items():
        if any(t in q for t in terms):return intent
    return 'general'

def plan(query:str,intent:str)->list[str]:
    q=query.lower()
    steps=[]
    if intent in ('incident','ticket') or any(t in q for t in ('alerts','events','incidents','correlat')):
        steps+=['search_security_events','calculate_incident_priority']
        if 'correlat' in q or 'related' in q or 'group' in q:steps.append('correlate_incidents')
    if intent in ('incident','ticket','playbook','knowledge') or any(t in q for t in ('runbook','playbook','procedure')):
        steps.append('retrieve_security_runbook')
    if intent=='ticket' or any(t in q for t in ('servicenow','work notes','draft ticket')):
        steps.append('draft_ticket')
    return list(dict.fromkeys(steps))+['generate_advisory_answer','validate_output']

def choose_model(intent:str,query:str)->tuple[str,str]:
    if intent in ('incident','ticket') or len(query)>500:
        return (settings.ollama_reasoning_model or settings.ollama_model,'reasoning')
    return (settings.ollama_fast_model or settings.ollama_model,'fast')

def parse_event_filters(query:str)->dict:
    q=query.lower()
    severity=next((s for s in ('critical','high','medium','low') if re.search(r'\b'+s+r'\b',q)),None)
    match=re.search(r'(?:last|past|previous)\s+(\d{1,3})\s*(hours?|hrs?|days?)',q)
    hours=(int(match.group(1))*(24 if match.group(2).startswith('day') else 1)) if match else 24
    return {'severity':severity,'hours':max(1,min(hours,24*30)),'limit':50}
