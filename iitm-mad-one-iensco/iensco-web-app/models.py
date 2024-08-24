from flask_sqlalchemy import SQLAlchemy

# this is for password hashing
from werkzeug.security import generate_password_hash, check_password_hash

# this is for timestamp functionality
from datetime import datetime


db = SQLAlchemy()


# -------------------------------------------------------------------------------------------------------------------


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(
        db.String(120), nullable=False
    )  # done for debugging purposes so that i can see while developing the app
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), nullable=False)
    is_flagged = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# -------------------------------------------------------------------------------------------------------------------


class Sponsor(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False
    )

    name = db.Column(db.String(125), nullable=False)
    industry = db.Column(db.String(125))
    budget = db.Column(db.Float, default=0)
    budget_left = db.Column(db.Float, default=0)

    user = db.relationship("User", backref=db.backref("sponsor", uselist=False))
    # this is basically a one-to-one relationship between the user and the sponsor,
    # as one sponsor is one user ...


# -------------------------------------------------------------------------------------------------------------------


class Influencer(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
        db.Integer, db.ForeignKey("user.id"), unique=True, nullable=False
    )

    name = db.Column(db.String(125), nullable=False)
    category = db.Column(db.String(125))
    niche = db.Column(db.String(125))
    reach = db.Column(db.Integer, default=0)
    earning = db.Column(db.Float, default=0)

    user = db.relationship("User", backref=db.backref("influencer", uselist=False))
    # this is basically a one-to-one relationship between the user and the influencer,
    # as one influencer is one user ...


# -------------------------------------------------------------------------------------------------------------------


class Campaign(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    sponsor_id = db.Column(db.Integer, db.ForeignKey("sponsor.id"), nullable=False)

    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text)

    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)

    budget = db.Column(db.Float, nullable=False)
    visibility = db.Column(db.String(25))  # 'public' or 'private'
    niche = db.Column(db.String(150))
    goals = db.Column(db.Text)

    is_flagged = db.Column(db.Boolean, default=False)
    status = db.Column(db.String(25), default="Active")

    sponsor = db.relationship("Sponsor", backref=db.backref("campaigns"))


# -------------------------------------------------------------------------------------------------------------------


class AdRequest(db.Model):

    # an ad req has it's own id, the id of the campaign it belongs to and the id of the influencer who has been assigned to that ad-req
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey("campaign.id"), nullable=False)
    influencer_id = db.Column(db.Integer, db.ForeignKey("influencer.id"))

    ad_name = db.Column(db.String(125), nullable=False)
    messages = db.Column(db.Text)
    requirements = db.Column(db.Text)
    payment_amount = db.Column(db.Float)

    # most imp for logic
    status = db.Column(
        db.String(25), nullable=False
    )  # [ 'Pending', 'Accepted', 'Rejected' ]

    # extra attributes, timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    campaign = db.relationship("Campaign", backref=db.backref("ad_requests"))
    influencer = db.relationship("Influencer", backref=db.backref("ad_requests"))


# -------------------------------------------------------------------------------------------------------------------
