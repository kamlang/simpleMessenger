from flask_login import UserMixin, AnonymousUserMixin, current_user
from flask import url_for
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from flask import current_app, url_for
import os
import uuid
from datetime import datetime
from app import db, login_manager
from app.sse.views import push_message_to_redis
from werkzeug.exceptions import HTTPException

class UnauthorizedOperation(HTTPException):
    code = 403

class ApiDict(dict):
    """Defining a custom dict with some methods to convert some objects to dictionnary."""
    def __init__(self):
        self["items"] = []
        self["message"] = ""
        self["help"] = url_for("api.get_help")

    def message_to_dict(self,message):
        message_dict = {}
        message_dict["from"] = message.sender.username if message.sender else "None"
        message_dict["message"] = message.content
        message_dict["time"] = message.timestamp
        return message_dict

    def conversation_to_dict(self,conversation,message_number):
        conversation_dict = {}
        conversation_dict["conversation_uuid"] = conversation.conversation_uuid
        conversation_dict["participants"] = \
                [user.username for user in conversation.users.all()]
        conversation_dict["messages"] = \
                [self.message_to_dict(message) for message in conversation.messages.all( )[:message_number]]
        return conversation_dict


class UserApiMixin():
    """Extends User class so it can handle some api functionality
        Exceptions are handled by the app error_handler."""

    def get_api_key(self):
        self.api_key = str(uuid.uuid4())
        db.session.commit()
        api_data = ApiDict()
        api_data["items"].append({"API key": self.api_key})
        api_data["message"] = "You can know use your API key using Autorization header."
        return api_data

    def api_get_conversations(self,message_number):
        """ Return a list of all conversations, including participants and the most recent messages
        . The number of message returned if defined by message_number argument. """
        conversations = (
            Conversation.query.filter(Conversation.users.contains(self))
            .order_by(Conversation.timestamp.desc())
        )
        api_data = ApiDict()
        for conversation in conversations:
            api_data["items"].append(api_data.conversation_to_dict(conversation,message_number))
        return api_data


    def api_get_unread_messages(self):
        """ Return a list containing all the unread messages of a user. Each message is
        represented as a dictionary. Not really satisfied with that. """
        conversation_users = ConversationUsers.query.join(
            Conversation, Conversation.id == ConversationUsers.conversation_id
            ).filter(ConversationUsers.user_id == self.id,
            ConversationUsers.unread_messages > 0).all()
        api_data = ApiDict()
        if not conversation_users:
            api_data["message"] =  "You don'have any unread messages."
            return api_data

        for item in conversation_users:
            conversation = Conversation.query.get(item.conversation_id)
            # only get the the last nth unread messages
            api_data["items"].append(api_data.conversation_to_dict(conversation,item.unread_messages))
        return api_data
    
    def api_get_conversation(self,conversation_uuid,message_number):
        conversation = Conversation.get_conversation_by_uuid(conversation_uuid) 
        api_data = ApiDict()
        api_data["items"].append(api_data.conversation_to_dict(conversation,message_number))
        return api_data

    
    def api_set_about_me(self,content):
        self.about_me = content
        db.session.commit() 
        api_data = ApiDict()
        api_data["message"] =  "Status has been successfully updated"
        return api_data

    def api_add_message_to_conversation(self,conversation_uuid,message_content):
        conversation = Conversation.get_conversation_by_uuid(conversation_uuid)
        message = Message(content=message_content,sender_id=self.id)
        conversation.add_message(message)
        push_message_to_redis(conversation,message_content)
        api_data = ApiDict()
        api_data["message"] = "Message has been successfully added to the conversation"
        return api_data

    def api_delete_conversation(self,conversation_uuid):
        conversation = Conversation.get_conversation_by_uuid(conversation_uuid)
        conversation.delete()
        api_data = ApiDict()
        api_data["message"] = "Conversation has been successfully deleted."
        return api_data

    def api_add_users(self,conversation_uuid,username_list):
        conversation = Conversation.get_conversation_by_uuid(conversation_uuid)
        conversation.add_users(username_list)
        api_data = ApiDict()
        api_data["message"] = "All users have been added to the conversation."
        return api_data

    def api_leave_conversation(self,conversation_uuid):
        conversation = Conversation.get_conversation_by_uuid(conversation_uuid)
        conversation.remove_user()
        api_data = ApiDict()
        api_data["message"] = "You have successfully left the conversation"
        return api_data

class Role(db.Model):
    __tablename__ = "roles"
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(50), unique=True)


class UserRoles(db.Model):
    __tablename__ = "user_roles"
    id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey("users.id", ondelete="CASCADE"))
    role_id = db.Column(db.Integer(), db.ForeignKey("roles.id", ondelete="CASCADE"))


class ConversationUsers(db.Model):
    __tablename__ = "conversations_users"
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer(), db.ForeignKey("conversations.id", ondelete="CASCADE")
    )
    user_id = db.Column(db.Integer(), db.ForeignKey("users.id", ondelete="CASCADE"))
    unread_messages = db.Column(db.Integer(), default=0) # TODO: change to a better name


class ConversationMessages(db.Model):
    __tablename__ = "conversations_messages"
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(
        db.Integer(), db.ForeignKey("conversations.id", ondelete="CASCADE")
    )
    message_id = db.Column(
        db.Integer(), db.ForeignKey("messages.id", ondelete="CASCADE")
    )


class Conversation(db.Model):
    __tablename__ = "conversations"
    id = db.Column(db.Integer, primary_key=True)
    users = db.relationship("User", secondary="conversations_users", lazy="dynamic")
    messages = db.relationship(
        "Message",
        secondary="conversations_messages",
        order_by="desc(Message.timestamp)",
        lazy="dynamic",
        backref="belongs_to",
    )
    admin_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    conversation_uuid = db.Column(db.String(100), unique=True)

    def __init__(self):
        self.admin = current_user
        self.users.append(current_user)
        self.conversation_uuid = str(uuid.uuid4())
        db.session.commit()

    def delete(self):
        if current_user == self.admin:
            db.session.delete(self)
            db.session.commit()
        else:
            raise UnauthorizedOperation("Only the admin of a conversation can delete it.")

    @classmethod
    def get_conversation_by_uuid(cls, conversation_uuid):
        conversation = cls.query.filter_by(
            conversation_uuid=str(conversation_uuid)
        ).first_or_404()
        if current_user in conversation.users:
            return conversation
        raise UnauthorizedOperation("Only participants which belongs to a conversation can access it.")

    def remove_user(self):
        """ When a user choose to leave a conversation it has to be removed from it.
        if admin left it is replaced with the user which belongs to the conversation for the longest time
        If not user left, then conversation is deleted."""
        if current_user in self.users:
            self.users.remove(current_user)
            if self.admin == current_user:
                try:
                    self.admin = self.users[0]
                except:
                    db.session.delete(self)
            db.session.commit()
        else:
            raise UnauthorizedOperation("Only a user which already belongs to a conversation can be removed.") 


    def add_users(self, username_list):
        if current_user == self.admin:
            for username in username_list:
                user = User.query.filter_by(username=username).first()
                if user:
                    self.users.append(user)
                else:
                    raise UnauthorizedOpersation("User "+ user + " does not exist.")
            db.session.commit()
        else:
            raise UnauthorizedOperation("Only admin of a conversation can add users.")

    def _increment_unread_messages(self, user_list):
        for user in user_list:
            q = ConversationUsers.query.filter_by(
                user_id=user.id, conversation_id=self.id
            ).first()
            q.unread_messages += 1

    def reset_unread_messages(self):
        q = ConversationUsers.query.filter_by(
        user_id=current_user.id, conversation_id=self.id
        ).first_or_404()
        q.unread_messages = 0
        db.session.commit()

    def add_message(self, message):
        if current_user in self.users:
            self.timestamp = datetime.utcnow()
            self.messages.append(message)
            # Add +1 to new message count for all users in the conversation
            self._increment_unread_messages(self.users)
            db.session.commit()
        else:
            raise UnauthorizedOperation(
                "Only users which are participants of a conversation can add message."
            )


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String())
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model, UserMixin, UserApiMixin):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.String(100))
    api_key = db.Column(db.String(100),default=None)
    email = db.Column(db.String(155))
    roles = db.relationship("Role", secondary="user_roles")
    confirmed = db.Column(db.Boolean, default=False)
    about_me = db.Column(db.String(140))
    messages_sent = db.relationship(
        "Message", foreign_keys="Message.sender_id", backref="sender", lazy="dynamic"
        ) # TODO: change to a better name
    conversations = db.relationship(
        "Conversation",
        foreign_keys="Conversation.admin_id",
        backref="admin",
        lazy="dynamic",
    )
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    _avatar_hash = db.Column(db.String(32), default="default.png")

    def __init__(self,username,password,email,role="User"):
        self.username = username
        self.password = password
        self.email = email
        self.role = role

    def get_number_of_unread_messages(self, conversation):
        q = ConversationUsers.query.filter_by(
            user_id=self.id, conversation_id=conversation.id
        ).first()
        return q.unread_messages

    def get_all_conversations(self, page):
        conversations = (
            Conversation.query.filter(Conversation.users.contains(self))
            .order_by(Conversation.timestamp.desc())
            .paginate(page, current_app.config["POSTS_PER_PAGE"], False)
        )
        return conversations
    
    
    @property
    def password(self):
        raise AttributeError("Password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def role(self):
        pass

    @role.setter
    def role(self, role):
        try:
            self.roles.append(Role.query.filter_by(name=role).first())
        except:
            raise Exception("The role specified does not exist.")

    def is_role(self, role_name):
        for role in self.roles:
            if role.name == role_name:
                return True
        return False

    @property
    def avatar(self):
        return self._avatar_hash

    @avatar.setter
    def avatar(self, avatar_data):

        import hashlib
        from PIL import Image

        try:
            image = Image.open(avatar_data)
            data = list(image.getdata())
            image2 = Image.new(image.mode, image.size)
            image2.putdata(data)
            filename = hashlib.md5(self.username.encode())
            self._avatar_hash = filename.hexdigest()
            image2.thumbnail((128, 128))
            image2.save(
                os.path.join(current_app.config["UPLOAD_FOLDER"], filename.hexdigest()),
                format="png",
            )
        except:
            exception = UnauthorizedOperation("Image file is not valid.")
            exception.code = 400
            raise exception


class AnonymousUser(AnonymousUserMixin):
    # To avoid error when calling some methods as unauthenticated user.
    def is_role(self, role_name):
        return False
