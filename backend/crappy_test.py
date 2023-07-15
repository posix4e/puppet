import requests
import json


def test_register():
    data = {
        "apiKey": "test-api-key",
        "authDomain": "test-auth-domain",
        "databaseURL": "test-database-url",
        "storageBucket": "test-storage-bucket",
        "openai_key": "test-openai-key",
    }
    response = requests.post(
        "http://localhost:8000/register",
        data=json.dumps(data),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    uid = response.json().get("uid")
    assert uid is not None

    # Let's use this uid to send a process request
    data = {
        "uid": uid,
        "prompt": "Hello, OpenAI!",
    }
    response = requests.post(
        "http://localhost:8000/process_request",
        data=json.dumps(data),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json().get("message") == "Notification sent"
