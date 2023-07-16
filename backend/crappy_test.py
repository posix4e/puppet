import time
import uuid
from fastapi.testclient import TestClient
import pytest
import json
import backend
import httpx


@pytest.mark.asyncio
async def test_register():
    client = TestClient(backend.app)

    data = {
        "openai_key": "garbage",
    }
    client.post("/register", json=data)


@pytest.mark.asyncio
async def test_send_event():
    client = TestClient(backend.app)

    data = {
        "uid": str(uuid.uuid4()),
        "event": "test event",
    }
    client.post("/register", json=data)


@pytest.mark.asyncio
async def test_assist():
    client = TestClient(backend.app)

    data = {
        "uid": str(uuid.uuid4()),
        "prompt": "test prompt",
        "version": "davinci-fake",
    }
    client.post("/assist", json=data)
