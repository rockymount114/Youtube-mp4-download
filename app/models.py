from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(500), nullable=False)

class Meeting(db.Model):
    __tablename__ = 'meetings'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(500), nullable=False)
    meeting_date = db.Column(db.Date, nullable=False)
    audio_file = db.Column(db.String(1000), nullable=True)
    transcript = db.Column(db.Text, nullable=True)
    summary = db.Column(db.Text, nullable=True)
    action_items = db.Column(db.JSON, nullable=True)
    motions = db.Column(db.JSON, nullable=True)
    budget_notes = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(100), default='Pending') # Pending, Transcribing, Transcribed, Analyzing, Analyzed, Error
    progress = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Meeting {self.title}>'
