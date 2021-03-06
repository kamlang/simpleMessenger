import os
from app import db, create_app
from app.models import User, Role, Message, Conversation

app = create_app(os.getenv("FLASK_CONFIG") or "default")

@app.shell_context_processor
def make_shell_context():
    return dict(
        app=app, db=db, User=User, Role=Role, Message=Message, Conversation=Conversation
    )

