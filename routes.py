from flask import render_template, redirect, url_for, flash, request
from flask_mail import Message
from ebookcreator import app, mail
from flask_login import current_user, login_required

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_email')
def send_email():
    msg = Message('Hello', sender='noreply@example.com', recipients=['user@example.com'])
    msg.body = 'This is a test email sent from a Flask application.'
    mail.send(msg)
    return 'Email sent!'

# Add your other routes here
