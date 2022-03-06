import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    UPLOAD_FOLDER = os.path.join(basedir, "app/static/avatars")
    MAIL_SUBJECT_PREFIX = "[Glgmsh] "
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD")
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME")
    ADMINS = ["glgmsh@protonmail.com"]
    POSTS_PER_PAGE = 7


class DevelopmentConfig(Config):
    DEBUG = True
    SECRET_KEY = "i$àdf$àd-gdà241243$-fà$gsb-sà$a-d$às"
    REDIS_URL = "redis://localhost:6379"
    REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD")
    SSL_KEYFILE = os.path.join(basedir, "./certs/key.pem")
    SSL_CERTFILE =os.path.join(basedir, "./certs/cert.pem")
    USER_EMAIL_SENDER_EMAIL = "Admin"
    MAIL_SERVER = "localhost"
    MAIL_PORT = 8025
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
    MAIL_SERVER = "smtp.gmail.com"
    MAIL_PORT = 587
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
