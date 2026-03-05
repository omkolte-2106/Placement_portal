from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    role = db.Column(db.String(20))  
    department = db.Column(db.String(50))
    cgpa = db.Column(db.Float)
    contact = db.Column(db.String(15))
    resume = db.Column(db.String(200))
    account_status = db.Column(db.String(20), default="Active")
    
    def get_id(self):
        return f"user_{self.id}"


class Company(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(100))
    hr_name = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(200))
    website = db.Column(db.String(100))
    industry = db.Column(db.String(50))
    approval_status = db.Column(db.String(20), default="Pending")
    account_status = db.Column(db.String(20), default="Active")
    drives = db.relationship('Drive', backref='company', lazy=True)

    def get_id(self):
        return f"company_{self.id}"


class Drive(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"))
    job_role = db.Column(db.String(100))
    description = db.Column(db.Text)
    package = db.Column(db.String(50))
    location = db.Column(db.String(100))
    eligibility = db.Column(db.String(100))
    drive_type = db.Column(db.String(50))
    deadline = db.Column(db.Date)
    approval_status = db.Column(db.String(20), default="Pending")
    drive_status = db.Column(db.String(20), default="Open")


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    drive_id = db.Column(db.Integer, db.ForeignKey("drive.id"))
    date_applied = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default="Applied")
