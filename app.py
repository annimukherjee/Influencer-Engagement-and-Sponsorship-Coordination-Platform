from flask import Flask, request, redirect, url_for, render_template, flash, session
from flask_sqlalchemy import SQLAlchemy
from models import db, User, Sponsor, Influencer
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///influencer_platform.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "anniop"  # Change this to a random secret key

db.init_app(app)

# Create the database tables
with app.app_context():
    db.create_all()


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html")


# ------------------------------------------------------------
# ---------------------- ADMIN ROUTES ------------------------
# ------------------------------------------------------------


@app.route("/login_admin", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("admin_email")
        password = request.form.get("admin_password")

        user = User.query.filter_by(email=email, role="admin").first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["role"] = "admin"
            flash("Logged in successfully as admin.", category="success")
            return redirect(url_for("admin_dashboard"))
            # return redirect(url_for("sample_dashboard"))
        else:
            flash("Invalid email or password for admin.",  category="danger")

    return render_template("login_admin.html")


@app.route("/login_influencer", methods=["GET", "POST"])
def login_influencer():
    if request.method == "POST":
        email = request.form.get("influencer_email")
        password = request.form.get("influencer_password")

        user = User.query.filter_by(email=email, role="influencer").first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["role"] = "influencer"
            flash("Logged in successfully as influencer.",  category="success")
            return redirect(url_for("influencer_dashboard"))
        else:
            flash("Invalid email or password for influencer.",  category="danger")

    return render_template("login_influencer.html")


@app.route("/register_influencer", methods=["GET", "POST"])
def register_influencer():
    if request.method == "POST":
        username = request.form.get("influencer_username")
        email = request.form.get("influencer_email")
        password = request.form.get("influencer_password")
        full_name = request.form.get("influencer_name")
        platforms = request.form.getlist('platform')
        platforms_str = ','.join(platforms)
        niche = request.form.get("influencer_niche")
        reach = request.form.get("influencer_reach")

        print("Received data in backend: ", username, email, password, full_name, platforms, niche, reach)

        # Check if any required field is empty
        if not all([username, email, password, full_name]):
            flash("All fields are required. Please fill in all the information.",  category="info")
            return redirect(url_for("register_influencer"))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please use a different email.",  category="danger")
            return redirect(url_for("register_influencer"))

        new_user = User(username=username, email=email, role="influencer")
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        new_influencer = Influencer(user_id=new_user.id, name=full_name, niche=niche, reach=reach, category=platforms_str)
        db.session.add(new_influencer)
        db.session.commit()

        flash("Registration successful. Please log in.",  category="success")
        return redirect(url_for("login_influencer"))

    return render_template("register_influencer.html")




# --------------------------------------------------------------------------------
# ==============  SPONSOR ROUTES  BGN ============================================
# --------------------------------------------------------------------------------



@app.route("/login_sponsor", methods=["GET", "POST"])
def login_sponsor():
    if request.method == "POST":
        email = request.form.get("sponsor_email")
        password = request.form.get("sponsor_password")

        user = User.query.filter_by(email=email, role="sponsor").first()
        if user and user.check_password(password):
            session["user_id"] = user.id
            session["role"] = "sponsor"
            flash("Logged in successfully as sponsor.",  category="success")
            return redirect(url_for("sponsor_dashboard"))
        else:
            flash("Invalid email or password for sponsor.",  category="danger")

    return render_template("login_sponsor.html")


@app.route("/register_sponsor", methods=["GET", "POST"])
def register_sponsor():
    if request.method == "POST":
        username = request.form.get("sponsor_username")
        email = request.form.get("sponsor_email")
        password = request.form.get("sponsor_password")
        company_name = request.form.get("sponsor_name")
        industry = request.form.get("sponsor_industry")
        budget = request.form.get("sponsor_budget")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered. Please use a different email.", category="danger")
            return redirect(url_for("register_sponsor"))

        new_user = User(username=username, email=email, role="sponsor")
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        new_sponsor = Sponsor(
            user_id=new_user.id, name=company_name, industry=industry, budget=budget
        )
        db.session.add(new_sponsor)
        db.session.commit()

        flash("Registration successful. Please log in.",  category="success")
        return redirect(url_for("login_sponsor"))

    return render_template("register_sponsor.html")




# --------------------------------------------------------------------------------
# ==============  SPONSOR ROUTES  END ============================================
# --------------------------------------------------------------------------------




@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        flash("You must be logged in as an admin to access this page.",  category="info")
        return redirect(url_for("admin_login"))
    # return render_template("admin_dashboard.html")
    return render_template("sample_dashboard.html")


@app.route("/sponsor_dashboard")
def sponsor_dashboard():
    if session.get("role") != "sponsor":
        flash("You must be logged in as a sponsor to access this page.",  category="danger")
        return redirect(url_for("login_sponsor"))
    # return render_template("sponsor_dashboard.html")
    return render_template("sample_dashboard.html")


@app.route("/influencer_dashboard")
def influencer_dashboard():
    if session.get("role") != "influencer":
        flash("You must be logged in as an influencer to access this page.",  category="danger")
        return redirect(url_for("login_influencer"))
    # return render_template("influencer_dashboard.html")
    return render_template("sample_dashboard.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.",  category="info")
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(debug=True)
