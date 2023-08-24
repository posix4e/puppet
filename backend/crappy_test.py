import uuid

import pytest
from fastapi.testclient import TestClient

import backend

client = TestClient(backend.app)


@pytest.mark.asyncio
async def test_register_new_name():
    data = {"name": "new_name"}
    response = client.post("/register", json=data)
    assert response.status_code == 200
    assert "uid" in response.json()
    uid = response.json()["uid"]

    data = {"name": "new_name"}
    response = client.post("/register", json=data)
    assert response.status_code == 200
    assert "uid" in response.json()
    assert response.json()["uid"] == uid


@pytest.mark.asyncio
async def test_register_existing_key():
    data = {"name": "existing_name"}
    response = client.post("/register", json=data)
    assert response.status_code == 200
    assert "uid" in response.json()
    uid = response.json()["uid"]

    data = {"name": "existing_name"}
    response = client.post("/register", json=data)
    assert response.status_code == 200
    assert "uid" in response.json()
    assert response.json()["uid"] == uid


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
