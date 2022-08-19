# simpleMessenger

This is a small chatting app built with Python Flask.
It uses SSE and Redis to implement instant messaging system and also has a small RestFullAPI.

It has full registration and login support and has the possibility to create conversation with multiple users.
The frontend is build using Bootstrap as well as a bit of raw javascript to manage SSE connections.

Flask-SQLAlchemy is used to interact with the database.

As an exercise, an OAuth server has also be implemented to manage API authorization, it's overkilled but was done for the learning experience.
