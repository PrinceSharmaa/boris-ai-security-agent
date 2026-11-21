from datetime import datetime,timezone,timedelta
from backend.agent_routing import plan,parse_event_filters
from backend.agent_tools import correlate_incidents
import pytest
pytest.importorskip("langgraph")
from backend.graph import execute_tools

def test_multi_intent_plan():
    p=plan('Correlate critical alerts from last 24 hours, find runbook and draft ServiceNow ticket','ticket')
    assert set(['search_security_events','calculate_incident_priority','correlate_incidents','retrieve_security_runbook','draft_ticket']).issubset(p)

def test_time_filter():
    assert parse_event_filters('critical alerts from last 48 hours')['hours']==48
    assert parse_event_filters('high alerts from past 2 days')['hours']==48

def test_general_chat_does_not_query_events(monkeypatch):
    def no_events(_):raise AssertionError('Should not query events for general chat')
    monkeypatch.setattr('backend.graph.search_security_events',no_events)
    result=execute_tools({'query':'What is encryption?','plan':['generate_advisory_answer','validate_output']})
    assert result['live_events']==[] and result['tool_trace']==[]

def test_correlations_only_on_selected_events():
    events=[{'id':'a','hostname':'A','category':'malware','severity':'high'},
            {'id':'b','hostname':'A','category':'malware','severity':'medium'}]
    groups=correlate_incidents(events)
    assert len(groups)==1 and groups[0]['count']==2
