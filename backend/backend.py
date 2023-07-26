import json
import uuid
from datetime import datetime

import mistune
import openai
from dotenv import load_dotenv
from easycompletion import openai_text_call
from fastapi import FastAPI, HTTPException
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.testclient import TestClient
from gradio import Interface, TabbedInterface, components, mount_gradio_app
from pydantic import BaseModel
from pygments import highlight
from pygments.formatters import html
from pygments.lexers import get_lexer_by_name
from sqlalchemy import JSON, Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import insert, select, text
from uvicorn import Config, Server

LANGS = [
    "gpt-3.5-turbo",
    "gpt-4",
]

Base = declarative_base()


class User(Base):
    __tablename__ = "user_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String, nullable=False)
    openai_key = Column(String, unique=True, nullable=False)

    def __repr__(self):
        return f"User(id={self.id}, uid={self.uid}"


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String, nullable=False)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)

    def __repr__(self):
        return f"History(id={self.id}, uid={self.uid}, question={self.question}, answer={self.answer}"


# Add a new table to store the commands
class Command(Base):
    __tablename__ = "commands"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String, nullable=False)
    command = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")

    def __repr__(self):
        return f"self.command"


engine = create_engine("sqlite:///puppet.db")
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

load_dotenv()

app = FastAPI(debug=True)
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Add a new API endpoint to add commands to the queue
class CommandItem(BaseModel):
    uid: str
    command: str


@app.post("/add_command")
async def add_command(item: CommandItem):
    db: Session = SessionLocal()
    new_command = Command(uid=item.uid, command=item.command)
    db.add(new_command)
    db.commit()
    db.refresh(new_command)
    return {"message": "Command added"}


class EventItem(BaseModel):
    uid: str
    event: str


@app.post("/send_event")
async def send_event(item: EventItem):
    print(f"Received event from {item.uid}:\n{item.event}")

    with open(f"{item.uid}_events.txt", "a") as f:
        f.write(f"{datetime.now()} - {item.event}\n")

    db: Session = SessionLocal()
    user = db.query(User).filter(User.uid == item.uid).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid uid")

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


class RegisterItem(BaseModel):
    openai_key: str


@app.post("/register")
async def register(item: RegisterItem):
    db: Session = SessionLocal()
    existing_user = db.query(User).filter(User.openai_key == item.openai_key).first()
    if existing_user:
        return {"uid": existing_user.uid}  # return existing UUID
    else:
        new_user = User(uid=str(uuid.uuid4()), openai_key=item.openai_key)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return {"uid": new_user.uid}


class AssistItem(BaseModel):
    uid: str
    prompt: str
    version: str


@app.post("/assist")
async def assist(item: AssistItem):
    db: Session = SessionLocal()
    user = db.query(User).filter(User.uid == item.uid).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid uid")

    # Call OpenAI
    openai.api_key = user.openai_key
    response = openai_text_call(item.prompt, model=item.version)

    # Update the last time assist was called
    user.last_assist = datetime.now()

    # Store the history
    new_history = History(uid=item.uid, question=item.prompt, answer=response["text"])

    db.add(new_history)
    db.commit()

    return response


@app.get("/get_history/{uid}")
async def get_history(uid: str):
    db: Session = SessionLocal()
    history = db.query(History).filter(History.uid == uid).all()
    commands = db.query(Command).filter(Command.uid == uid).all()
    if not history:
        raise HTTPException(status_code=400, detail="No history found for this uid")
    ret = {"history": [h.__dict__ for h in history]}

    if commands and len(commands) > 0:
        try:
            with open(f"{uid}_events.txt", "r") as f:
                events = f.read().split(",")
        except FileNotFoundError:
            events = None

        return {
            "events": events,
            "history": [h.__dict__ for h in history],
            "commands": [c.__dict__ for c in commands],
        }

    else:
        return {"history": [h.__dict__ for h in history]}


def assist_interface(uid, prompt, gpt_version):
    client = TestClient(app)

    response = client.post(
        "/assist",
        json={"uid": uid, "prompt": prompt, "version": gpt_version},
    )
    return generate_html_response_from_openai(response.text)


def get_user_interface(uid):
    db: Session = SessionLocal()
    user = db.query(User).filter(User.uid == uid).first()
    if not user:
        return {"message": "No user with this uid found"}
    return str(user)


class HighlightRenderer(mistune.HTMLRenderer):
    def block_code(self, code, info=None):
        if info:
            lexer = get_lexer_by_name(info, stripall=True)
            formatter = html.HtmlFormatter()
            return highlight(code, lexer, formatter)
        return "<pre><code>" + mistune.escape(code) + "</code></pre>"


def generate_html_response_from_openai(openai_response):
    r"""
    This is used by the gradio to extract all of the user
    data and write it out as a giant json blob that can be easily diplayed.
    >>>
    >>> data = {'text': 'This is a test'}
    >>> generate_html_response_from_openai(json.dumps(data))
    '<html><p>This is a test</p>\n</html>'
    """

    openai_response = json.loads(openai_response)
    openai_response = openai_response["text"]
    markdown = mistune.create_markdown(renderer=HighlightRenderer())
    openai_response = markdown(openai_response)
    return f"<html>{openai_response}</html>"


def get_assist_interface():
    gpt_version_dropdown = components.Dropdown(label="GPT Version", choices=LANGS)

    return Interface(
        fn=assist_interface,
        inputs=[
            components.Textbox(label="UID", type="text"),
            components.Textbox(label="Prompt", type="text"),
            gpt_version_dropdown,
        ],
        outputs="html",
        title="OpenAI Text Generation",
        description="Generate text using OpenAI's GPT-4 model.",
    )


def get_db_interface():
    return Interface(
        fn=get_user_interface,
        inputs="text",
        outputs="text",
        title="Get User Details",
        description="Get user details from the database",
    )


def register_interface(openai_key):
    client = TestClient(app)
    response = client.post(
        "/register",
        json={"openai_key": openai_key},
    )
    return response.json()


def get_register_interface():
    return Interface(
        fn=register_interface,
        inputs=[components.Textbox(label="OpenAI Key", type="text")],
        outputs="json",
        title="Register New User",
        description="Register a new user by entering an OpenAI key.",
    )


def get_history_interface(uid):
    client = TestClient(app)
    response = client.get(f"/get_history/{uid}")
    return response.json()


def get_history_gradio_interface():
    return Interface(
        fn=get_history_interface,
        inputs=[components.Textbox(label="UID", type="text")],
        outputs="json",
        title="Get User History",
        description="Get the history of questions and answers for a given user.",
    )


def add_command_interface(uid, command):
    client = TestClient(app)
    response = client.post(
        "/add_command",
        json={"uid": uid, "command": command},
    )
    return response.json()


def get_add_command_interface():
    return Interface(
        fn=add_command_interface,
        inputs=[
            components.Textbox(label="UID", type="text"),
            components.Textbox(label="Command", type="text"),
        ],
        outputs="json",
        title="Add Command",
        description="Add a new command for a given user.",
    )


app = mount_gradio_app(
    app,
    TabbedInterface(
        [
            get_assist_interface(),
            get_db_interface(),
            get_register_interface(),
            get_history_gradio_interface(),
            get_add_command_interface(),
        ]
    ),
    path="/",
)

if __name__ == "__main__":
    config = Config("backend:app", host="0.0.0.0", port=7860, reload=True)
    server = Server(config)
    server.run()
