from flask_login import UserMixin, AnonymousUserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from flask import current_app
import os
from datetime import datetime
from app import db,login_manager

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
    converation_id = db.Column(
        db.Integer(), db.ForeignKey("conversations.id", ondelete="CASCADE")
    )
    user_id = db.Column(db.Integer(), db.ForeignKey("users.id", ondelete="CASCADE"))
    unread_messages = db.Column(db.Integer(),default=0)



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


    def add_users(self,username_list):
        if current_user == self.admin: 
            for username in username_list:
                user = User.query.filter_by(username=username).first()
                self.users.append(user)
            db.session.commit()
        else: 
            raise Exception("Only admin of a conversation can add users.")

    def increment_unread_messages(self,user_list):
        for user in user_list:
            q = ConversationUsers.query.filter_by(user_id=user.id,converation_id=self.id).first()
            q.unread_messages +=1

    def reset_unread_messages(self,user):
        q=ConversationUsers.query.filter_by(user_id=user.id,converation_id=self.id).first()
        q.unread_messages = 0
        db.session.commit()
     
    def add_message(self,message):
        if current_user in self.users:
            self.timestamp = datetime.utcnow()
            self.messages.append(message)
            ## Add +1 to new message count for all users in the conversation
            self.increment_unread_messages(self.users)
            db.session.commit()
        else: 
            raise Exception("Only user which are participants of a conversation can add message.")

    @staticmethod 
    def create_new(admin):
        conversation = Conversation()
        conversation.admin = admin
        conversation.users.append(admin)
        db.session.commit()
        return conversation


class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String())
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class User(db.Model, UserMixin):
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
    )
    conversations = db.relationship(
        "Conversation",
        foreign_keys="Conversation.admin_id",
        backref="admin",
        lazy="dynamic",
    )
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    _avatar_hash = db.Column(db.String(32),default="default.png")

    def number_of_unread_messages(self,conversation):
        q=ConversationUsers.query.filter_by(user_id=self.id,converation_id=conversation.id).first()
        return q.unread_messages

    def is_allowed_to_access(self,conversation):
        allowed_users = conversation.users.all()
        if self in allowed_users:
            return True
        return False

    def get_conversations(self, page):
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
            raise AttributeError("The role specified do not exists")

    def is_role(self, role_name):
        for role in self.roles:
            if role.name == role_name:
                return True
        return False

    @property
    def avatar(self):
        return self._avatar_hash

    @avatar.setter
    def avatar(self,avatar_data):

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
            flash("Please provide a valid image file")

class AnonymousUser(AnonymousUserMixin):
    def is_role(self, role):
        return False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)
