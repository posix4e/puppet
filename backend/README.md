# Backend for the puppet

This is a Python-based application that uses FastAPI and OpenAI's GPT-4 model to provide a backend for puppet. It can receive telemetry from the puppet client. It can control the puppet and it provides its own quick webclient.

# dev

- (optional) Install virtualenv or equiv please
- pip install -r requirements.txt
- pytest

# you can also run the test server with
- uvicorn --host 0.0.0.0 --port 8000 backend:app --reload

