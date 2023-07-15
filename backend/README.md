# Backend for the puppet


	This servers receives everything going on on the puppet. It can send requests to the puppet to do action. it uses openai as a llm currents

# dev

- (optional) Install virtualenv or equiv please
- pip install -r requirements.txt
- pytest

# you can also run the test server with
- uvicorn --host 0.0.0.0 --port 8000 backend:app --reload

