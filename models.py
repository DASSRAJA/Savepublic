from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    trial_start_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    trial_end_date = db.Column(db.DateTime, nullable=False)

    def __init__(self, username, email, password, trial_days=14):
        self.username = username
        self.email = email
        self.password = password
        self.trial_start_date = datetime.utcnow()
        self.trial_end_date = self.trial_start_date + timedelta(days=trial_days)
