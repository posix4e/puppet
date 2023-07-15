import time
from fastapi.testclient import TestClient
import pytest
import json
import backend
import httpx


@pytest.mark.asyncio
async def test_register():
    client = TestClient(backend.app)

    data = {
        "apiKey": "test-api-key",
        "authDomain": "test-auth-domain",
        "databaseURL": "test-database-url",
        "storageBucket": "test-storage-bucket",
        "openai_key": "test-openai-key",
    }
    with pytest.raises(ValueError):
        client.post("/register", json=data)
