import uuid

import pytest
from fastapi.testclient import TestClient

import backend

client = TestClient(backend.app)


@pytest.mark.asyncio
async def test_register_new_name():
    data = {"name": "new_name", "openai_key": None}
    response = client.post("/register", json=data)
    print(response.text)
    assert response.status_code == 200
    assert "uid" in response.json()
    uid = response.json()["uid"]

    data = {"name": "new_name", "openai_key": None}
    response = client.post("/register", json=data)
    assert response.status_code == 200
    response_json = response.json()
    assert "uid" in response_json
    assert response_json["uid"] == uid
    assert response_json["existing"] == True


@pytest.mark.asyncio
async def test_send_event():
    data = {
        "uid": str(uuid.uuid4()),
        "event": "test event",
    }
    client.post("/register", json=data)


@pytest.mark.asyncio
async def test_assist():
    data = {
        "uid": str(uuid.uuid4()),
        "prompt": "test prompt",
        "version": "davinci-fake",
    }
    client.post("/assist", json=data)
