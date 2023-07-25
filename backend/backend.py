import json
import uuid
from datetime import datetime

import gradio as gr
import mistune
import openai
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel
from pygments import highlight
from pygments.formatters import html
from pygments.lexers import get_lexer_by_name
from sqlalchemy import JSON, Column, Integer, String, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.sql import insert, select, text
from uvicorn import Config, Server
from fastapi.middleware.gzip import GZipMiddleware

LANGS = [
    "text-davinci-002:100",
    "text-davinci-003:1500",
    "gpt-3.5-turbo:4000",
    "gpt-4:6000",
]

Base = declarative_base()


class User(Base):
    __tablename__ = "user_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String, nullable=False)
    openai_key = Column(String)

    def __repr__(self):
        return f"User(id={self.id}, uid={self.uid}"


class History(Base):
    __tablename__ = "history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uid = Column(String, nullable=False)
    question = Column(String, nullable=False)
    answer = Column(JSON, nullable=False)

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
    new_user = User(uid=str(uuid.uuid4()), openai_key=item.openai_key)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"uid": new_user.uid}


class AssistItem(BaseModel):
    uid: str
    prompt: str
    version: str


def generate_quick_completion(prompt, model):
    dropdrown = model.split(":")
    engine = dropdrown[0]
    max_tokens = int(dropdrown[1])
    if "gpt" in model:
        message = [{"role": "user", "content": prompt}]
        response = openai.ChatCompletion.create(
            model=engine,
            messages=message,
            temperature=0.2,
            max_tokens=max_tokens,
            frequency_penalty=0.0,
        )
    elif "davinci" in model:
        response = openai.Completion.create(
            engine=engine, prompt=prompt, max_tokens=max_tokens
        )
    else:
        raise Exception("Unknown model")
    return response


@app.post("/assist")
async def assist(item: AssistItem):
    db: Session = SessionLocal()
    user = db.query(User).filter(User.uid == item.uid).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid uid")

    # Call OpenAI
    openai.api_key = user.openai_key
    response = generate_quick_completion(item.prompt, item.version)

    # Update the last time assist was called
    user.last_assist = datetime.now()

    # Store the history
    new_history = History(
        uid=item.uid, question=item.prompt, answer=json.loads(str(response))
    )

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
    return gradio_user_output_helper(response.text)


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


def gradio_user_output_helper(data):
    r"""
    This is used by the gradio to extract all of the user
    data and write it out as a giant json blob that can be easily diplayed.
    >>> choices = [{'message': {'content': 'This is a test'}}]
    >>> data = { 'id': '1', 'object': 'user', 'created': '2021-09-01', 'model': 'gpt-3', 'choices': choices}
    >>> gradio_user_output_helper(json.dumps(data))
    '<html><h2>ID: 1</h2><p>Object: user</p><p>Created: 2021-09-01</p><p>Model: gpt-3</p><h3>Choices:</h3><p>Text: <p>This is a test</p>\n</p></html>'
    """
    html_output = "<html>"
    json_data = json.loads(data)

    id = json_data["id"]
    object = json_data["object"]
    created = json_data["created"]
    model = json_data["model"]
    choices = json_data["choices"]

    html_output += f"<h2>ID: {id}</h2>"
    html_output += f"<p>Object: {object}</p>"
    html_output += f"<p>Created: {created}</p>"
    html_output += f"<p>Model: {model}</p>"

    html_output += "<h3>Choices:</h3>"
    if "davinci" in model:
        for choice in choices:
            text = choice["text"]
            html_output += f"<p>Text: {text}</p>"
    elif "gpt" in model:
        for choice in choices:
            markdown = mistune.create_markdown(renderer=HighlightRenderer())
            text = markdown(choice["message"]["content"])
            html_output += f"<p>Text: {text}</p>"
    html_output += "</html>"
    return html_output


def get_assist_interface():
    gpt_version_dropdown = gr.components.Dropdown(label="GPT Version", choices=LANGS)

    return gr.Interface(
        fn=assist_interface,
        inputs=[
            gr.components.Textbox(label="UID", type="text"),
            gr.components.Textbox(label="Prompt", type="text"),
            gpt_version_dropdown,
        ],
        outputs="html",
        title="OpenAI Text Generation",
        description="Generate text using OpenAI's GPT-4 model.",
    )


def get_db_interface():
    return gr.Interface(
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
    return gr.Interface(
        fn=register_interface,
        inputs=[gr.components.Textbox(label="OpenAI Key", type="text")],
        outputs="json",
        title="Register New User",
        description="Register a new user by entering an OpenAI key.",
    )


def get_history_interface(uid):
    client = TestClient(app)
    response = client.get(f"/get_history/{uid}")
    return response.json()


def get_history_gradio_interface():
    return gr.Interface(
        fn=get_history_interface,
        inputs=[gr.components.Textbox(label="UID", type="text")],
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
    return gr.Interface(
        fn=add_command_interface,
        inputs=[
            gr.components.Textbox(label="UID", type="text"),
            gr.components.Textbox(label="Command", type="text"),
        ],
        outputs="json",
        title="Add Command",
        description="Add a new command for a given user.",
    )


app = gr.mount_gradio_app(
    app,
    gr.TabbedInterface(
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
