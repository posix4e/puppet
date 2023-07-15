from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from firebase_admin import credentials, messaging, initialize_app, auth
import openai
import uuid
import asyncio

app = FastAPI()

# To store user information in memory.
# WARNING: This information will be lost when the server stops/restarts
user_data = {}


class RegisterItem(BaseModel):
    apiKey: str
    authDomain: str
    databaseURL: str
    storageBucket: str
    openai_key: str


@app.post("/register")
async def register(item: RegisterItem):
    # Generate a unique user id
    uid = str(uuid.uuid4())

    # Initialize the Firebase app
    user_data[uid] = {
        "firebase": credentials.Certificate(
            {
                "apiKey": item.apiKey,
                "authDomain": item.authDomain,
                "databaseURL": item.databaseURL,
                "storageBucket": item.storageBucket,
            }
        ),
        "openai_key": item.openai_key,
    }

    initialize_app(user_data[uid]["firebase"], name=uid)

    return {"uid": uid}


class ProcessItem(BaseModel):
    uid: str
    prompt: str


@app.post("/process_request")
async def process_request(item: ProcessItem):
    # Get the user data using the provided uid
    user = user_data.get(item.uid)

    if not user:
        raise HTTPException(status_code=400, detail="Invalid uid")

    # Set the OpenAI key for this user
    openai.api_key = user["openai_key"]

    # Call OpenAI
    response = openai.Completion.create(
        engine="text-davinci-002", prompt=item.prompt, max_tokens=150
    )

    # The message data that will be sent to the client
    message = messaging.Message(
        data={
            "message": response.choices[0].text.strip(),
        },
        topic="updates",
    )

    # Send the message asynchronously
    asyncio.run(send_notification(message, item.uid))

    return {"message": "Notification sent"}


def send_notification(message, uid):
    # Send a message to the devices subscribed to the provided topic.
    response = messaging.send(message, app=user_data[uid]["firebase"])
    print("Successfully sent message:", response)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
