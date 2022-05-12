# simpleMessenger

This is a small chatting app built with Python Flask.
It uses SSE and Redis to implement instant messaging system and also has a small API.

It has full registration and login support and has the possibility to create conversation with multiple users.

The frontend is build using Jinja templates and Bootstrap as well as a bit of raw javascript.
Flask-SQLAlchemy is used to interact with the database, as it's very flexible it can be used with almost
any database engine.

I partly rely on the Mega Flask Tutorial from Miguel Grinberg from which I've learnt a lot.

As an exercise, an OAuth server has also be implemented to manage API authorization, it's clearly overkilled but it was done for the learning experience.

This was done as an exercise to know more about how a web app works.
