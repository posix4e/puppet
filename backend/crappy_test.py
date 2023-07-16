import uuid

import pytest
from fastapi.testclient import TestClient

import backend

client = TestClient(backend.app)


@pytest.mark.asyncio
async def test_register():
    data = {
        "openai_key": "garbage",
    }
    client.post("/register", json=data)


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
