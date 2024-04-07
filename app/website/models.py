from . import db 
from flask_login import UserMixin
from sqlalchemy.sql import func
import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.String(10000))
    date = db.Column(db.DateTime(timezone=True), default=func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    notes = db.relationship('Note')

class WebResource(db.Model):
    __tablename__ = 'webresource'  # Явно указываем имя таблицы
    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4()))
    url = db.Column(db.String(2048), nullable=False)
    protocol = db.Column(db.String(10), nullable=False)
    domain = db.Column(db.String(255), nullable=False)
    domain_zone = db.Column(db.String(10), nullable=False)
    path = db.Column(db.String(255), nullable=True)
    query_parameters = db.Column(db.JSON, nullable=True)
    is_available = db.Column(db.Boolean, default=True)
    last_status_code = db.Column(db.Integer, nullable=True)
    screenshot_path = db.Column(db.String(2048), nullable=True)
    last_checked = db.Column(db.DateTime, nullable=True, default=datetime.now)

class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    resource_id = db.Column(db.Integer, db.ForeignKey('webresource.id'), nullable=False)
    resource = db.relationship('WebResource', backref=db.backref('news', lazy=True))
