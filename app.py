from flask import Flask, render_template, redirect, url_for, request, flash
from models import db, User, Company, Drive, Application
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from config import Config


app = Flask(__name__)


# ---------------- CONFIGURATION ---------------- #

app.config.from_object(Config)

db.init_app(app)


# ---------------- LOGIN MANAGER ---------------- #

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


# ---------------- USER LOADER ---------------- #

@login_manager.user_loader
def load_user(user_id):

    if user_id.startswith("user_"):
        return db.session.get(User, int(user_id.split("_")[1]))

    if user_id.startswith("company_"):
        return db.session.get(Company, int(user_id.split("_")[1]))

    return None


# ---------------- DATABASE INIT ---------------- #

with app.app_context():

    db.create_all()

    admin = User.query.filter_by(role="admin").first()

    if not admin:

        admin = User(
            full_name="Placement Admin",
            email="admin123@gmail.com",
            password=generate_password_hash("admin123"),
            role="admin"
        )

        db.session.add(admin)
        db.session.commit()


# ---------------- HOME ---------------- #

@app.route("/")
def home():
    return redirect(url_for("login"))


# ---------------- LOGIN ---------------- #

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            login_user(user)
            return redirect(url_for("dashboard"))

        company = Company.query.filter_by(email=email).first()

        if company and company.approval_status == "Approved":

            if check_password_hash(company.password, password):

                login_user(company)
                return redirect(url_for("company_dashboard", id=company.id))

        flash("Invalid login credentials")

    return render_template("login.html")


# ---------------- LOGOUT ---------------- #

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect(url_for("login"))


# ---------------- DASHBOARD ---------------- #

@app.route("/dashboard")
@login_required
def dashboard():

    if isinstance(current_user, Company):

        return redirect(url_for("company_dashboard", id=current_user.id))

    if current_user.role == "admin":

        students = User.query.filter_by(role="student").count()
        companies = Company.query.count()
        drives = Drive.query.count()
        applications = Application.query.count()

        return render_template(
            "admin_dashboard.html",
            students=students,
            companies=companies,
            drives=drives,
            applications=applications
        )

    drives = Drive.query.filter_by(
        approval_status="Approved",
        drive_status="Open"
    ).all()

    my_apps = Application.query.filter_by(
        student_id=current_user.id
    ).all()

    applied_ids = [a.drive_id for a in my_apps]

    return render_template(
        "student_dashboard.html",
        drives=drives,
        applied_drive_ids=applied_ids
    )


# ---------------- REGISTER STUDENT ---------------- #

@app.route("/register_student", methods=["GET", "POST"])
def register_student():

    if request.method == "POST":

        existing = User.query.filter_by(email=request.form["email"]).first()

        if existing:
            flash("Email already exists")
            return redirect(url_for("register_student"))

        student = User(
            full_name=request.form["name"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            role="student",
            department=request.form["department"],
            cgpa=request.form["cgpa"],
            contact=request.form["contact"]
        )

        db.session.add(student)
        db.session.commit()

        flash("Student registered successfully")

        return redirect(url_for("login"))

    return render_template("register_student.html")


# ---------------- REGISTER COMPANY ---------------- #

@app.route("/register_company", methods=["GET", "POST"])
def register_company():

    if request.method == "POST":

        company = Company(
            company_name=request.form["company_name"],
            hr_name=request.form["hr_name"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            website=request.form["website"],
            industry=request.form["industry"]
        )

        db.session.add(company)
        db.session.commit()

        flash("Company registered. Waiting for admin approval.")

        return redirect(url_for("login"))

    return render_template("register_company.html")


# ---------------- ADMIN COMPANIES ---------------- #

@app.route("/admin_companies")
@login_required
def admin_companies():

    if current_user.role != "admin":
        return redirect(url_for("dashboard"))

    companies = Company.query.all()

    return render_template("admin_companies.html", companies=companies)


# ---------------- APPROVE COMPANY ---------------- #

@app.route("/approve_company/<int:id>")
@login_required
def approve_company(id):

    company = db.session.get(Company, id)
    if not company:
        return redirect(url_for("admin_companies"))

    company.approval_status = "Approved"

    db.session.commit()

    flash("Company approved")

    return redirect(url_for("admin_companies"))


# ---------------- ADMIN DRIVES ---------------- #

@app.route("/admin_drives")
@login_required
def admin_drives():

    if current_user.role != "admin":
        return redirect(url_for("dashboard"))

    drives = Drive.query.all()

    return render_template("admin_drives.html", drives=drives)


# ---------------- APPROVE DRIVE ---------------- #

@app.route("/approve_drive/<int:id>")
@login_required
def approve_drive(id):

    drive = db.session.get(Drive, id)
    if not drive:
        return redirect(url_for("admin_drives"))

    drive.approval_status = "Approved"
    drive.drive_status = "Open"

    db.session.commit()

    flash("Drive approved")

    return redirect(url_for("admin_drives"))


# ---------------- COMPANY DASHBOARD ---------------- #

@app.route("/company_dashboard/<int:id>")
@login_required
def company_dashboard(id):

    if not isinstance(current_user, Company):
        return redirect(url_for("dashboard"))

    drives = Drive.query.filter_by(company_id=id).all()

    return render_template(
    "company_dashboard.html",
    drives=drives,
    company=current_user
)



# ---------------- CREATE DRIVE ---------------- #

@app.route("/create_drive/<int:company_id>", methods=["GET", "POST"])
@login_required
def create_drive(company_id):

    if not isinstance(current_user, Company) or current_user.id != company_id:
        flash("Unauthorized action")
        return redirect(url_for("dashboard"))

    if request.method == "POST":

        drive = Drive(
            company_id=company_id,
            job_role=request.form["job_role"],
            description=request.form["description"],
            package=request.form["package"],
            location=request.form["location"],
            eligibility=request.form["eligibility"],
            drive_type=request.form["drive_type"],
            deadline=datetime.strptime(request.form["deadline"], "%Y-%m-%d").date()
        )

        db.session.add(drive)
        db.session.commit()

        flash("Drive submitted for approval")

        return redirect(url_for("company_dashboard", id=company_id))

    return render_template("create_drive.html")


# ---------------- APPLY DRIVE ---------------- #

@app.route("/apply/<int:drive_id>")
@login_required
def apply(drive_id):

    if current_user.role != "student":
        return redirect(url_for("dashboard"))

    existing = Application.query.filter_by(
        student_id=current_user.id,
        drive_id=drive_id
    ).first()

    if existing:
        flash("Already applied")
        return redirect(url_for("dashboard"))

    application = Application(
        student_id=current_user.id,
        drive_id=drive_id
    )

    db.session.add(application)
    db.session.commit()

    flash("Application submitted")

    return redirect(url_for("dashboard"))


# ---------------- STUDENT APPLICATIONS ---------------- #

@app.route("/my_applications")
@login_required
def my_applications():

    apps = Application.query.filter_by(
        student_id=current_user.id
    ).all()

    return render_template("my_applications.html", applications=apps)


# ---------------- SHORTLIST ---------------- #

@app.route("/shortlist/<int:app_id>")
@login_required
def shortlist(app_id):

    if not isinstance(current_user, Company):
        return redirect(url_for("dashboard"))

    application = db.session.get(Application, app_id)
    if not application:
        return redirect(request.referrer)

    application.status = "Shortlisted"

    db.session.commit()

    flash("Student shortlisted")

    return redirect(request.referrer)



# ---------------- COMPANY APPLICATIONS ---------------- #

@app.route("/company_applications/<int:drive_id>")
@login_required
def company_applications(drive_id):

    if not isinstance(current_user, Company):
        return redirect(url_for("dashboard"))

    applications = Application.query.filter_by(
        drive_id=drive_id
    ).all()

    return render_template(
        "company_applications.html",
        applications=applications
    )

# ---------------- REJECT DRIVE ---------------- #

@app.route("/reject_drive/<int:id>")
@login_required
def reject_drive(id):

    if current_user.role != "admin":
        return redirect(url_for("dashboard"))

    drive = db.session.get(Drive, id)
    if not drive:
        return redirect(url_for("admin_drives"))

    drive.approval_status = "Rejected"

    db.session.commit()

    flash("Drive rejected")

    return redirect(url_for("admin_drives"))


# ---------------- REJECT COMPANY ---------------- #

@app.route("/reject_company/<int:id>")
@login_required
def reject_company(id):

    if current_user.role != "admin":
        return redirect(url_for("dashboard"))

    company = db.session.get(Company, id)
    if not company:
        return redirect(url_for("admin_companies"))

    company.approval_status = "Rejected"

    db.session.commit()

    flash("Company rejected")

    return redirect(url_for("admin_companies"))


# ---------------- ADMIN STUDENTS ---------------- #

@app.route("/admin_students")
@login_required
def admin_students():

    if current_user.role != "admin":
        return redirect(url_for("dashboard"))

    students = User.query.filter_by(role="student").all()

    return render_template(
        "admin_students.html",
        students=students
    )


# ---------------- RUN SERVER ---------------- #

if __name__ == "__main__":

    app.run(debug=True)
