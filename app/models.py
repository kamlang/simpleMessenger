from flask_login import UserMixin, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash
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
    avatar_name = db.Column(db.String(32),default="default.png")

    def create_conversation(self, usernames, content):
        c = Conversation()
        m = Message(sender=self, content=content)
        c.users.append(self)
        c.messages.append(m)
        for username in usernames:  ### validation is done in the form
            user = User.query.filter_by(username=username).first()
            c.users.append(user)
        self.conversations.append(c)
        db.session.commit()
        return c.id

    def add_users_conversation(self, conversation_id, usernames):
        conversation = Conversation.query.get(conversation_id)
        if self.id == conversation.admin.id:
            for username in usernames:  ### validation is done in the form
                user = User.query.filter_by(username=username).first()
                if not user in conversation.users.all():
                    conversation.users.append(user)
                    db.session.commit()
        else:
            raise Exception("Only admin of a conversation can add a user.")


    def add_message_conversation(self, conversation_id, content):
        conversation = Conversation.query.get(conversation_id)
        if self in conversation.users.all():
            message = Message(sender=self, content=content)
            conversation.timestamp = datetime.utcnow()
            conversation.messages.append(message)
            db.session.commit()
        else:
            raise Exception("Only participant of a conversation can add a message.")

    def get_conversation(self, conversation_id):
        conversation = Conversation.query.get(conversation_id)
        users = conversation.users.all()
        if self in users:
            return conversation
        return None

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

    def is_role(self, role):
        for r in self.roles:
            if r.name == role:
                return True
        return False

    def last_seen_clean(self):
        cleantime = self.last_seen.strftime("%A %d-%b-%Y, %H:%M")
        return cleantime

    def set_avatar(self, avatar_data):
        import hashlib
        from PIL import Image

        try:
            image = Image.open(avatar_data)
            data = list(image.getdata())
            image2 = Image.new(image.mode, image.size)
            image2.putdata(data)
            filename = hashlib.md5(self.username.encode())
            self.avatar_name = filename.hexdigest()
            image2.thumbnail((128, 128))
            image2.save(
                os.path.join(current_app.config["UPLOAD_FOLDER"], filename.hexdigest()),
                format="png",
            )
        except:
            flash("Please provide a valid image file")

    def get_avatar_path(self):
        return os.path.join("../static/avatars/", str(self.avatar_name))


class AnonymousUser(AnonymousUserMixin):
    def is_role(self, role):
        return False

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)
