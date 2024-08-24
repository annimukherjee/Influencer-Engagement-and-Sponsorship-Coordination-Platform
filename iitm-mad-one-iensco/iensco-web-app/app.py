from flask import Flask, request, redirect, url_for, render_template, flash, session, jsonify
from models import db, User, Sponsor, Influencer, Campaign, AdRequest
from sqlalchemy import func
from datetime import datetime


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///influencer_platform.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = "anni-op"


db.init_app(app)

# Create the database tables
with app.app_context():
    db.create_all()


@app.route("/", methods=["GET", "POST"])
def home():
    return render_template("home.html")


#
#

# --------------------------------------------------------------------------------
#            _           _                           _           
#           | |         (_)                         | |          
#   __ _  __| |_ __ ___  _ _ __      _ __ ___  _   _| |_ ___ ___ 
#  / _` |/ _` | '_ ` _ \| | '_ \    | '__/ _ \| | | | __/ _ / __|
# | (_| | (_| | | | | | | | | | |   | | | (_) | |_| | ||  __\__ \
#  \__,_|\__,_|_| |_| |_|_|_| |_|   |_|  \___/ \__,_|\__\___|___/
# --------------------------------------------------------------------------------



#
#
#

# region ADMIN ROUTES


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

        else:
            flash("Invalid email or password for admin.", category="danger")

    return render_template("admin/login_admin.html")


@app.route("/admin_dashboard")
def admin_dashboard():
    if session.get("role") != "admin":
        flash("You must be logged in as an admin to access this page.", "info")
        return redirect(url_for("admin_login"))

    all_campaigns = Campaign.query.all()

    # CALC a percentage based on strt_date and end_date
    for campaign in all_campaigns:
        total_duration = (campaign.end_date - campaign.start_date).days
        elapsed_duration = (datetime.now().date() - campaign.start_date).days
        campaign.progress = min(int((elapsed_duration / total_duration) * 100), 100)

    all_sponsors = Sponsor.query.all()  
    all_influencers = Influencer.query.all()  

    # both sponsor + influencer counted here!
    flagged_users_count = User.query.filter_by(
        is_flagged=True
    ).count()  

    flagged_campaigns_count = Campaign.query.filter(
        Campaign.is_flagged == True
    ).count() 

    return render_template(
        "admin/admin_dashboard.html",
        all_campaigns=all_campaigns,
        all_sponsors=all_sponsors,
        all_influencers=all_influencers,
        flagged_users_count=flagged_users_count,
        flagged_campaigns_count=flagged_campaigns_count,
    )

    ## --------------------------------------------------------------------------


@app.route("/admin/flagged_items")
def view_flagged_items():
    if session.get("role") != "admin":
        flash("You must be logged in as an admin to access this page.", "info")
        return redirect(url_for("admin_login"))


    flagged_sponsors = Sponsor.query.join(User).filter(User.is_flagged == True).all()
    flagged_influencers = (Influencer.query.join(User).filter(User.is_flagged == True).all())
    flagged_campaigns = Campaign.query.filter_by(is_flagged=True).all()

    return render_template(
        "admin/flagged_items.html",
        flagged_sponsors=flagged_sponsors,
        flagged_influencers=flagged_influencers,
        flagged_campaigns=flagged_campaigns,
    )


@app.route("/admin_find", methods=["GET", "POST"])
def admin_find():

    if session.get("role") != "admin":
        flash("You must be logged in as an admin to access this page.", "info")
        return redirect(url_for("admin_login"))

    search_query = request.args.get("search", "")
    filter_type = request.args.get("filter", "all")

    if filter_type == "sponsors":
        results = (
            db.session.query(Sponsor)
            .join(User)
            .filter(Sponsor.name.ilike(f"%{search_query}%"))
            .all()
        )

    elif filter_type == "campaigns":
        results = (
            db.session.query(Campaign)
            .join(Sponsor)
            .join(User)
            .filter(Campaign.name.ilike(f"%{search_query}%"))
            .all()
        )

    elif filter_type == "influencers":
        results = (
            db.session.query(Influencer)
            .join(User)
            .filter(Influencer.name.ilike(f"%{search_query}%"))
            .all()
        )

    else:

        sponsors = (
            db.session.query(Sponsor)
            .join(User)
            .filter(Sponsor.name.ilike(f"%{search_query}%"))
            .all()
        )

        campaigns = (
            db.session.query(Campaign)
            .join(Sponsor)
            .join(User)
            .filter(Campaign.name.ilike(f"%{search_query}%"))
            .all()
        )

        influencers = (
            db.session.query(Influencer)
            .join(User)
            .filter(Influencer.name.ilike(f"%{search_query}%"))
            .all()
        )

        results = sponsors + campaigns + influencers


    for r in results:
        if isinstance(r, Sponsor):
            r.type = 'sponsor'

        elif isinstance(r, Campaign):
            r.type = 'campaign'
            r.sponsor_name = r.sponsor.name

        elif isinstance(r, Influencer):
            r.type = 'influencer'
    
        if hasattr(r, 'user'):
            r.is_flagged = r.user.is_flagged


    return render_template(
        "admin/admin_find.html",
        results=results,
        search_query=search_query,
        filter_type=filter_type,
    )


@app.route("/admin_stats")
def admin_stats():
    if session.get("role") != "admin":
        flash("You must be logged in as an admin to access this page.", "info")
        return redirect(url_for("admin_login"))
    
    #count usr stuff
    total_users = User.query.count()
    total_sponsors = Sponsor.query.count()
    total_influencers = Influencer.query.count()

    #count campaign stuff
    total_campaigns = Campaign.query.count()
    public_campaigns = Campaign.query.filter_by(visibility="public").count()
    private_campaigns = Campaign.query.filter_by(visibility="private").count()

    # count ad_req stuff
    total_ad_requests = AdRequest.query.count()
    accepted_ads = AdRequest.query.filter_by(status="Accepted").count()
    pending_ads = AdRequest.query.filter_by(status="Pending").count()
    rejected_ads = AdRequest.query.filter_by(status="Rejected").count()



    # count flagged stuff
    flagged_sponsors = Sponsor.query.join(User).filter(User.is_flagged == True).count()
    flagged_influencers = (Influencer.query.join(User).filter(User.is_flagged == True).count())
    flagged_campaigns = Campaign.query.filter_by(is_flagged=True).count()
    
    
    total_flagged = flagged_sponsors + flagged_influencers + flagged_campaigns

    return render_template(
        "admin/admin_stats.html",
        total_users=total_users,
        total_sponsors=total_sponsors,
        total_influencers=total_influencers,
        total_campaigns=total_campaigns,
        total_ad_requests=total_ad_requests,
        public_campaigns=public_campaigns,
        private_campaigns=private_campaigns,
        total_flagged=total_flagged,
        flagged_sponsors=flagged_sponsors,
        flagged_influencers=flagged_influencers,
        flagged_campaigns=flagged_campaigns,
        rejected_ads=rejected_ads,
        accepted_ads=accepted_ads,
        pending_ads=pending_ads,
    )



@app.route("/remove_flag/<string:type>/<int:id>")
def remove_flag(type, id):
    
    if session.get("role") != "admin":
        flash("You must be logged in as an admin to access this functionality.", "info")
        return redirect(url_for("admin_login"))

    if type == "user":
        item = User.query.get_or_404(id)
    elif type == "campaign":
        item = Campaign.query.get_or_404(id)
    else:
        flash("Invalid type specified.", "error")
        return redirect(url_for("admin_dashboard"))

    item.is_flagged = False
    db.session.commit()
    flash(f"{type.capitalize()} flag removed successfully.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/view_sponsor/<int:id>")
def view_sponsor(id):
    if session.get("role") != "admin":
        flash("You must be logged in as an admin to access this page.", "info")
        return redirect(url_for("admin_login"))

    sponsor = Sponsor.query.get_or_404(id)
    return render_template("views/view_sponsor.html", sponsor=sponsor)


@app.route("/view_campaign/<int:id>")
def view_campaign(id):
    if session.get("role") not in ["admin", "influencer"]:
        flash(
            "You must be logged in as an admin or influencer to access this page.",
            "info",
        )
        return redirect(url_for("home"))

    campaign = Campaign.query.get_or_404(id)
    open_ad_requests = AdRequest.query.filter_by(
        campaign_id=id, influencer_id=None, status="Open"
    ).all()
    
    return render_template(
        "views/view_campaign.html",
        campaign=campaign,
        role=session.get("role"),
        open_ad_requests=open_ad_requests,
    )


@app.route("/view_influencer/<int:id>")
def view_influencer(id):
    if session.get("role") not in ["admin", "sponsor"]:
        flash("You must be logged in as an admin/sponsor to access this page.", "info")
        return redirect(url_for("admin_login"))

    influencer = Influencer.query.get_or_404(id)
    return render_template(
        "views/view_influencer.html", influencer=influencer, role=session.get("role")
    )


@app.route("/flag_item/<string:type>/<int:id>")
def flag_item(type, id):
    
    if session.get("role") != "admin":
        flash("You must be logged in as an admin to access this page.", "info")
        return redirect(url_for("admin_login"))

    if type == "sponsor":
        item = Sponsor.query.get_or_404(id)
        user = item.user
        user.is_flagged = True
    
    elif type == "campaign":
        item = Campaign.query.get_or_404(id)
        item.is_flagged = True
    elif type == "influencer":
        item = Influencer.query.get_or_404(id)
        user = item.user
        user.is_flagged = True
    else:
        flash("Invalid type specified.", "error")
        return redirect(url_for("admin_dashboard"))

    db.session.commit()
    flash(f"{type.capitalize()} flagged successfully.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))


# endregion


#
#
#
#
#
#

# ====================================================================================
#  _        __ _                                                   _
# (_)      / _| |                                                 | |
#  _ _ __ | |_| |_   _  ___ _ __   ___ ___ _ __    _ __ ___  _   _| |_ ___ ___
# | | '_ \|  _| | | | |/ _ | '_ \ / __/ _ | '__|  | '__/ _ \| | | | __/ _ / __|
# | | | | | | | | |_| |  __| | | | (_|  __| |     | | | (_) | |_| | ||  __\__ \
# |_|_| |_|_| |_|\__,_|\___|_| |_|\___\___|_|     |_|  \___/ \__,_|\__\___|___/
# ====================================================================================

# region INFLUENCER ROUTES


# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# -------------------- INFUENCER ROUTES ------------------------------------------
# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------


@app.route("/register_influencer", methods=["GET", "POST"])
def register_influencer():

    if request.method == "POST":

        username = request.form.get("influencer_username")
        email = request.form.get("influencer_email")
        password = request.form.get("influencer_password")
        full_name = request.form.get("influencer_name")
        platforms = request.form.getlist("platform")
        platforms_str = ", ".join(platforms)
        niche = request.form.get("influencer_niche")
        reach = request.form.get("influencer_reach")

        # debugging statement ------------
        # print(
        #     "Received data in backend: ",
        #     username,
        #     email,
        #     password,
        #     full_name,
        #     platforms,
        #     niche,
        #     reach,
        # )

        # backend validation
        if not all([username, email, password, full_name]):
            flash(
                "All fields are required. Please fill in all the information.",
                category="info",
            )
            return redirect(url_for("register_influencer"))

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash(
                "Email already registered. Please use a different email.",
                category="danger",
            )
            return redirect(url_for("register_influencer"))

        new_user = User(
            username=username, email=email, password=password, role="influencer"
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        new_influencer = Influencer(
            user_id=new_user.id,
            name=full_name,
            niche=niche,
            reach=reach,
            category=platforms_str,
        )

        db.session.add(new_influencer)
        db.session.commit()

        flash("Registration successful. Please log in.", category="success")

        return redirect(url_for("login_influencer"))

    return render_template("influencer/register_influencer.html")


@app.route("/login_influencer", methods=["GET", "POST"])
def login_influencer():

    if request.method == "POST":
        email = request.form.get("influencer_email")
        password = request.form.get("influencer_password")

        user = User.query.filter_by(email=email, role="influencer").first()

        if user and user.check_password(password):

            if user.is_flagged:
                flash(
                    "Your account has been flagged. Please contact admin.",
                    category="danger",
                )

            else:
                session["user_id"] = user.id
                session["role"] = "influencer"
                flash("Logged in successfully as influencer.", category="success")
                return redirect(url_for("influencer_dashboard"))

        else:
            flash("Invalid email or password for influencer.", category="danger")

    return render_template("influencer/login_influencer.html")


@app.route("/influencer_dashboard")
def influencer_dashboard():

    if session.get("role") != "influencer":
        flash("You must be logged in as an influencer to access this page.", "info")
        return redirect(url_for("home"))

    influencer = Influencer.query.filter_by(user_id=session.get("user_id")).first()

    active_campaigns = AdRequest.query.filter_by(
        influencer_id=influencer.id, status="Accepted"
    ).all()

    new_requests = AdRequest.query.filter_by(
        influencer_id=influencer.id, status="Pending"
    ).all()

    return render_template(
        "influencer/influencer_dashboard.html",
        influencer=influencer,
        active_campaigns=active_campaigns,
        new_requests=new_requests,
    )


@app.route("/influencer_find")
def influencer_find():

    if session.get("role") != "influencer":
        flash("You must be logged in as an influencer to access this page.", "info")
        return redirect(url_for("home"))

    influencer = Influencer.query.filter_by(user_id=session.get("user_id")).first()
    search_query = request.args.get("search", "")
    niche_query = request.args.get("niche", "")

    # Query for public and non-flagged campaigns
    public_non_flagged_campaigns = Campaign.query.join(Sponsor).filter(
        Campaign.visibility == "public", Campaign.is_flagged == False
    )

    if search_query:
        public_non_flagged_campaigns = public_non_flagged_campaigns.filter(
            Campaign.name.ilike(f"%{search_query}%")
            | Campaign.description.ilike(f"%{search_query}%")
        )

    if niche_query:
        public_non_flagged_campaigns = public_non_flagged_campaigns.filter(
            Campaign.niche.ilike(f"%{niche_query}%")
        )

    campaigns = public_non_flagged_campaigns.all()


    for campaign in campaigns:
        campaign.has_open_request = (
            AdRequest.query.filter_by(
                campaign_id=campaign.id, influencer_id=None, status="Open"
            ).first()
            is not None
        )

    # need to pass to the dropdown
    niches = [niche for niche, in db.session.query(Campaign.niche).distinct().all()]

    return render_template(
        "influencer/influencer_find.html",
        campaigns=campaigns,
        search_query=search_query,
        niche_query=niche_query,
        niches=niches,
        influencer=influencer,
    )


@app.route("/request_ad/<int:ad_request_id>", methods=["POST"])
def request_ad(ad_request_id):
    
    if session.get("role") != "influencer":
        flash("You must be logged in as an influencer to request an ad.", "error")
        return redirect(url_for("home"))

    ad_request = AdRequest.query.get_or_404(ad_request_id)
    influencer = Influencer.query.filter_by(user_id=session.get("user_id")).first()

    # Check if the influencer has already requested this ad
    existing_request = AdRequest.query.filter_by(
        campaign_id=ad_request.campaign_id,
        influencer_id=influencer.id,
        status="Pending Influ Req",
    ).first()

    if existing_request:
        flash("You have already submitted a request for this ad.", "warning")

    elif ad_request.influencer_id is not None:
        flash("This ad request is no longer open.", "warning")
    
    else:
        new_request = AdRequest(
            campaign_id=ad_request.campaign_id,
            influencer_id=influencer.id,
            ad_name=ad_request.ad_name,
            messages=ad_request.messages,
            requirements=ad_request.requirements,
            payment_amount=ad_request.payment_amount,
            status="Pending Influ Req"
        )

        db.session.add(new_request)
        db.session.commit()
        flash("Request submitted.", "success")

    return redirect(url_for("view_campaign", id=ad_request.campaign_id))


@app.route("/influencer_stats")
def influencer_stats():
    if session.get("role") != "influencer":
        flash("You must be logged in as an influencer to access this page.", "info")
        return redirect(url_for("home"))

    influencer = Influencer.query.filter_by(user_id=session.get("user_id")).first()

    total_campaigns = (
        AdRequest.query.filter_by(influencer_id=influencer.id)
        .distinct(AdRequest.campaign_id)
        .count()
    )
    total_ads = AdRequest.query.filter_by(influencer_id=influencer.id).count()
    total_earnings = influencer.earning

    if total_earnings is None:
        total_earnings = 0

    # Earnings across ad-requests
    ad_request_earnings = (
        db.session.query(AdRequest.ad_name, AdRequest.payment_amount)
        .filter(
            AdRequest.influencer_id == influencer.id, AdRequest.status == "Accepted"
        )
        .all()
    )

    return render_template(
        "influencer/influencer_stats.html",
        influencer=influencer,
        total_campaigns=total_campaigns,
        total_ads=total_ads,
        total_earnings=total_earnings,
        ad_request_earnings=ad_request_earnings,
    )


@app.route("/view_ad_request/<int:id>", methods=["POST", "GET"])
def view_ad_request(id):

    if session.get("role") not in ["influencer", "admin"]:
        flash("You must be logged in as an influencer or admin for access.", "info")
        return redirect(url_for("home"))

    ad_request = AdRequest.query.get_or_404(id)
    return render_template(
        "views/view_ad_request.html", ad_request=ad_request, user_role=session.get("role")
    )


@app.route("/update_ad_request/<int:id>", methods=["POST", "GET"])
def update_ad_request(id):
    
    if session.get("role") != "influencer":
        flash("You must be logged in as an influencer to access this page.", "info")
        return redirect(url_for("home"))

    ad_request = AdRequest.query.get_or_404(id)
    influencer = Influencer.query.filter_by(user_id=session.get("user_id")).first()

    action = request.form.get("action")

    if action == "accept":
        ad_request.status = "Accepted"

        #for initialization purposes 
        if influencer.earning is None:
            influencer.earning = 0

        influencer.earning += ad_request.payment_amount

    elif action == "reject":
        ad_request.status = "Rejected"

    db.session.commit()
    flash("Suceess! Ad request updated.", "success")
    return redirect(url_for("influencer_dashboard"))


# endregion

#
#
#
#
#
# ---------------------------------------------------------------------------------                                                    _
#                                                        | |
#  ___ _ __   ___  _ __  ___  ___  _ __   _ __ ___  _   _| |_ ___ ___
# / __| '_ \ / _ \| '_ \/ __|/ _ \| '__| | '__/ _ \| | | | __/ _ / __|
# \__ | |_) | (_) | | | \__ | (_) | |    | | | (_) | |_| | ||  __\__ \
# |___| .__/ \___/|_| |_|___/\___/|_|    |_|  \___/ \__,_|\__\___|___/
#     | |
#     |_|
# ---------------------------------------------------------------------------------



# region SPONSOR ROUTES

# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# ==============  SPONSOR ROUTES  BGN ============================================
# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------
# --------------------------------------------------------------------------------


@app.route("/login_sponsor", methods=["GET", "POST"])
def login_sponsor():

    if request.method == "POST":

        email = request.form.get("sponsor_email")
        password = request.form.get("sponsor_password")

        user = User.query.filter_by(email=email, role="sponsor").first()

        if user and user.check_password(password):
            # usr exists and pswd verified.

            if user.is_flagged:
                flash(
                    "Your account is FLAGGED. Contact admin @ admin@iitm.com.",
                    category="danger",
                )
            else:
                session["user_id"], session["role"] = user.id, "sponsor"
                flash("Successfully login as sponsor.", category="success")
                return redirect(url_for("sponsor_dashboard"))

        else:
            flash(
                "Invalid email or password for sponsor. Try again...", category="danger"
            )

    return render_template("sponsor/1_login_sponsor.html")


@app.route("/register_sponsor", methods=["GET", "POST"])
def register_sponsor():

    if request.method == "POST":
        username = request.form.get("sponsor_username")
        email = request.form.get("sponsor_email")
        password = request.form.get("sponsor_password")
        company_name = request.form.get("sponsor_name")
        industry = request.form.get("sponsor_industry")
        budget = request.form.get("sponsor_budget")
        budget_left = budget

        # debugging statement
        # print(
        #     "Received data in backend: ",
        #     username,
        #     email,
        #     password,
        #     company_name,
        #     industry,
        #     budget,
        # )

        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash(
                "Email already registered. Please use a different email.",
                category="danger",
            )
            return redirect(url_for("register_sponsor"))

        new_usr = User(
            username=username, email=email, role="sponsor", password=password
        )

        new_usr.set_password(password)
        db.session.add(new_usr)
        db.session.commit()

        new_sponsor = Sponsor(
            user_id=new_usr.id, name=company_name, industry=industry, budget=budget, budget_left=budget_left
        )

        db.session.add(new_sponsor)
        db.session.commit()

        flash("Successful registration. Please log in.", category="success")
        return redirect(url_for("login_sponsor"))

    return render_template("sponsor/0_register_sponsor.html")


# ---------------


@app.route("/sponsor_dashboard")
def sponsor_dashboard():

    # only sponsor can access sponsor dashboard. no one else can.
    if session.get("role") != "sponsor":
        flash("FORBIDDEN! Only sponsors can access this page. Sorry!", "info")
        return redirect(url_for("home"))

    sponsor = Sponsor.query.filter_by(user_id=session.get("user_id")).first()

    active_campaigns = Campaign.query.filter_by(
        sponsor_id=sponsor.id, status="Active"
    ).all()

    # based on my design of influencer's req
    # in the influ table, if there's ad req w/ influid set to NONE, influ can "request"
    # on request, another row is added to the table w/ "Pending Influ Req" and influ's id

    influencer_reqs = (
        AdRequest.query.join(Campaign)
        .filter(
            Campaign.sponsor_id == sponsor.id,
            AdRequest.status == "Pending Influ Req",
            AdRequest.influencer_id != None,
        )
        .all()
    )

    return render_template(
        "sponsor/3_sponsor_dashboard.html",
        sponsor=sponsor,
        active_campaigns=active_campaigns,
        influencer_requests=influencer_reqs,
    )


@app.route("/process_request/<int:ad_request_id>", methods=["POST"])
def process_request(ad_request_id):

    if session.get("role") != "sponsor":
        flash("You must be logged in as a sponsor to process requests.", "error")
        return redirect(url_for("home"))

    ad_request = AdRequest.query.get_or_404(ad_request_id)
    action = request.form.get("action")

    if action == "accept":

        # first find the ad req w/ influ_id = NULL
        open_ad_request = AdRequest.query.filter_by(
            campaign_id=ad_request.campaign_id, influencer_id=None, status="Open"
        ).first()

        if open_ad_request:
            ad_request.ad_name = open_ad_request.ad_name
            ad_request.messages = open_ad_request.messages
            ad_request.requirements = open_ad_request.requirements
            ad_request.payment_amount = open_ad_request.payment_amount

            # Delete the original req with Influ.id = NULL as it's accepted now
            db.session.delete(open_ad_request)

        ad_request.status = "Accepted"

        # Reject other pending requests for this ad
        other_requests = AdRequest.query.filter(
            AdRequest.campaign_id == ad_request.campaign_id,
            AdRequest.id != ad_request.id,
            AdRequest.status == "Pending Influ Req",
        ).all()

        for req in other_requests:
            req.status = "Rejected"
            req.payment_amount = 0

        influencer = ad_request.influencer
        influencer.earning += ad_request.payment_amount

        flash("Request accepted and influencer notified.", "success")

    elif action == "reject":
        ad_request.status = "Rejected"
        ad_request.payment_amount = 0
        flash("Request rejected.", "success")

    db.session.commit()
    return redirect(url_for("sponsor_dashboard"))


# ------------


@app.route("/sponsor_campaigns")
def sponsor_campaigns():

    if session.get("role") != "sponsor":
        flash("FORBIDDEN! Only sponsors can access this page. Sorry!", "info")
        return redirect(url_for("home"))

    sponsor = Sponsor.query.filter_by(user_id=session.get("user_id")).first()
    campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id).all()

    return render_template(
        "sponsor/2_sponsor_campaigns.html", sponsor=sponsor, campaigns=campaigns
    )


@app.route("/add_campaign", methods=["GET", "POST"])
def add_campaign():

    if session.get("role") != "sponsor":
        flash("FORBIDDEN! Only sponsors can access this page. Sorry!", "info")
        return redirect(url_for("home"))

    sponsor = Sponsor.query.filter_by(user_id=session.get("user_id")).first()

    if request.method == "POST":

        campaign_budget = float(request.form.get("campaign_budget"))

        # for initializing purposes
        if sponsor.budget_left is None:
            sponsor.budget_left = sponsor.budget

        if sponsor.budget_left < campaign_budget:
            flash("Insufficient funds to create this campaign.", "danger")
            return redirect(url_for("sponsor_campaigns"))

        new_campaign = Campaign(
            sponsor_id=sponsor.id,
            name=request.form.get("campaign_name"),
            description=request.form.get("campaign_desc"),
            start_date=datetime.strptime(request.form.get("start_date"), "%Y-%m-%d"),
            end_date=datetime.strptime(request.form.get("end_date"), "%Y-%m-%d"),
            budget=campaign_budget,
            visibility=request.form.get("visb"),
            niche=request.form.get("niche"),
            goals=request.form.get("goals"),
            status="Active",  # sort of useless, but let it be...
        )

        sponsor.budget_left = sponsor.budget_left - campaign_budget

        db.session.add(new_campaign)
        db.session.commit()

        flash("Added Campaign.", "success")
        return redirect(url_for("sponsor_campaigns"))

    return render_template("sponsor/add_campaign.html", sponsor=sponsor)


@app.route("/delete_campaign/<int:campaign_id>", methods=["POST"])
def delete_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    db.session.delete(campaign)
    db.session.commit()
    flash("Campaign deleted successfully.", "success")
    return redirect(url_for("sponsor_campaigns"))


@app.route("/edit_campaign/<int:campaign_id>", methods=["GET", "POST"])
def edit_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)

    if request.method == "POST":
        title = request.form.get("campaign_name")
        description = request.form.get("campaign_desc")
        start_date = datetime.strptime(request.form.get("start_date"), "%Y-%m-%d")
        end_date = datetime.strptime(request.form.get("end_date"), "%Y-%m-%d")
        budget = request.form.get("campaign_budget")
        visibility = request.form.get("visb")
        niche = request.form.get("niche")
        goals = request.form.get("goals")

        if not title:
            flash("Campaign name is required.", "error")
            return redirect(url_for("edit_campaign", campaign_id=campaign_id))

        campaign.name = title
        campaign.description = description
        campaign.start_date = start_date
        campaign.end_date = end_date
        campaign.budget = budget
        campaign.visibility = visibility
        campaign.niche = niche
        campaign.goals = goals

        db.session.commit()
        flash("Campaign updated successfully.", "success")

        return redirect(url_for("sponsor_campaigns"))

    return render_template("sponsor/5_edit_campaign.html", campaign=campaign)


@app.route("/campaign/<int:campaign_id>")
def campaign_details(campaign_id):

    if session.get("role") != "sponsor":
        flash("FORBIDDEN! Only sponsors can access this page. Sorry!", "info")
        return redirect(url_for("home"))

    campaign = Campaign.query.get_or_404(campaign_id)
    ad_requests = AdRequest.query.filter_by(campaign_id=campaign_id).all()

    # to get the amt of money already allocated, we have to add all the payment amounts of Accepted ad reqs
    total_spent_for_campaign = (
        db.session.query(func.sum(AdRequest.payment_amount))
        .filter_by(campaign_id=campaign_id, status="Accepted")
        .scalar()
        or 0
    )

    return render_template(
        "sponsor/campaign_details.html",
        campaign=campaign,
        ad_requests=ad_requests,
        total_spent=total_spent_for_campaign,
    )


@app.route("/add_ad_request/<int:campaign_id>", methods=["GET", "POST"])
def add_ad_request(campaign_id):
    if session.get("role") != "sponsor":
        flash("FORBIDDEN! Only sponsors can access this page. Sorry!", "info")
        return redirect(url_for("home"))

    campaign = Campaign.query.get_or_404(campaign_id)
    influencers = Influencer.query.all()  # Fetch all influencers

    if request.method == "POST":
        influencer_id = request.form.get("influencer_id")
        payment_amount = float(request.form.get("payment"))

        total_spent_for_campaign = (
            db.session.query(func.sum(AdRequest.payment_amount))
            .filter_by(campaign_id=campaign_id, status= "Accepted"
            )
            .scalar()
            or 0
        )

        remaining_budget = campaign.budget - total_spent_for_campaign

        if payment_amount > remaining_budget:
            flash(
                f"The payment amount exceeds the remaining campaign budget. Remaining budget: ${remaining_budget}",
                "danger",
            )
            return render_template(
                "sponsor/add_ad_request.html",
                campaign=campaign,
                influencers=influencers,
            )

        new_ad_req = AdRequest(
            campaign_id=campaign_id,
            influencer_id=None if influencer_id == "open" else influencer_id,
            messages=request.form.get("messages"),
            requirements=request.form.get("terms"),
            payment_amount=payment_amount,
            status="Open" if influencer_id == "open" else "Pending",
            ad_name=request.form.get("ad-name"),
        )
        db.session.add(new_ad_req)
        db.session.commit()

        if influencer_id == "open":
            flash("Added Open ad request.", "success")
        else:
            flash("Added Ad request.", "success")

        return redirect(url_for("campaign_details", campaign_id=campaign_id))

    return render_template(
        "sponsor/add_ad_request.html", campaign=campaign, influencers=influencers
    )


@app.route("/edit_ad_request/<int:ad_request_id>", methods=["GET", "POST"])
def edit_ad_request(ad_request_id):
    if session.get("role") != "sponsor":
        flash("FORBIDDEN! Only sponsors can access this page. Sorry!", "info")
        return redirect(url_for("home"))

    ad_request = AdRequest.query.get_or_404(ad_request_id)
    influencers = Influencer.query.all()

    if request.method == "POST":
        influencer_id = request.form.get("influencer_id")

        if influencer_id is None:
            ad_request.influencer_id = None
            ad_request.status = "Open"
        else:
            ad_request.influencer_id = influencer_id
            ad_request.status = "Pending"

        ad_request.messages = request.form.get("messages")
        ad_request.requirements = request.form.get("terms")
        ad_request.payment_amount = float(request.form.get("payment"))
        ad_request.ad_name = request.form.get("ad-name")

        db.session.commit()
        flash("Ad request updated successfully.", "success")

        return redirect(url_for("campaign_details", campaign_id=ad_request.campaign_id))

    return render_template(
        "sponsor/edit_ad_request.html", ad_request=ad_request, influencers=influencers
    )


@app.route("/delete_ad_request/<int:ad_request_id>", methods=["POST"])
def delete_ad_request(ad_request_id):

    if session.get("role") != "sponsor":
        flash("FORBIDDEN! Only sponsors can access this page. Sorry!", "info")
        return redirect(url_for("home"))

    ad_request = AdRequest.query.get_or_404(ad_request_id)
    campaign_id = ad_request.campaign_id

    db.session.delete(ad_request)
    db.session.commit()
    flash("Ad request deleted successfully.", "success")
    return redirect(url_for("campaign_details", campaign_id=campaign_id))


@app.route("/sponsor_find")
def sponsor_find():

    if session.get("role") != "sponsor":
        flash("FORBIDDEN! Only sponsors can access this page. Sorry!", "info")
        return redirect(url_for("home"))

    search_query = request.args.get("search", "")
    selected_niche = request.args.get("niche", "")
    min_reach = request.args.get("min_reach", "")

    sponsor = Sponsor.query.filter_by(user_id=session.get("user_id")).first()
    

    query = Influencer.query

    if search_query:
        query = query.filter(Influencer.name.ilike(f"%{search_query}%"))

    if selected_niche:
        query = query.filter(Influencer.niche == selected_niche)

    if min_reach:
        query = query.filter(Influencer.reach >= int(min_reach))

    # influencers = Influencer.query.join(User).filter(User.is_flagged==0).all()
    influencers = query.all()

    # for i in influencers:
    #     print(i.name) 

    # query.join(Campaign).filter(Campaign.sponsor_id == sponsor.id).count()

    # Get unique niches (dropdown)
    niches = (
        db.session.query(Influencer.niche).distinct().order_by(Influencer.niche).all()
    )
    niches = [niche[0] for niche in niches if niche[0]]

    return render_template(
        "sponsor/4_sponsor_find.html",
        influencers=influencers,
        search_query=search_query,
        selected_niche=selected_niche,
        min_reach=min_reach,
        sponsor=sponsor,
        niches=niches,
    )


@app.route("/sponsor_stats")
def sponsor_stats():
    if session.get("role") != "sponsor":
        flash("FORBIDDEN! Only sponsors can access this page. Sorry!", "info")
        return redirect(url_for("home"))

    sponsor = Sponsor.query.filter_by(user_id=session.get("user_id")).first()

    # get total campaigns created by sponsor
    campaigns = Campaign.query.filter_by(sponsor_id=sponsor.id)
    total_campaigns = campaigns.count()

    # get total ads created by sponsor
    total_ads = (
        AdRequest.query.join(Campaign).filter(Campaign.sponsor_id == sponsor.id).count()
    )

    ads_accepted = (
        AdRequest.query.join(Campaign).filter(
            Campaign.sponsor_id == sponsor.id, AdRequest.status == "Accepted"
        )
    ).count()

    ads_rejected = (
        AdRequest.query.join(Campaign).filter(
            Campaign.sponsor_id == sponsor.id, AdRequest.status == "Rejected"
        )
    ).count()

    ads_pending_sponsor_sent = (
        AdRequest.query.join(Campaign).filter(
            Campaign.sponsor_id == sponsor.id, AdRequest.status == "Pending"
        )
    ).count()

    ads_pending_influ_sent = (
        AdRequest.query.join(Campaign).filter(
            Campaign.sponsor_id == sponsor.id, AdRequest.status == "Pending Influ Req"
        )
    ).count()

    ads_pending = ads_pending_influ_sent + ads_pending_sponsor_sent

    total_budget = sponsor.budget
    total_budget_spent = total_budget - sponsor.budget_left

    ad_requests_count = (
        db.session.query(Influencer.name, func.count(AdRequest.id).label("count"))
        .join(AdRequest, AdRequest.influencer_id == Influencer.id)
        .join(Campaign, Campaign.id == AdRequest.campaign_id)
        .filter(Campaign.sponsor_id == sponsor.id)
        .group_by(Influencer.name)
        .all()
    )

    return render_template(
        "sponsor/6_sponsor_stats.html",
        sponsor=sponsor,
        campaigns = campaigns,
        total_campaigns=total_campaigns,
        total_ads=total_ads,
        total_budget=total_budget,
        total_budget_spent=total_budget_spent,
        ad_requests_count=ad_requests_count,
        ads_accepted=ads_accepted,
        ads_rejected=ads_rejected,
        ads_pending=ads_pending,
    )


# --------------------------------------------------------------------------------
# ==============  SPONSOR ROUTES  END ============================================
# --------------------------------------------------------------------------------


# endregion


# ---------------------------------------------------------------------------------
#              _                    _             _       _       
#             (_)                  | |           (_)     | |      
#   __ _ _ __  _      ___ _ __   __| |_ __   ___  _ _ __ | |_ ___ 
#  / _` | '_ \| |    / _ | '_ \ / _` | '_ \ / _ \| | '_ \| __/ __|
# | (_| | |_) | |   |  __| | | | (_| | |_) | (_) | | | | | |_\__ \
#  \__,_| .__/|_|    \___|_| |_|\__,_| .__/ \___/|_|_| |_|\__|___/
#       | |                          | |                          
#       |_|                          |_|                          
# ---------------------------------------------------------------------------------



# +--------------------------------------------+-------------------+--------------------+
# | Endpoint                                   | Method            | Description        |
# +--------------------------------------------+-------------------+--------------------+
# | /api/campaigns                             | GET               | List all campaigns |
# | /api/campaigns/<campaign_id>               | GET               | Get campaign by ID |
# | /api/ad_requests/<int:ad_request_id>       | DELETE            | Delete Ad-request  |
# | /api/sponsors                              | GET               | List all sponsors  |
# | /api/sponsors/<sponsor_id>                 | GET               | Get sponsor by ID  |
# | /api/influencers                           | GET               | List influencers   |
# | /api/influencers/<influencer_id>           | GET               | Get influencer     |
# | /api/ad_requests                           | GET               | List ad requests   |
# | /api/ad_requests/<ad_request_id>           | GET               | Get ad request     |
# +--------------------------------------------+-------------------+--------------------+




# region API ROUTES



@app.route('/api/campaigns')
def get_campaigns():
    campaigns = Campaign.query.all()
    return jsonify([{
        'id': campn.id,
        'name': campn.name,
        'description': campn.description,
        'start_date': campn.start_date.isoformat(),
        'end_date': campn.end_date.isoformat(),
        'budget': campn.budget,
        'visibility': campn.visibility,
        'niche': campn.niche,
        'goals': campn.goals,
        'status': campn.status
    } for campn in campaigns])

@app.route('/api/campaigns/<int:campaign_id>')
def get_campaign(campaign_id):
    campaign = Campaign.query.get_or_404(campaign_id)
    
    return jsonify({
        'id': campaign.id,
        'name': campaign.name,
        'description': campaign.description,
        'start_date': campaign.start_date.isoformat(),
        'end_date': campaign.end_date.isoformat(),
        'budget': campaign.budget,
        'visibility': campaign.visibility,
        'niche': campaign.niche,
        'goals': campaign.goals,
        'status': campaign.status
    })

# Sponsors
@app.route('/api/sponsors')
def get_sponsors():
    sponsors = Sponsor.query.all()
    return jsonify([{
        'id': spon.id,
        'name': spon.name,
        'industry': spon.industry,
        'budget': spon.budget,
        'budget_left': spon.budget_left
    } for spon in sponsors])

@app.route('/api/sponsors/<int:sponsor_id>')
def get_sponsor(sponsor_id):
    sponsor = Sponsor.query.get_or_404(sponsor_id)
    return jsonify({
        'id': sponsor.id,
        'name': sponsor.name,
        'industry': sponsor.industry,
        'budget': sponsor.budget,
        'budget_left': sponsor.budget_left
    })


@app.route('/api/influencers')
def get_influencers():
    influencers = Influencer.query.all()
    return jsonify([{
        'id': influ.id,
        'name': influ.name,
        'niche': influ.niche,
        'reach': influ.reach,
        'category': influ.category,
        'earning': influ.earning
    } for influ in influencers])

@app.route('/api/influencers/<int:influencer_id>')
def get_influencer(influencer_id):
    influencer = Influencer.query.get_or_404(influencer_id)
    return jsonify({
        'id': influencer.id,
        'name': influencer.name,
        'niche': influencer.niche,
        'reach': influencer.reach,
        'category': influencer.category,
        'earning': influencer.earning
    })


@app.route('/api/ad_requests')
def get_ad_requests():
    ad_requests = AdRequest.query.all()
    return jsonify([{
        'id': ad_req.id,
        'campaign_id': ad_req.campaign_id,
        'influencer_id': ad_req.influencer_id,
        'ad_name': ad_req.ad_name,
        'messages': ad_req.messages,
        'requirements': ad_req.requirements,
        'payment_amount': ad_req.payment_amount,
        'status': ad_req.status
    } for ad_req in ad_requests])

@app.route('/api/ad_requests/<int:ad_request_id>')
def get_ad_request(ad_request_id):
    ad_request = AdRequest.query.get_or_404(ad_request_id)
    return jsonify({
        'id': ad_request.id,
        'campaign_id': ad_request.campaign_id,
        'influencer_id': ad_request.influencer_id,
        'ad_name': ad_request.ad_name,
        'messages': ad_request.messages,
        'requirements': ad_request.requirements,
        'payment_amount': ad_request.payment_amount,
        'status': ad_request.status
    })

# DELETE endpoint (Deleting an ad)
@app.route('/api/ad_requests/<int:ad_request_id>', methods=['DELETE'])
def delete_campaign_api(ad_request_id):
    ad_req = AdRequest.query.get_or_404(ad_request_id)
    db.session.delete(ad_req)
    db.session.commit()
    return jsonify({
        'message': 'Ad_req deleted successfully'
    })



# endregion



# actually running the app.....

if __name__ == "__main__":
    print("app started.")
    app.run(debug=True)


