import os
import sys
import json

# Ensure project package is on path when tests run from repo root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from src.mcp_server import app

client = TestClient(app)


def test_tools_list():
    r = client.get('/mcp/tools')
    assert r.status_code == 200
    data = r.json()
    # Accept either a list or a dict with a 'tools' key
    tools = data if isinstance(data, list) else data.get('tools', [])
    assert isinstance(tools, list)
    # Ensure finance tool metadata present
    assert any('finance_qa' in json.dumps(t) for t in tools)


def test_finance_qa_post():
    payload = {"query": "What is dollar-cost averaging?", "session_id": "pytest-session"}
    r = client.post('/mcp/finance_qa', json=payload)
    assert r.status_code == 200
    d = r.json()
    assert d.get('status') == 'ok'
    assert 'response' in d
    assert d.get('session_id') == 'pytest-session'
