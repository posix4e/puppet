from sqlalchemy import Column, Integer, String, DateTime, create_engine, Table, MetaData
from sqlalchemy.sql import text, select, insert
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import openai
from fastapi.middleware.wsgi import WSGIMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
from dotenv import load_dotenv
import requests
from uvicorn import Config, Server
import os
from typing import Optional
import gradio as gr
from enum import Enum

Base = declarative_base()


class User(Base):
    __tablename__ = "user_data"

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String, nullable=False)
    openai_key = Column(String)
    last_assist = Column(DateTime)


engine = create_engine("sqlite:///users.db")
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

load_dotenv()
app = FastAPI(debug=True)


class EventItem(BaseModel):
    uid: str
    event: str


@app.post("/send_event")
async def send_event(item: EventItem):
    print(f"Received event from {item.uid}:\n{item.event}")

    with open(f"{item.uid}_events.txt", "a") as f:
        f.write(f"{datetime.now()} - {item.event}\n")

    return {"message": "Event received"}


class RegisterItem(BaseModel):
    openai_key: str


@app.post("/register")
async def register(item: RegisterItem):
    db: Session = SessionLocal()
    new_user = User(uuid=str(uuid.uuid4()), openai_key=item.openai_key)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"uid": new_user.uuid}


class AssistItem(BaseModel):
    uid: str
    prompt: str
    version: str


def generate_quick_completion(prompt, gpt_version):
    response = openai.Completion.create(
        engine=gpt_version, prompt=prompt, max_tokens=1500
    )
    return response


@app.post("/assist")
async def assist(item: AssistItem):
    db: Session = SessionLocal()
    user = db.query(User).filter(User.uuid == item.uid).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid uid")

    # Call OpenAI
    openai.api_key = user.openai_key
    response = generate_quick_completion(item.prompt, item.version)

    # Update the last time assist was called
    user.last_assist = datetime.now()
    db.commit()

    return response


def assist_interface(uid, prompt, gpt_version):
    response = requests.post(
        "http://localhost:8000/assist",
        json={"uid": uid, "prompt": prompt, "version": gpt_version},
    )
    return response.text


def get_user_interface(uid):
    db: Session = SessionLocal()
    user = db.query(User).filter(User.uuid == uid).first()
    if not user:
        return {"message": "No user with this uid found"}
    return str(user)


def get_assist_interface():
    gpt_version_dropdown = gr.inputs.Dropdown(
        label="GPT Version",
        choices=["text-davinci-002", "text-davinci-003", "text-davinci-004"],
        default="text-davinci-002",
    )

    return gr.Interface(
        fn=assist_interface,
        inputs=[
            gr.inputs.Textbox(label="UID", type="text"),
            gr.inputs.Textbox(label="Prompt", type="text"),
            gpt_version_dropdown,
        ],
        outputs="text",
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
    response = requests.post(
        "http://localhost:8000/register",
        json={"openai_key": openai_key},
    )
    return response.json()


def get_register_interface():
    return gr.Interface(
        fn=register_interface,
        inputs=[gr.inputs.Textbox(label="OpenAI Key", type="text")],
        outputs="text",
        title="Register New User",
        description="Register a new user by entering an OpenAI key.",
    )


app = gr.mount_gradio_app(
    app,
    gr.TabbedInterface(
        [
            get_assist_interface(),
            get_db_interface(),
            get_register_interface(),
        ]
    ),
    path="/",
)

if __name__ == "__main__":
    config = Config("backend:app", host="127.0.0.1", port=8000, reload=True)
    server = Server(config)
    server.run()
