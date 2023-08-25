import mistune
import gradio as gr

from pygments import highlight
from pygments.formatters import html
from fastapi.testclient import TestClient


def assist_interface(uid, message, history):
    client = TestClient(app)
    if message == "" or uid == "":
        return "", history

    response = client.post(
        "/assist",
        json={"uid": uid, "prompt": message, "version": "falcon"},
    )
    if response.is_error:
        return message, history + [(message, "ERROR: invalid UID")]
    return "", history + [(message, generate_html(response.text))]


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
        gr.Markdown("Chat to the GPT4All falcon bot")
        with gr.Column(variant="panel"):
            chatbot = gr.Chatbot()
            with gr.Row():
                id_textbox = gr.Textbox(container=False, label="UID", placeholder="UID")
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
                        inputs=[id_textbox, prompt_textbox, chatbot],
                        outputs=[prompt_textbox, chatbot],
                    )
                    submit_btn.click(
                        assist_interface,
                        inputs=[id_textbox, prompt_textbox, chatbot],
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
def register_interface(name):
    client = TestClient(app)
    response = client.post(
        "/register",
        json={"name": name},
    )
    return response.json()


def get_register_interface():
    def wrapper(name):
        result = register_interface(name)
        return f"""<p id='uid'>{result["uid"]}</p>
        <button onclick="navigator.clipboard.writeText(document.getElementById('uid').innerText)">
        Copy to clipboard
        </button>"""

    return gr.Interface(
        fn=wrapper,
        inputs=[gr.components.Textbox(label="Name", type="text")],
        outputs=gr.components.HTML(),
        title="Register New User",
        description="Create a user by entering a username",
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


def adblock_filter_interface(url: str):
    client = TestClient(app)
    response = client.post(
        "/adblock_filter",
        json={"url": url},
    )
    return response.json()


def get_adblock_filter_interface():
    return gr.Interface(
        fn=adblock_filter_interface,
        inputs=[
            gr.components.Textbox(label="URL", type="text"),
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
