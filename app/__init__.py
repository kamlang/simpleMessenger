from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_moment import Moment
from config import config
from flask import Flask
from flask_bootstrap import Bootstrap
import logging
from logging.handlers import SMTPHandler,RotatingFileHandler
import redis
import os

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = "auth.login"
migrate = Migrate()
mail = Mail()
moment = Moment()
bootstrap = Bootstrap()
red = redis.StrictRedis()
csrf = CSRFProtect()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    moment.init_app(app)
    csrf.init_app(app)
    bootstrap.init_app(app)
    # attach routes and custom error pages here
    from app.main import main as main_blueprint
    from app.auth import auth as auth_blueprint
    from app.restricted import restricted as restricted_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix="/auth")
    app.register_blueprint(restricted_blueprint, url_prefix="/admin")

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
        app.logger.info("simpleMessenger startup")

    return app
