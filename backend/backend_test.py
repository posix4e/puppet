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
async def test_assist_with_no_key():
    data = {"name": "new_name", "openai_key": None}
    response = client.post("/register", json=data)
    uid = response.json()["uid"]

    data = {
        "uid": uid,
        "prompt": "test prompt",
        "version": "gpt-4",
    }
    response = client.post("/assist", json=data)
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_adblock_filter_with_no_key():
    data = {"name": "new_name", "openai_key": None}
    response = client.post("/register", json=data)
    uid = response.json()["uid"]

    data = {
        "uid": uid,
        "url": "ads.google.com",
        "version": "gpt-4",
    }
    response = client.post("/adblock_filter", json=data)
    assert "detail" in response.json()


@pytest.mark.asyncio
async def test_adblock_filter_with_gpt4all():
    data = {"name": "new_name", "openai_key": None}
    response = client.post("/register", json=data)
    uid = response.json()["uid"]

    data = {
        "uid": uid,
        "url": "ads.google.com",
        "version": "falcon",
    }
    response = client.post("/adblock_filter", json=data)
    json_response = response.json()
    assert "allow" in json_response
    assert "full_response" in json_response
    assert type(json_response["allow"]) is bool
    assert type(json_response["full_response"]) is str
