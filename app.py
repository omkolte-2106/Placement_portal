from flask import Flask, render_template, redirect, url_for, request, flash
from controllers import db, User, Company, Drive, Application
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)

# ---------------- CONFIG ---------------- #

class Config:
    SECRET_KEY = "placement_secret_key"
    SQLALCHEMY_DATABASE_URI = "sqlite:///placement.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

app.config.from_object(Config)
db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)

# ---------------- USER LOADER ---------------- #

@login_manager.user_loader
def load_user(user_id):
    if user_id.startswith("user_"):
        return User.query.get(int(user_id.split("_")[1]))
    elif user_id.startswith("company_"):
        return Company.query.get(int(user_id.split("_")[1]))
    return None

# ---------------- DATABASE INIT ---------------- #

with app.app_context():
    db.create_all()

    # Create admin if not exists
    if not User.query.filter_by(role="admin").first():
        admin = User(
            full_name="Placement Admin",
            email="admin123@gmail.com",
            password=generate_password_hash("admin123"),
            role="admin"
        )
        db.session.add(admin)
        db.session.commit()

# ---------------- ROUTES ---------------- #

@app.route("/")
def index():
    return redirect(url_for("login"))

# -------- REGISTER STUDENT -------- #

@app.route("/register_student", methods=["GET", "POST"])
def register_student():
    if request.method == "POST":
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
        flash("Registration Successful")
        return redirect(url_for("login"))

    return render_template("register_student.html")

# -------- REGISTER COMPANY -------- #

@app.route("/register_company", methods=["GET", "POST"])
def register_company():
    if request.method == "POST":
        company = Company(
            company_name=request.form["company_name"],
            hr_name=request.form["hr_name"],
            email=request.form["email"],
            password=generate_password_hash(request.form["password"]),
            website=request.form["website"],
            industry=request.form["industry"],
            approval_status="Approved"  # Auto approve company for now
        )
        db.session.add(company)
        db.session.commit()
        flash("Company registered successfully.")
        return redirect(url_for("login"))

    return render_template("register_company.html")

# -------- LOGIN -------- #

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
        if company and check_password_hash(company.password, password):
            login_user(company)
            return redirect(url_for("company_dashboard", id=company.id))

        flash("Invalid credentials")

    return render_template("login.html")

# -------- LOGOUT -------- #

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

# -------- DASHBOARD -------- #

@app.route("/dashboard")
@login_required
def dashboard():

    # Company redirect
    if current_user.__class__.__name__ == "Company":
        return redirect(url_for("company_dashboard", id=current_user.id))

    # Admin dashboard
    if current_user.role == "admin":
        total_students = User.query.filter_by(role="student").count()
        total_companies = Company.query.count()
        total_drives = Drive.query.count()
        total_applications = Application.query.count()

        drives = Drive.query.all()

        return render_template(
        "admin_dashboard.html",
         students=User.query.filter_by(role="student").count(),
         companies=Company.query.count(),
         drives=Drive.query.count(),
          applications=Application.query.count(),
        drives_list=drives
        )

    # Student dashboard
    if current_user.role == "student":

     drives = Drive.query.filter_by(
        approval_status="Approved",
        drive_status="Open"
    ).all()

    my_applications = Application.query.filter_by(
        student_id=current_user.id
    ).all()

    applied_drive_ids = [app.drive_id for app in my_applications]

    return render_template(
        "student_dashboard.html",
        drives=drives,
        applied_drive_ids=applied_drive_ids
    )


# -------- APPLY -------- #

@app.route("/apply/<int:drive_id>")
@login_required
def apply(drive_id):

    existing = Application.query.filter_by(
        student_id=current_user.id,
        drive_id=drive_id
    ).first()

    if existing:
        flash("Already Applied!")
        return redirect(url_for("dashboard"))

    application = Application(
        student_id=current_user.id,
        drive_id=drive_id
    )

    db.session.add(application)
    db.session.commit()

    flash("Application Submitted")
    return redirect(url_for("dashboard"))

# -------- MY APPLICATIONS -------- #

@app.route("/my_applications")
@login_required
def my_applications():
    if getattr(current_user, "role", None) != "student":
        return redirect(url_for("dashboard"))

    applications = Application.query.filter_by(student_id=current_user.id).order_by(Application.date_applied.desc()).all()
    return render_template("student_applications.html", applications=applications)

# -------- COMPANY DASHBOARD -------- #

@app.route("/company_dashboard/<int:id>")
@login_required
def company_dashboard(id):
    company = Company.query.get_or_404(id)
    drives = Drive.query.filter_by(company_id=id).all()

    return render_template(
        "company_dashboard.html",
        company=company,
        drives=drives
    )

# -------- CREATE DRIVE (AUTO APPROVED) -------- #

@app.route("/create_drive/<int:company_id>", methods=["GET", "POST"])
@login_required
def create_drive(company_id):

    company = Company.query.get_or_404(company_id)

    if request.method == "POST":
        drive = Drive(
            company_id=company.id,
            job_role=request.form["job_role"],
            description=request.form["description"],
            package=request.form["package"],
            location=request.form["location"],
            eligibility=request.form["eligibility"],
            drive_type=request.form["drive_type"],
            deadline=datetime.strptime(request.form["deadline"], "%Y-%m-%d"),
            approval_status="Approved",   # Auto approved
            drive_status="Open"           # Auto open
        )

        db.session.add(drive)
        db.session.commit()

        flash("Drive created successfully.")
        return redirect(url_for("company_dashboard", id=company.id))

    return render_template("create_drive.html", company=company)

# -------- APPROVE DRIVE (If needed later) -------- #

@app.route("/approve_drive/<int:id>")
@login_required
def approve_drive(id):

    if current_user.role != "admin":
        return redirect(url_for("dashboard"))

    drive = Drive.query.get_or_404(id)
    drive.approval_status = "Approved"
    db.session.commit()

    flash("Drive Approved Successfully")
    return redirect(url_for("dashboard"))




@app.route("/admin_drives")
@login_required
def admin_drives():

    if current_user.role != "admin":
        return redirect(url_for("dashboard"))

    drives = Drive.query.all()
    return render_template("admin_drives.html", drives=drives)

@app.route("/admin_companies")
@login_required
def admin_companies():

    if getattr(current_user, "role", None) != "admin":
        return redirect(url_for("dashboard"))

    companies = Company.query.all()
    return render_template("admin_companies.html", companies=companies)


# -------- ERROR HANDLER -------- #

@app.errorhandler(Exception)
def handle_exception(e):
    return f"Error occurred: {str(e)}", 500

# -------- RUN -------- #

if __name__ == "__main__":
    app.run(debug=True)
