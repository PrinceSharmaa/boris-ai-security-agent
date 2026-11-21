"""Explainable synthetic-event triage; demonstration policy, NOT enterprise severity policy."""
from collections import defaultdict
from datetime import datetime, timezone
from backend.live_data import list_events, get_event

SEVERITY={'low':20,'medium':45,'high':72,'critical':92}
CRITICAL_HOST_PREFIXES=('SRV-IDENTITY','SRV-ERP')

def score_event(event:dict)->dict:
    base=SEVERITY.get(str(event.get('severity','')).lower(),40)
    reasons=[f"Source severity: {event.get('severity','unknown')} ({base} baseline)"]
    if str(event.get('hostname','')).startswith(CRITICAL_HOST_PREFIXES):
        base+=8;reasons.append('Illustrative business-critical server (+8)')
    if event.get('category') in ('credential_access','exfiltration'):
        base+=8;reasons.append('Sensitive threat category (+8)')
    if event.get('status')=='resolved':
        reasons.append('Marked resolved; verify closure evidence (no automatic downgrade)')
    score=min(100,base)
    priority='P1' if score>=85 else 'P2' if score>=65 else 'P3' if score>=40 else 'P4'
    return {'event_id':event['id'],'priority':priority,'score':score,'requires_human_review':priority in ('P1','P2'),
            'factors':reasons,'missing_information':['Asset ownership and criticality confirmation','Detection confidence','Actual business impact'],
            'simulated':True,'policy':'DEMO ONLY: replace scoring weights and thresholds with approved incident policy'}

def correlate_events(limit=500)->list[dict]:
    """Group by endpoint and category in a 24h window, without claiming common cause."""
    groups=defaultdict(list)
    for event in list_events(limit=limit):
        try:
            ts=datetime.fromisoformat(event['observed_at'].replace('Z','+00:00'))
            if (datetime.now(timezone.utc)-ts).total_seconds()>86400:continue
        except (ValueError,TypeError):continue
        groups[(event['hostname'],event['category'])].append(event)
    output=[]
    for (host,category),events in groups.items():
        if len(events)<2:continue
        ranked=sorted((score_event(e) for e in events),key=lambda x:x['score'],reverse=True)
        output.append({'hostname':host,'category':category,'event_count':len(events),
                       'event_ids':[e['id'] for e in events], 'suggested_priority':ranked[0]['priority'],
                       'highest_score':ranked[0]['score'],'requires_human_review':ranked[0]['requires_human_review'],
                       'explanation':'Same host and category within 24 hours; temporal grouping is NOT proof of a linked incident.',
                       'simulated':True})
    return sorted(output,key=lambda g:(-g['highest_score'],-g['event_count']))

def draft_ticket(event_id:str)->dict|None:
    event=get_event(event_id)
    if event is None:return None
    triage=score_event(event)
    return {'event_id':event_id,'title':f"[SYNTHETIC] {event['title']} — {event['hostname']}",
            'description':event['description'],'source':event['source'],'suggested_priority':triage['priority'],
            'work_notes':f"Demo alert {event_id} observed at {event['observed_at']}. Verify alert in source console, collect evidence, review applicable runbook, and obtain analyst approval before remediation.",
            'review_required':triage['requires_human_review'],'submission':'manual_copy_only','simulated':True}
