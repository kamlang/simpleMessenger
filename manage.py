import os
from app import db, create_app
# from app.models import User,Role
from app.models import User, Role, Message, Conversation
import logging
from logging.handlers import SMTPHandler
from logging.handlers import RotatingFileHandler

app = create_app(os.getenv("FLASK_CONFIG") or "default")


@app.shell_context_processor
def make_shell_context():
    #    return dict(app=app,db=db, User=User, Role=Role)
    return dict(
        app=app, db=db, User=User, Role=Role, Message=Message, Conversation=Conversation
    )

### Adding logging

if app.config["MAIL_SERVER"]:
    auth = None
    if app.config["MAIL_USERNAME"] or app.config["MAIL_PASSWORD"]:
        auth = (app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
    secure = None
    if app.config["MAIL_USE_TLS"]:
        secure = ()
    mail_handler = SMTPHandler(
        mailhost=(app.config["MAIL_SERVER"], app.config["MAIL_PORT"]),
        fromaddr="no-reply@" + app.config["MAIL_SERVER"],
        toaddrs=app.config["ADMINS"],
        subject="Microblog Failure",
        credentials=auth,
        secure=secure,
    )
    mail_handler.setLevel(logging.ERROR)

    app.logger.addHandler(mail_handler)

    if not os.path.exists("logs"):
        os.mkdir("logs")
    file_handler = RotatingFileHandler(
        "logs/microblog.log", maxBytes=10240, backupCount=10
    )
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
        )
    )
    file_handler.setLevel(logging.DEBUG)

    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.DEBUG)
    app.logger.info("SimpleMessenger startup")
