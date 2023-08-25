import json
import requests
import mistune
import gradio as gr

from pygments import highlight
from pygments.formatters import html
from pygments.lexers import get_lexer_by_name
from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker


LANGS = ["gpt-3.5-turbo", "gpt-4", "falcon"]
url_host = "http://0.0.0.0:7860"


def assist_interface(uid, message, version, history):
    if message == "" or uid == "":
        return "", history

    response = requests.post(
        url_host + "/assist",
        json={"uid": uid, "prompt": message, "version": version},
    )
    if response.status_code != 200:
        return message, history + [(message, response.text)]
    return "", history + [(message, generate_html(response.text))]


def get_user_interface(uid):
    response = requests.post(url_host + "/user_details", json={"uid": uid})

    return response.text


class HighlightRenderer(mistune.HTMLRenderer):
    def block_code(self, code, info=None):
        if info:
            lexer = get_lexer_by_name(info, stripall=True)
            formatter = html.HtmlFormatter()
            return highlight(code, lexer, formatter)
        return "<pre><code>" + mistune.escape(code) + "</code></pre>"


def generate_html(gpt_response):
    r"""
    This is used by the gradio to extract all of the user
    data and write it out as a giant json blob that can be easily diplayed.
    >>>
    >>> data = {'text': 'This is a test'}
    >>> generate_html(json.dumps(data))
    '<html><p>This is a test</p>\n</html>'
    """

    gpt_response = json.loads(gpt_response)
    gpt_response = gpt_response["text"]
    markdown = mistune.create_markdown(renderer=HighlightRenderer())
    gpt_response = markdown(gpt_response)
    return f"<html>{gpt_response}</html>"


def get_assist_interface():
    with gr.Blocks() as interface:
        gr.Markdown(
            f"<h1 style='text-align: center; margin-bottom: 1rem'>GPT4All chatbot</h1>"
        )
        gr.Markdown("Chat to the GPT4All bot")
        with gr.Column(variant="panel"):
            chatbot = gr.Chatbot()
            with gr.Row():
                id_textbox = gr.Textbox(container=False, label="UID", placeholder="UID")
            with gr.Row():
                llm_model = gr.components.Dropdown(
                    container=False, label="LLM Model", choices=LANGS, value="falcon"
                )
            with gr.Group():
                with gr.Row():
                    prompt_textbox = gr.Textbox(
                        container=False,
                        show_label=False,
                        scale=7,
                        label="Message",
                        placeholder="Type a message...",
                    )
                    submit_btn = gr.Button(
                        "Submit",
                        variant="primary",
                        scale=1,
                        min_width=150,
                    )
                    prompt_textbox.submit(
                        assist_interface,
                        inputs=[id_textbox, prompt_textbox, llm_model, chatbot],
                        outputs=[prompt_textbox, chatbot],
                    )
                    submit_btn.click(
                        assist_interface,
                        inputs=[id_textbox, prompt_textbox, llm_model, chatbot],
                        outputs=[prompt_textbox, chatbot],
                    )
    return interface


def get_db_interface():
    return gr.Interface(
        fn=get_user_interface,
        inputs="text",
        outputs="text",
        title="Get User Details",
        description="Get user details from the database",
    )


## The register interface uses this weird syntax to make sure we don't copy and
## paste quotes in the uid when we output it
def register_interface(name, openai_key):
    response = requests.post(
        url_host + "/register",
        json={"name": name, "openai_key": openai_key},
    )
    return response.json()


def get_register_interface():
    def wrapper(name, openai_key):
        result = register_interface(name, openai_key)
        return f"""
            {{'uid': '<span id='uid'>{result["uid"]}</span>', existing: {result["existing"]}}}
                <br>
                <button onclick="navigator.clipboard.writeText(document.getElementById('uid').innerText)">
                    Copy to clipboard
                </button>
        """

    return gr.Interface(
        fn=wrapper,
        inputs=[
            gr.components.Textbox(label="Name", type="text"),
            gr.components.Textbox(label="OpenAI key", type="text"),
        ],
        outputs=gr.components.HTML(),
        title="Register New User",
        description="Create a user by entering a username and openai_key (optional)",
    )


def get_history_interface(uid):
    response = requests.get(f"{url_host}/get_history/{uid}")
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
    response = requests.post(
        url_host + "/add_command",
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


def adblock_filter_interface(uid: str, url: str, version: str):
    response = requests.post(
        url_host + "/adblock_filter",
        json={"uid": uid, "url": url, "version": version},
    )
    return response.json()


def get_adblock_filter_interface():
    return gr.Interface(
        fn=adblock_filter_interface,
        inputs=[
            gr.components.Textbox(label="UID", type="text"),
            gr.components.Textbox(label="URL", type="text"),
            gr.components.Dropdown(label="LLM Model", choices=LANGS, value="falcon"),
        ],
        outputs="json",
        title="Adblock filter",
        description="Given a domain, use an LLM to determine whether to allow/block the domain.",
    )


def get_interface():
    return gr.TabbedInterface(
        [
            get_assist_interface(),
            get_db_interface(),
            get_register_interface(),
            get_history_gradio_interface(),
            get_add_command_interface(),
            get_adblock_filter_interface(),
        ]
    )
