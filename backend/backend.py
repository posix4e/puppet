from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from firebase_admin import credentials, messaging, initialize_app, auth
import openai
import asyncio
import gradio as gr
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from dotenv import load_dotenv

load_dotenv()


app = FastAPI()

# User credentials will be stored in this dictionary
user_data = {}


class RegisterItem(BaseModel):
    apiKey: str
    authDomain: str
    databaseURL: str
    storageBucket: str


@app.post("/register")
async def register(item: RegisterItem):
    # Firebase initialization with user-specific credentials
    cred = credentials.Certificate(
        {
            "apiKey": item.apiKey,
            "authDomain": item.authDomain,
            "databaseURL": item.databaseURL,
            "storageBucket": item.storageBucket,
        }
    )
    firebase_app = initialize_app(cred, name=str(len(user_data)))
    # Add the Firebase app and auth details to the user_data dictionary
    user_data[str(len(user_data))] = {
        "firebase_app": firebase_app,
        "authDomain": item.authDomain,
    }
    return {"uid": str(len(user_data) - 1)}  # Return the user ID


class ProcessItem(BaseModel):
    uid: str
    prompt: str


@app.post("/process_request")
async def process_request(item: ProcessItem):
    # Get the user's Firebase app from the user_data dictionary
    firebase_app = user_data.get(item.uid, {}).get("firebase_app", None)
    authDomain = user_data.get(item.uid, {}).get("authDomain", None)

    if not firebase_app or not authDomain:
        raise HTTPException(status_code=400, detail="Invalid uid")

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
        app=firebase_app,  # Use the user-specific Firebase app
    )

    # Send the message asynchronously
    asyncio.run(send_notification(message))

    return {"message": "Notification sent"}


def send_notification(message):
    # Send a message to the devices subscribed to the provided topic.
    response = messaging.send(message)
    print("Successfully sent message:", response)


def gradio_interface():
    def register(apiKey, authDomain, databaseURL, storageBucket):
        response = requests.post(
            "http://localhost:8000/register",
            json={
                "apiKey": apiKey,
                "authDomain": authDomain,
                "databaseURL": databaseURL,
                "storageBucket": storageBucket,
            },
        )
        return response.json()

    def process_request(uid, prompt):
        response = requests.post(
            "http://localhost:8000/process_request", json={"uid": uid, "prompt": prompt}
        )
        return response.json()

    demo = gr.Interface(
        fn=[register, process_request],
        inputs=[
            [
                gr.inputs.Textbox(label="apiKey"),
                gr.inputs.Textbox(label="authDomain"),
                gr.inputs.Textbox(label="databaseURL"),
                gr.inputs.Textbox(label="storageBucket"),
            ],
            [gr.inputs.Textbox(label="uid"), gr.inputs.Textbox(label="prompt")],
        ],
        outputs="json",
        title="API Explorer",
        description="Use this tool to make requests to the Register and Process Request APIs",
    )
    return demo


def process_request_interface(uid, prompt):
    item = ProcessItem(uid=uid, prompt=prompt)
    response = process_request(item)
    return response


def get_gradle_interface():
    return gr.Interface(
        fn=process_request_interface,
        inputs=[
            gr.inputs.Textbox(label="UID", type="text"),
            gr.inputs.Textbox(label="Prompt", type="text"),
        ],
        outputs="text",
        title="OpenAI Text Generation",
        description="Generate text using OpenAI's GPT-3 model.",
    )


app = gr.mount_gradio_app(app, get_gradle_interface(), path="/")
