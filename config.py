import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY ="é$àéà$séf34efi][}{"
    USER_EMAIL_SENDER_EMAIL = os.environ.get('MAIL_USERNAME')
    SQLALCHEMY_TRACK_MODIFICATIONS =False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    UPLOAD_FOLDER =  os.path.join(basedir, 'app/static/avatars')
    APP_MAIL_SUBJECT_PREFIX = '[Glgmsh] '

class DevelopmentConfig(Config):
    DEBUG = True
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = 8025
    MAIL_USE_TLS = False
    APP_MAIL_ADMIN = os.environ.get('MAIL_ADMIN')
    USER_EMAIL_SENDER_EMAIL = 'Admin'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'users-dev.db')
    @staticmethod
    def init_app(app):
        pass

class TestingConfig(Config):
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    ADMINS= ['glgmsh@protonmail.com']
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')

class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data.sqlite')

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
