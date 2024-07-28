

from app import app, db
from models import User, Sponsor, Influencer

with app.app_context():
    all_users = User.query.all() 
    for i in all_users:
        print(User.query.first())

    print(all_users)