from flask_login import UserMixin, AnonymousUserMixin, current_user
from flask import url_for
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from flask import current_app, url_for
import os
import uuid
from authlib.integrations.sqla_oauth2 import (
    OAuth2ClientMixin,
    OAuth2AuthorizationCodeMixin,
    OAuth2TokenMixin,
)
from datetime import datetime
import time
from app import db, login_manager
from app.sse.views import push_message_to_redis
from werkzeug.exceptions import HTTPException
from werkzeug.security import gen_salt
from authlib.integrations.flask_oauth2 import current_token

class UnauthorizedOperation(HTTPException):
    code = 403

class OAuth2Client(db.Model, OAuth2ClientMixin):
    __tablename__ = 'oauth2_client'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    user = db.relationship('User')

    def has_user_consent(self):
        if OAuth2Token.query.filter_by(client_id = self.client_id).first():
            return True
        return False


class OAuth2AuthorizationCode(db.Model, OAuth2AuthorizationCodeMixin):
    __tablename__ = 'oauth2_code'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    user = db.relationship('User')


class OAuth2Token(db.Model, OAuth2TokenMixin):
    __tablename__ = 'oauth2_token'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    user = db.relationship('User')

    """    def is_refresh_token_active(self):
        if self.revoked:
            return False
        expires_at = self.issued_at + self.expires_in * 2
        return expires_at >= time.time() """

    def is_refresh_token_active(self):
        if OAuth2Client.query.filter_by(client_id = self.client_id).first():
            return True
        return False

class ApiDict(dict):
    """Defining a custom dict with some methods to convert some objects to dictionary."""
    def __init__(self):
        self["items"] = []
        self["message"] = ""
        self["links"] = {}
        self["links"]["help"] = url_for("api.get_help",_external = True)

    def message_to_dict(self,message):
        message_dict = {}
        message_dict["sender"] = message.sender.username if message.sender else "None"
        message_dict["message"] = message.content
        message_dict["time"] = message.timestamp
        return message_dict

    def conversation_to_dict(self,conversation,page,messages_per_page, return_page_link = False):
        conversation_dict = {}
        conversation_dict["links"] = {}
        conversation_dict["conversation_uuid"] = conversation.conversation_uuid
        conversation_dict["admin"] = conversation.admin.username
        conversation_dict["links"]["url"] = url_for("api.get_conversation",conversation_uuid=conversation.conversation_uuid,_external=True)
        conversation_dict["participants"] = \
                [user.username for user in conversation.users.all()]
        messages = conversation.messages.paginate(page, messages_per_page, False)

        conversation_dict["messages"] = \
                [self.message_to_dict(message) for message in messages.items]

        if messages.has_next and return_page_link:
            conversation_dict["links"]["next_page"] =  \
            url_for("api.get_conversation",conversation_uuid=conversation.conversation_uuid,_external=True,
                page=messages.next_num)
        if messages.has_prev and return_page_link:
            conversation_dict["links"]["previous_page"] = \
            url_for("api.get_conversation",conversation_uuid=conversation.conversation_uuid,_external=True,
                page=messages.prev_num) 

        conversation_dict["number_of_items"] = messages.total
        conversation_dict["number_of_pages"] = messages.pages
        conversation_dict["links"]["add_message"] = url_for("api.add_message",conversation_uuid = conversation.conversation_uuid,_external=True)
        return conversation_dict


class UserApiMixin():
    """Extends User class so it can handle some api functionality
       Exceptions are handled by the app error_handler."""

    def api_get_conversations(self,page,conversations_per_page,messages_per_page):
        """ Returns a dictionary containg a list of all conversations, including participants and the most recents messages.
        The number of message returned is defined by messages_per_page argument. """
        conversations = (
            Conversation.query.filter(Conversation.users.contains(self))
            .order_by(Conversation.timestamp.desc())
            ).paginate(page, conversations_per_page, False)

        api_data = ApiDict()
        for conversation in conversations.items:
            api_data["items"].append(api_data.conversation_to_dict(conversation,page=1,messages_per_page=messages_per_page))
            if conversations.has_next:
                api_data["links"]["next_page"] = url_for("api.get_conversations",page=conversations.next_num)
            if conversations.has_prev:
                api_data["links"]["previous_page"] = url_for("api.get_conversations",page=conversations.prev_num)
            api_data["number_of_items"] = conversations.total
            api_data["number_of_pages"] = conversations.pages
        return api_data


    def api_get_unread_messages(self,page,conversations_per_page):
        """ Returns a list of conversations which contains unread messages. Each message is
        represented as a dictionary. """
        conversation_users = (
            ConversationUsers.query.join(
            Conversation, Conversation.id == ConversationUsers.conversation_id
            ).filter(ConversationUsers.user_id == self.id,
            ConversationUsers.unread_messages > 0)
            ).paginate(page, conversations_per_page, False)

        api_data = ApiDict()
        if not conversation_users.items:
            api_data["message"] =  "You don'have any unread messages."
            return api_data

        for item in conversation_users.items:
            conversation = Conversation.query.get(item.conversation_id)
            api_data["items"].append(api_data.conversation_to_dict(conversation,page=1,
                messages_per_page = item.unread_messages))
            # Don't return the below if only one page
            if conversation_users.has_next:
                api_data["links"]["next_page"] = url_for("api.get_unread_messages",page=conversation_users.next_num) 
            if conversation_users.has_prev:
                api_data["links"]["previous_page"] = url_for("api.get_unread_messages",page=conversation_users.prev_num)         
            api_data["number_of_items"] = conversations_users.total
            api_data["number_of_pages"] = conversations_users.pages
        return api_data
    
    def api_get_conversation(self,conversation_uuid,page,messages_per_page):
        conversation = self.get_conversation_by_uuid(conversation_uuid) 

        api_data = ApiDict()
        api_data["items"].append(api_data.conversation_to_dict(conversation,page,messages_per_page,return_page_link=True))
        return api_data
    
    def api_set_about_me(self,content):
        self.about_me = content
        db.session.commit() 
        api_data = ApiDict()
        api_data["message"] =  "Status has been successfully updated"
        return api_data

    def api_add_message_to_conversation(self,conversation_uuid,message_content):
        conversation = self.get_conversation_by_uuid(conversation_uuid)
        message = Message(sender=self, content=message_content)
        self.add_message_to_conversation(conversation,message)
        push_message_to_redis(conversation,message)
        api_data = ApiDict()
        api_data["message"] = "Message has been successfully added to the conversation"
        return api_data

    def api_delete_conversation(self,conversation_uuid):
        conversation = self.get_conversation_by_uuid(conversation_uuid)
        self.delete_conversation(conversation)

        api_data = ApiDict()
        api_data["message"] = "Conversation has been successfully deleted."
        return api_data

    def api_add_users(self,conversation_uuid,username_list):
        conversation = self.get_conversation_by_uuid(conversation_uuid)
        self.add_users_to_conversation(conversation,username_list)

        api_data = ApiDict()
        api_data["message"] = "All users have been added to the conversation."
        return api_data

    def api_leave_conversation(self,conversation_uuid):
        conversation = self.get_conversation_by_uuid(conversation_uuid)
        self.leave_conversation(conversation)

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

    def __init__(self,admin):
        self.admin = admin
        self.users.append(admin)
        self.conversation_uuid = str(uuid.uuid4())
        db.session.commit()

    def increment_unread_messages(self):
        for user in self.users:
            q = ConversationUsers.query.filter_by(
                user_id=user.id, conversation_id=self.id
            ).first()
            q.unread_messages += 1
        db.session.commit()

    def reset_unread_messages(self,user):
        q = ConversationUsers.query.filter_by(
        user_id=user.id, conversation_id=self.id
        ).first_or_404()
        q.unread_messages = 0
        db.session.commit()

class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String())
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class OAuth2User():
    def create_oauth2_client(self,client_name,client_scope):
        client_id = gen_salt(24)
        client_id_issued_at = int(time.time())
        client = OAuth2Client(
        client_id=client_id,
        client_id_issued_at=client_id_issued_at,
        user_id=self.id,
        )

        client_metadata = {
            "client_name": client_name,
            "client_uri": url_for("main.conversations", _external=True),
            "grant_types": ["authorization_code","refresh_token"],
            "redirect_uris": [url_for("auth.get_code", _external=True)],
            "response_types": ["code"],
            "scope" : client_scope,
            "token_endpoint_auth_method": "client_secret_basic"
        }
        client.set_client_metadata(client_metadata)
        client.client_secret = gen_salt(48)
        db.session.add(client)
        db.session.commit()

    def get_oauth2_clients(self):
        clients = OAuth2Client.query.filter_by(user=self).all()
        return clients

    def delete_oauth2_client(self,client_id)):
        client = OAuth2Client.query.filter_by(client_id=client_id, user_id=self.id).first_or_404()
        tokens = OAuth2Token.query.filter_by(client_id=client_id).all()
        for token in tokens: 
            token.revoked = True
        db.session.delete(client)
        db.session.commit()

    def get_oauth2_client_from_code(self,code):
        client = OAuth2Client.query.join(OAuth2AuthorizationCode, \
             OAuth2Client.client_id==OAuth2AuthorizationCode.client_id) \
             .filter(OAuth2AuthorizationCode.code == code, OAuth2Client.user == current_user).first_or_404()
        return client


class User(db.Model, UserMixin, UserApiMixin, OAuth2User):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    password_hash = db.Column(db.String(100))
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

    def get_user_id(self):
        """ For OAuth compatibility """
        return self.id

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

    def add_message_to_conversation(self,conversation, message):
        if self in conversation.users:
            conversation.timestamp = datetime.utcnow()
            conversation.messages.append(message)
            # Add +1 to new message count for all users in the conversation
            conversation.increment_unread_messages()
            db.session.commit()
        else:
            raise UnauthorizedOperation(
                "Only users who are participants of a conversation can add message."
                )

    def get_conversation_by_uuid(self, conversation_uuid):
        conversation = (
            Conversation.query.filter(Conversation.users.contains(self)).
            filter_by(conversation_uuid=str(conversation_uuid)).first_or_404()
            )
        return conversation
    
    def delete_conversation(self,conversation):
        if conversation.admin == self:
            db.session.delete(self)
            db.session.commit()
        else:
            raise UnauthorizedOperation("Only the admin of a conversation can delete it.")

    def leave_conversation(self,conversation):
        """ When a user choose to leave a conversation it has to be removed from it.
        if admin left it is replaced with the user which belongs to the conversation for the longest time
        If not user left, then conversation is deleted."""
        if self in conversation.users:
            conversation.users.remove(self)
            if conversation.admin == self:
                try:
                    conversation.admin = conversation.users[0]
                except:
                    db.session.delete(conversation)
            db.session.commit()
        else:
            raise UnauthorizedOperation("Only a user which already belongs to a conversation can be removed from it.") 

    def add_users_to_conversation(self,conversation, username_list):
        if self  == conversation.admin:
            for username in username_list:
                user = User.query.filter_by(username=username).first()
                if user:
                    conversation.users.append(user)
                else:
                    raise UnauthorizedOpersation("User "+ user + " does not exist.")
            db.session.commit()
        else:
            raise UnauthorizedOperation("Only the admin of a conversation can add users.")
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


