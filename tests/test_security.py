from fraud_agent_orchestrator.security import AuditTrail


def test_audit_chain_verifies():
    t = AuditTrail()
    t.append("a", {"x": 1})
    t.append("b", {"y": 2})
    assert t.verify() is True


def test_audit_tamper_fails():
    t = AuditTrail()
    t.append("a", {"x": 1})
    t.events[-1].payload = {"x": 2}
    assert t.verify() is False
