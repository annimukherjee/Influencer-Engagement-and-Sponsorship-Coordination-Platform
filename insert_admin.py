from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db

# Initialize Flask app and database
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///influencer_platform.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "your-secret-key"  # Change this to a random secret key

db.init_app(app)

# Create the database tables
with app.app_context():
    db.create_all()


def insert_user(username, email, password, role):
    with app.app_context():
        # Check if user already exists
        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing_user:
            print(f"User with username '{username}' or email '{email}' already exists.")
            return

        # Create new user
        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)

        # Add user to database
        db.session.add(new_user)
        db.session.commit()

        print(f"User '{username}' successfully added to the database.")


if __name__ == "__main__":
    # Example usage
    insert_user("admin", "admin@iitm.com", "admin_pass", "admin")
