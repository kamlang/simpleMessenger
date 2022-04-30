from flask import stream_with_context,Response
from app import red
from app.sse import sse
from flask_login import current_user, login_required

def push_message_to_redis(conversation,message):
    """Each time a user post a message in a conversation it's also pushed to the redis channel
    of each participants."""

    users = conversation.users.all()
    for user in users:
        participants = " ".join(
            ["Me" if user == user_ else user_.username for user_ in users]
        )
        redis_message = {
            "event": "new_message",
            "from": message.sender.username,
            "avatar_name": message.sender.avatar,
            "conversation_uuid": conversation.conversation_uuid,
            "content": message.content,
            "participants": participants,
            "unread_messages": user.get_number_of_unread_messages(conversation),
        }
        print(redis_message)
        try:
            red.publish(user.username, str(redis_message))
        except:
            raise Exception("Pushing message to redis failed.")

@stream_with_context
def event_stream(username):
    pubsub = red.pubsub()
    pubsub.subscribe(username)
    for message in pubsub.listen():
        if message["type"] == "message":
            yield "retry:5000\ndata: %s\n\n" % message["data"].decode("utf-8")

@sse.route("/<username>")
@login_required
def stream(username):
    if current_user.username == username:
        response = Response(event_stream(username), 
                content_type="text/event-stream; charset=utf-8")
        return response
    abort(403)
