"""Read-only and advisory tool adapters. All event records are synthetic."""
from backend.live_data import list_events, get_event
from backend.triage import score_event, draft_ticket
from backend.knowledge import retrieve
from backend.agent_routing import parse_event_filters
from datetime import datetime, timezone, timedelta
from collections import defaultdict


def search_security_events(query:str)->dict:
    filters=parse_event_filters(query)
    return {'filters':filters,'events':list_events(**filters),'simulated':True}

def calculate_incident_priority(events:list[dict])->list[dict]:
    return [score_event(e) for e in events[:20]]

def correlate_incidents(events:list[dict])->list[dict]:
    groups=defaultdict(list)
    for event in events:groups[(event['hostname'],event['category'])].append(event)
    results=[]
    for (host,category),rows in groups.items():
        if len(rows)<2:continue
        scores=[score_event(e) for e in rows]
        highest=max(scores,key=lambda s:s['score'])
        results.append({'hostname':host,'category':category,'event_ids':[e['id'] for e in rows],
                        'count':len(rows),'suggested_priority':highest['priority'],
                        'explanation':'Same host and category in the selected time window; NOT proof of one incident.', 'simulated':True})
    return results

def retrieve_security_runbook(query:str)->list[dict]:
    return retrieve(query)

def draft_tickets(events:list[dict])->list[dict]:
    return [ticket for e in events[:5] if (ticket:=draft_ticket(e['id']))]
