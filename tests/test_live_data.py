from datetime import datetime,timezone
from backend import live_data

def test_generate_persists_and_filters(tmp_path,monkeypatch):
    monkeypatch.setattr(live_data.settings,'boris_data_dir',tmp_path)
    now=datetime(2026,11,21,tzinfo=timezone.utc)
    result=live_data.generate(12,seed=7,base_time=now)
    assert result['inserted']==12 and result['simulated']
    events=live_data.list_events(50)
    assert len(events)==12
    assert all(e['simulated']==1 and 'SYNTHETIC' in e['description'] for e in events)
    assert live_data.get_event(events[0]['id'])['id']==events[0]['id']
    assert len(live_data.list_events(severity='high'))==sum(e['severity']=='high' for e in events)
    assert live_data.summary()['total']==12
    assert live_data.seed_if_empty()['inserted']==0

def test_count_validation():
    import pytest
    with pytest.raises(ValueError):live_data.generate(251)
