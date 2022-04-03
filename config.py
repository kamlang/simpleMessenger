import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    UPLOAD_FOLDER = os.path.join(basedir, "app/static/avatars")
    MAIL_SUBJECT_PREFIX = "[simpleMessenger] "
    ADMINS = ["admin@simpleMessenger.com"]
    POSTS_PER_PAGE = 7


class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = os.environ.get("SECRET_KEY") or "1"
    MAIL_USERNAME = ""
    MAIL_PASSWORD = ""
    REDIS_URL = os.environ.get("DEV_REDIS_URL") or "redis://localhost:6379"
    SSL_KEYFILE = os.path.join(basedir, "./certs/key.pem") or None
    SSL_CERTFILE = os.path.join(basedir, "./certs/cert.pem") or None
    USER_EMAIL_SENDER_EMAIL = "Admin"
    MAIL_SERVER = os.environ.get("DEV_MAIL_SERVER") or "localhost"
    MAIL_PORT = os.environ.get("DEV_MAIL_PORT") or 8025
    MAIL_USE_TLS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DEV_DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "users-dev.db")
    @staticmethod
    def init_app(app):
        pass


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "TEST_DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "data-test.sqlite")


class ProductionConfig(Config):
    SECRET_KEY = os.environ.get("SECRET_KEY")
    USER_EMAIL_SENDER_EMAIL = os.environ.get("MAIL_USERNAME")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_SERVER = os.environ.get("MAIL_SERVER")
    MAIL_PORT = os.environ.get("MAIL_PORT")
    MAIL_USE_TLS = True
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL"
    ) or "sqlite:///" + os.path.join(basedir, "data.sqlite")


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
