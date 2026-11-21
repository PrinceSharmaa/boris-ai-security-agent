from backend.triage import score_event

def test_critical_requires_review():
    result=score_event({'id':'x','severity':'critical','hostname':'SRV-IDENTITY-01','category':'credential_access','status':'new'})
    assert result['priority']=='P1' and result['requires_human_review']
    assert result['score']==100 and result['simulated']

def test_low_is_p4():
    result=score_event({'id':'y','severity':'low','hostname':'WS-1','category':'other','status':'new'})
    assert result['priority']=='P4' and not result['requires_human_review']

def test_missing_impact_is_explicit():
    result=score_event({'id':'z','severity':'medium','hostname':'WS-1','category':'other','status':'new'})
    assert result['missing_information']
