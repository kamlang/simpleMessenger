from flask import stream_with_context,Response
from app import red
from app.sse import sse
from flask_login import current_user, login_required

def push_message_to_redis(conversation, content):
    """Each time a user post a message in a conversation it's also pushed to the redis channel
    of each participants."""
    users = conversation.users.all()
    for user in users:
        participants = " ".join(
            ["Me" if user == user_ else user_.username for user_ in users]
        )
        redis_message = {
            "event": "new_message",
            "from": current_user.username,
            "avatar_name": current_user.avatar,
            "conversation_uuid": conversation.conversation_uuid,
            "content": content,
            "participants": participants,
            "unread_messages": user.get_number_of_unread_messages(conversation),
        }
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
            yield "retry:15000\ndata: %s\n\n" % message["data"].decode("utf-8")

@sse.route("/<username>")
@login_required
def stream(username):
    if current_user.username == username:
        response = Response(event_stream(username), mimetype="text/event-stream")
        # Add custom headers to fix event stream timeout with nginx
        response.headers["X-Accel-Buffering"] = "no"
        response.headers["Connection"] = "keep-alive"
        return response
    abort(403)
