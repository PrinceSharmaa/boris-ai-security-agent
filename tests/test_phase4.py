from backend.agent_routing import classify, plan, choose_model
from backend.approvals import request_approval, decide, list_approvals
from backend.config import settings

def test_agent_routes():
    assert classify('Prepare ServiceNow ticket')=='ticket'
    assert classify('Show the malware runbook')=='playbook'
    assert classify('Analyze this critical endpoint alert')=='incident'
    assert classify('Hello')=='general'

def test_planner_and_model():
    assert 'calculate_incident_priority' in plan('analyze alert','incident')
    assert 'draft_ticket' in plan('draft ticket','ticket')
    model,profile=choose_model('incident','analyze')
    assert model and profile=='reasoning'

def test_persistent_approval(tmp_path,monkeypatch):
    monkeypatch.setattr(settings,'boris_data_dir',tmp_path)
    first=request_approval('demo-123',{'priority':'P1'})
    second=request_approval('demo-123',{'priority':'P1'})
    assert first['id']==second['id']
    assert len(list_approvals('pending'))==1
    result=decide(first['id'],'approved','test analyst','reviewed')
    assert result['updated'] and result['status']=='approved'
    assert decide(first['id'],'rejected','other')['updated'] is False
    assert not list_approvals('pending')
