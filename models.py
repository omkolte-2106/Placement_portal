from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()



class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    full_name = db.Column(db.String(120), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(20))   

    department = db.Column(db.String(100))

    cgpa = db.Column(db.Float)

    contact = db.Column(db.String(20))

    def get_id(self):
        return f"user_{self.id}"




class Company(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    company_name = db.Column(db.String(150), nullable=False)

    hr_name = db.Column(db.String(120))

    email = db.Column(db.String(120), unique=True)

    password = db.Column(db.String(200))

    website = db.Column(db.String(200))

    industry = db.Column(db.String(100))

    approval_status = db.Column(db.String(20), default="Pending")

    blacklisted = db.Column(db.Boolean, default=False)

    role = "company"

    def get_id(self):
        return f"company_{self.id}"




class Drive(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    company_id = db.Column(db.Integer, db.ForeignKey("company.id"))

    job_role = db.Column(db.String(120))

    description = db.Column(db.Text)

    package = db.Column(db.String(50))

    location = db.Column(db.String(120))

    eligibility = db.Column(db.String(100))

    drive_type = db.Column(db.String(50))

    deadline = db.Column(db.Date)

    approval_status = db.Column(db.String(20), default="Pending")

    drive_status = db.Column(db.String(20), default="Closed")

    company = db.relationship('Company', backref='drives')




class Application(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    student_id = db.Column(db.Integer, db.ForeignKey("user.id"))

    drive_id = db.Column(db.Integer, db.ForeignKey("drive.id"))

    status = db.Column(db.String(50), default="Applied")

    student = db.relationship('User', backref='applications')

    drive = db.relationship('Drive', backref='applications')
