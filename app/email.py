from . import mail
from threading import Thread
from flask import current_app, render_template
from flask_mail import Message

def sendAsyncEmail(app, msg):
      with app.app_context():
        mail.send(msg)

def sendEmailToAdmin(subject,template, **kwargs):
    msg = Message(app.config['APP_MAIL_SUBJECT_PREFIX'] + subject, recipients=[app.config['APP_MAIL_ADMIN']],
                  sender=app.config['USER_EMAIL_SENDER_EMAIL'])
#    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template + '.html', **kwargs)
    thr = Thread(target=sendAsyncEmail, args=(app, msg))
    thr.start()
    return thr
