import os
import uuid
from datetime import datetime

import openai
from dotenv import load_dotenv
from easycompletion import openai_text_call
from fastapi import FastAPI, HTTPException
from gradio import mount_gradio_app
from fastapi.middleware.gzip import GZipMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uvicorn import Config, Server
from gpt4all import GPT4All
from models import Base, User, AndroidHistory, BrowserHistory, Command
from backend_ui import get_interface

GPT4ALL_MODELS_ENABLED = True
if GPT4ALL_MODELS_ENABLED:
    model = GPT4All("ggml-model-gpt4all-falcon-q4_0.bin")
    model.chat_session()
engine = create_engine("sqlite:///puppet.db")
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"

load_dotenv()

app = FastAPI(debug=True)
app.add_middleware(GZipMiddleware, minimum_size=1000)


class UserIDItem(BaseModel):
    uid: str


class RegisterItem(BaseModel):
    name: str
    openai_key: Optional[str]


class CommandItem(BaseModel):
    uid: str
    command: str


class EventItem(BaseModel):
    uid: str
    event: str


class AssistItem(BaseModel):
    uid: str
    prompt: str
    version: str


class SaveURLItem(BaseModel):
    uid: str
    machineid: str
    url: str


class URLItem(BaseModel):
    url: str
    version: str
    uid: Optional[str]


@app.post("/add_command")
async def add_command(item: CommandItem):
    db: Session = SessionLocal()
    new_command = Command(uid=item.uid, command=item.command)
    db.add(new_command)
    db.commit()
    db.refresh(new_command)
    return {"message": "Command added"}


@app.post("/send_event")
async def send_event(item: EventItem):
    print(f"Received event from {item.uid}:\n{item.event}")

    with open(f"{item.uid}_events.txt", "a") as f:
        f.write(f"{datetime.now()} - {item.event}\n")

    db: Session = SessionLocal()
    user = db.query(User).filter(User.uid == item.uid).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid UID")

    # Update the last time send_event was called and increment the number of events
    user.last_event = datetime.now()
    db.commit()

    # Get all the queued commands for this user
    commands = (
        db.query(Command)
        .filter(Command.uid == item.uid, Command.status == "queued")
        .all()
    )
    for command in commands:
        command.status = "running"
    db.commit()

    return {
        "message": "Event received",
        "commands": [command.command for command in commands],
    }


@app.post("/register")
async def register(item: RegisterItem):
    db: Session = SessionLocal()
    existing_user = db.query(User).filter(User.name == item.name).first()
    if existing_user:
        return {"uid": existing_user.uid, "existing": True}  # return existing UUID
    else:
        new_user = User(
            uid=str(uuid.uuid4()), name=item.name, openai_key=item.openai_key
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"uid": new_user.uid, "existing": False}


@app.post("/user_details")
async def user_details(item: UserIDItem):
    db: Session = SessionLocal()
    print(item)
    user = db.query(User).filter(User.uid == item.uid).first()
    if not user:
        return {"message": "No user with this uid found"}

    return {"uid": user.uid, "name": user.name, "openai_key": user.openai_key}


@app.post("/assist")
async def assist(item: AssistItem):
    db: Session = SessionLocal()
    response = {}

    user = db.query(User).filter(User.uid == item.uid).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid uid")

    if item.version.startswith("gpt-"):
        openai.api_key = user.openai_key
        response = openai_text_call(item.prompt, model=item.version)
        if "error" in response:
            raise HTTPException(status_code=400, detail=response["error"])
    elif item.version == "falcon":
        output = (
            model.generate(item.prompt, max_tokens=60, temp=0)
            if GPT4ALL_MODELS_ENABLED
            else "MODEL DISABLED"
        )
        response = {"text": output, "usage": None, "finish_reason": None, "error": None}
    else:
        raise HTTPException(status_code=400, detail="Invalid version: " + item.version)

    # Update the last time assist was called
    user.last_assist = datetime.now()

    # Store the history
    new_history = AndroidHistory(
        uid=item.uid, question=item.prompt, answer=response["text"]
    )
    db.add(new_history)
    db.commit()

    return response


@app.post("/adblock_filter")
async def adblock_filter(item: URLItem):
    db: Session = SessionLocal()
    prompt = 'I am building a soft ad-block filter, should I filter "{}"? answer directly in 1 sentence starting with yes or no.'.format(
        item.url
    )

    if item.version.startswith("gpt-"):
        user = db.query(User).filter(User.uid == item.uid).first()
        if not user:
            raise HTTPException(status_code=400, detail="Invalid uid")
        openai.api_key = user.openai_key
        response = openai_text_call(prompt, model=item.version)
        if response["error"]:
            raise HTTPException(status_code=400, detail=response["error"])
        output = response["text"] if "text" in response else ""
    elif item.version == "falcon":
        output = (
            model.generate(prompt[:-25], max_tokens=60, temp=0)
            if GPT4ALL_MODELS_ENABLED
            else "no 123456789"
        )

    if len(output) < 6:
        raise HTTPException(
            status_code=400, detail="Output length less than 6 characters: "
        )

    return {
        "allow": "no" in output[:6].lower(),
        "full_response": output,
    }


@app.get("/get_history/{uid}")
async def get_history(uid: str):
    db: Session = SessionLocal()
    history = db.query(AndroidHistory).filter(AndroidHistory.uid == uid).all()
    browser_history = db.query(BrowserHistory).filter(BrowserHistory.uid == uid).all()
    commands = db.query(Command).filter(Command.uid == uid).all()

    try:
        with open(f"{uid}_events.txt", "r") as f:
            events = f.read().split(",")
    except FileNotFoundError:
        events = ""

    return {
        "events": events,
        "history": [h.__dict__ for h in history],
        "browser_history": [h.__dict__ for h in browser_history],
        "commands": [c.__dict__ for c in commands],
    }


@app.post("/saveurl")
async def saveurl(item: SaveURLItem):
    db: Session = SessionLocal()
    new_browser_history = BrowserHistory(
        uid=item.uid, machineid=item.machineid, url=item.url
    )
    db.add(new_browser_history)
    db.commit()
    db.refresh(new_browser_history)
    return {"message": "Browser history saved"}


app = mount_gradio_app(
    app,
    get_interface(),
    path="/",
)

if __name__ == "__main__":
    config = Config("backend:app", host="0.0.0.0", port=7860, reload=True)
    server = Server(config)
    server.run()
