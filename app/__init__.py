from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_moment import Moment
from config import config
from flask import Flask
from flask_bootstrap import Bootstrap

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.session_protection = "strong"
login_manager.login_view = 'auth.login'
migrate = Migrate()
mail = Mail()
moment=Moment()
bootstrap=Bootstrap()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    migrate.init_app(app,db)
    login_manager.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    moment.init_app(app)
    bootstrap.init_app(app)
    # attach routes and custom error pages here
    from .main import main as main_blueprint
    from .auth import auth as auth_blueprint
    from .restricted import restricted as restricted_blueprint
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint,url_prefix='/auth')
    app.register_blueprint(restricted_blueprint,url_prefix='/admin')
    return app
