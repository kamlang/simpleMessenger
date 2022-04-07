# simpleMessenger

This is a small chatting app built with Python Flask.
It uses SSE and Redis to implement instant messaging system and also has a small API.

It has full registration and login support and has the possibility to create conversation with multiple users.

The frontend is build using Jinja templates and Bootstrap as well as a bit of javascript.
Flask-SQLAlchemy is used to interact with the database, as it's very flexible it can be used with almost
any database engine.

I partly rely on the Mega Flask Tutorial from Miguel Grinberg from which I've learnt a lot.

This was done as an exercise to know more about how a web app works.

If you want to run it locally:

- Git clone this repo
- create a virtual environmment : python -m venv venv
- run flask db init, flask db migrate and flask db upgrade
- Create user and Roles from flask shell (I need tomake a script for this)
- you can run it using either flask run or gunicorn

If you use a .env file for configuration variable and running gunicorn you need to add the below in gunicorn.conf.py file.

gunicorn -b localhost:5000 -w 4 manage:app --worker-class gevent -c ./gunicorn.conf.py

# gunicorn.conf.py

import os
from dotenv import load_dotenv

for env_file in ('.env', '.flaskenv'):
    env = os.path.join(os.getcwd(), env_file)
    if os.path.exists(env):
        load_dotenv(env)

