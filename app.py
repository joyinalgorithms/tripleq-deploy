from cs50 import SQL
from flask import Flask, redirect, render_template, request, session, url_for, flash
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
from flask import render_template_string
import os

app = Flask(__name__)
db = SQL("sqlite:///tripleq.db")


app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("adminlog"))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/")
def index():
    return render_template("home.html")


@app.route("/aboutus")
def aboutus():
    about = db.execute("SELECT * FROM about_us LIMIT 1")
    return render_template("aboutus.html", about=about[0] if about else {})


@app.route("/admin/aboutus", methods=["GET", "POST"])
@login_required
def admin_about():
    if request.method == "POST":
        introduction = request.form.get("introduction", "").replace("\n", "<br>")
        services = request.form.get("services", "").replace("\n", "<br>")
        expertise = request.form.get("expertise", "").replace("\n", "<br>")
        commitment = request.form.get("commitment", "").replace("\n", "<br>")
        team = request.form.get("team", "").replace("\n", "<br>")
        vision = request.form.get("vision", "").replace("\n", "<br>")

        if not (introduction and services and expertise and commitment and team and vision):
            flash("All fields must be filled!", "danger")
            return redirect(url_for("admin_about"))

        db.execute("""
            UPDATE about_us
            SET
                introduction = :introduction,
                services = :services,
                expertise = :expertise,
                commitment = :commitment,
                team = :team,
                vision = :vision
            WHERE id = 1
        """,
                   introduction=introduction,
                   services=services,
                   expertise=expertise,
                   commitment=commitment,
                   team=team,
                   vision=vision)

        flash("About Us updated successfully!", "success")
        return redirect(url_for("admin_about"))

    about_content = db.execute("SELECT * FROM about_us WHERE id = 1")
    print(request.form)

    if about_content:
        return render_template("admin_about.html", about=about_content[0])
    else:
        flash("No content found. Please insert an initial entry in the database.", "danger")
        return render_template("admin_about.html", about={})


@app.route("/blogpost")
def blogpost():
    articles = db.execute(
        "SELECT post_id, title, summary, author, created_at FROM blog_posts ORDER BY created_at DESC"
    )
    return render_template("blogpost.html", articles=articles)


@app.route("/blogpost/<int:post_id>")
def blogpost_detail(post_id):
    article = db.execute("SELECT * FROM blog_posts WHERE post_id = ?", post_id)
    if not article:
        flash("Article not found", "danger")
        return redirect(url_for("blogpost"))
    return render_template("blogpost_detail.html", article=article[0])


@app.route("/admin/blog", methods=["GET", "POST"])
@login_required
def admin_blog():
    if request.method == "POST":
        title = request.form["title"]
        author = request.form["author"]
        summary = request.form["summary"]
        content = request.form["content"]

        db.execute("INSERT INTO blog_posts (title, author, summary, content) VALUES (?, ?, ?, ?)",
                   title, author, summary, content)
        flash("Blog post added successfully!", "success")
        return redirect(url_for("admin_blog"))

    posts = db.execute("SELECT * FROM blog_posts ORDER BY created_at DESC")
    return render_template("admin_blog.html", posts=posts)


@app.route("/admin/blog/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_blog(id):
    if request.method == "POST":
        title = request.form["title"]
        summary = request.form["summary"]
        content = request.form["content"]

        db.execute(
            "UPDATE blog_posts SET title = ?, summary = ?, content = ? WHERE post_id = ?",
            title, summary, content, id
        )
        flash("Blog post updated successfully!", "info")
        return redirect(url_for("admin_blog"))

    post = db.execute("SELECT * FROM blog_posts WHERE post_id = ?", id)
    if not post:
        flash("Post not found", "danger")
        return redirect(url_for("admin_blog"))
    return render_template("edit_blog.html", post=post[0])


@app.route("/admin/blog/delete/<int:id>")
@login_required
def delete_blog(id):
    db.execute("DELETE FROM blog_posts WHERE post_id = ?", id)
    flash("Blog post deleted successfully!", "danger")
    return redirect(url_for("admin_blog"))


@app.route("/careers")
def careers():
    careers = db.execute("SELECT * FROM careers")
    return render_template("careers.html", careers=careers)


@app.route("/admin/careers")
@login_required
def admin_careers():
    careers = db.execute("SELECT * FROM careers")
    return render_template("admin_careers.html", careers=careers)


@app.route("/admin/careers/add", methods=["POST"])
@login_required
def add_career():
    position = request.form.get("position")
    requirements = request.form.get("requirements")

    if position and requirements:
        db.execute("INSERT INTO careers (position, requirements) VALUES (?, ?)",
                   position, requirements)
        flash("Job position added!", "success")

    return redirect(url_for("admin_careers"))


@app.route("/admin/careers/edit/<int:id>", methods=["GET", "POST"])
@login_required
def edit_career(id):
    if request.method == "POST":
        position = request.form.get("position")
        requirements = request.form.get("requirements")

        if position and requirements:
            db.execute("UPDATE careers SET position = ?, requirements = ? WHERE id = ?",
                       position, requirements, id)
            flash("Job position updated!", "success")

        return redirect(url_for("admin_careers"))

    job = db.execute("SELECT * FROM careers WHERE id = ?", id)
    if not job:
        flash("Job not found!", "danger")
        return redirect(url_for("admin_careers"))

    return render_template("edit_career.html", job=job[0])


@app.route("/admin/careers/delete/<int:id>")
def delete_career(id):
    db.execute("DELETE FROM careers WHERE id = ?", id)
    flash("Job position deleted!", "danger")
    return redirect(url_for("admin_careers"))


@app.route("/contactus")
def contact_us():
    contact = db.execute("SELECT * FROM contact_info WHERE id = 1")[0]
    return render_template("contactus.html", contact=contact)


@app.route("/quotation", methods=["GET", "POST"])
def quotation():
    estimate = None

    if request.method == "POST":
        project_type = request.form.get("project_type")
        try:
            area_size = float(request.form.get("area_size"))
        except ValueError:
            flash("Please enter a valid number for area size.", "danger")
            return redirect(url_for("quotation"))

        services = request.form.getlist("services")

        base_rate_row = db.execute("SELECT value FROM quotation_settings WHERE setting_type = 'base_rate' AND name = ?", project_type)
        base_rate = base_rate_row[0]["value"] if base_rate_row else 0

        service_cost = 0
        for service in services:
            row = db.execute("SELECT value FROM quotation_settings WHERE setting_type = 'service_cost' AND name = ?", service)
            if row:
                service_cost += row[0]["value"]

        estimate = int(area_size * base_rate + service_cost)

    return render_template("quotation.html", estimate=estimate)


@app.route("/admin/quotation-settings", methods=["GET", "POST"])
def admin_quotation_settings():
    if request.method == "POST":
        for key, value in request.form.items():
            try:
                float_value = float(value)
                db.execute("UPDATE quotation_settings SET value = ? WHERE id = ?", float_value, key)
            except ValueError:
                flash(f"Invalid value for setting ID {key}. Must be a number.", "danger")
        flash("Quotation settings updated successfully.", "success")
        return redirect(url_for("admin_quotation_settings"))

    settings = db.execute("SELECT * FROM quotation_settings ORDER BY setting_type, name")
    return render_template("admin_quotation.html", settings=settings)


@app.route("/reviews", methods=["GET", "POST"])
def reviews():
    if request.method == "POST":
        name = request.form.get("name")
        rating = request.form.get("rating")
        comment = request.form.get("review")

        db.execute("INSERT INTO project_reviews (reviewer_name, rating, comment) VALUES (?, ?, ?)",
                   name, rating, comment)
        flash("Thank you for your review!", "success")
        return redirect(url_for("reviews"))

    reviews = db.execute("SELECT * FROM project_reviews ORDER BY created_at DESC")
    return render_template("reviews.html", reviews=reviews)


@app.route("/admin/reviews")
@login_required
def admin_reviews():
    reviews = db.execute("SELECT * FROM project_reviews ORDER BY created_at DESC")
    return render_template("admin_reviews.html", reviews=reviews)


@app.route("/admin/reviews/delete/<int:id>")
@login_required
def delete_review(id):
    db.execute("DELETE FROM project_reviews WHERE id = ?", id)
    flash("Review deleted!", "danger")
    return redirect(url_for("admin_reviews"))


@app.route("/services")
def services():
    services = db.execute("SELECT * FROM services")
    projects = db.execute("""
        SELECT projects.id, projects.title, projects.description, services.name AS service_name
        FROM projects
        JOIN services ON projects.service_id = services.id
    """)
    images = db.execute("SELECT * FROM project_images")

    return render_template("services.html", services=services, projects=projects, images=images)


@app.route("/admin/services", methods=["GET", "POST"])
@login_required
def admin_services():
    services = db.execute("SELECT * FROM services")
    return render_template("admin_services.html", services=services)


@app.route("/admin/services/add", methods=["POST"])
@login_required
def add_service():
    name = request.form.get("name")
    description = request.form.get("description")
    db.execute("INSERT INTO services (name, description) VALUES (?, ?)", name, description)
    flash("Service added successfully!", "success")
    return redirect(url_for("admin_services"))


@app.route("/admin/services/delete/<int:id>")
@login_required
def delete_service(id):
    db.execute("DELETE FROM services WHERE id = ?", id)
    flash("Service deleted!", "danger")
    return redirect(url_for("admin_services"))

@app.route("/privacypolicy")
def privacy():
    policy = db.execute("SELECT content FROM site_content WHERE page = 'privacy'")
    contact = db.execute("SELECT * FROM contact_info WHERE id = 1")[0]
    rendered_content = render_template_string(policy[0]["content"], contact=contact) if policy else ""
    return render_template("privacy.html", content=rendered_content)


@app.route("/termsandconditions")
def terms():
    terms = db.execute("SELECT content FROM site_content WHERE page = 'terms'")
    contact = db.execute("SELECT * FROM contact_info WHERE id = 1")[0]
    rendered_content = render_template_string(terms[0]["content"], contact=contact) if terms else ""
    return render_template("terms.html", content=rendered_content)


@app.route("/cookiepolicy")
def cookiepolicy():
    policy = db.execute("SELECT content FROM site_content WHERE page = 'cookies'")
    contact = db.execute("SELECT * FROM contact_info WHERE id = 1")[0]
    rendered_content = render_template_string(policy[0]["content"], contact=contact) if policy else ""
    return render_template("cookies.html", content=rendered_content)

@app.route("/admin/privacy", methods=["GET", "POST"])
def admin_privacy():
    if request.method == "POST":
        content = request.form.get("content")
        db.execute("""
            INSERT INTO site_content (page, content) VALUES ('privacy', ?)
            ON CONFLICT (page) DO UPDATE SET content = excluded.content
        """, content)
        return redirect(url_for("admin_privacy"))

    policy = db.execute("SELECT content FROM site_content WHERE page = 'privacy'")
    return render_template("admin_privacy.html", policy=policy[0] if policy else {"content": ""})


@app.route("/admin/terms", methods=["GET", "POST"])
def admin_terms():
    if request.method == "POST":
        content = request.form.get("content")
        db.execute("""
            INSERT INTO site_content (page, content) VALUES ('terms', ?)
            ON CONFLICT (page) DO UPDATE SET content = excluded.content
        """, content)
        return redirect(url_for("admin_terms"))

    terms = db.execute("SELECT content FROM site_content WHERE page = 'terms'")
    return render_template("admin_terms.html", terms=terms[0] if terms else {"content": ""})


@app.route("/admin/cookies", methods=["GET", "POST"])
def admin_cookies():
    if request.method == "POST":
        content = request.form.get("content")
        db.execute("""
            INSERT INTO site_content (page, content) VALUES ('cookies', ?)
            ON CONFLICT (page) DO UPDATE SET content = excluded.content
        """, content)
        return redirect(url_for("admin_cookies"))

    cookies = db.execute("SELECT content FROM site_content WHERE page = 'cookies'")
    return render_template("admin_cookies.html", cookies=cookies[0] if cookies else {"content": ""})


@app.route("/adminlogin", methods=["GET", "POST"])
def adminlog():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        admin = db.execute("SELECT * FROM admin WHERE username = ?", username)
        if not admin or not check_password_hash(admin[0]["password_hash"], password):
            flash("Invalid credentials", "danger")
            return redirect(url_for("adminlog"))

        session["admin_id"] = admin[0]["admin_id"]
        flash("Login successful!", "success")
        return redirect(url_for("admin"))

    return render_template("adminlog.html")


@app.route("/admin")
@login_required
def admin():
    return render_template("admin.html")

@app.route("/admin/contactus", methods=["GET", "POST"])
@login_required
def admin_contact():
    if request.method == "POST":
        phone = request.form.get("phone").strip().replace("\n", "<br>")
        email = request.form.get("email")
        address = request.form.get("address")
        office_hours = request.form.get("office_hours")

        db.execute("UPDATE contact_info SET phone = ?, email = ?, address = ?, office_hours = ? WHERE id = 1",
                   phone, email, address, office_hours)
        flash("Contact Information Updated Successfully!", "success")

    contact = db.execute("SELECT * FROM contact_info WHERE id = 1")[0]
    return render_template("admin_contact.html", contact=contact)


@app.route("/appointment", methods=["GET", "POST"])
def appointment():
    if request.method == "POST":
        full_name = request.form["full_name"]
        phone = request.form["phone"]
        email = request.form["email"]
        preferred_date = request.form["preferred_date"]
        preferred_time = request.form["preferred_time"]
        message = request.form["message"]

        db.execute("""
            INSERT INTO appointments (full_name, phone, email, preferred_date, preferred_time, message, status)
            VALUES (?, ?, ?, ?, ?, ?, 'Pending')
        """, full_name, phone, email, preferred_date, preferred_time, message)

        return redirect(url_for("appointment_confirmation"))

    return render_template("appointment.html")


@app.route("/appointment-confirmation")
def appointment_confirmation():
    return render_template("appointment_confirmation.html")


@app.route("/admin/appointments", methods=["GET"])
@login_required
def admin_appointments():
    pending_appointments = db.execute(
        "SELECT * FROM appointments WHERE status = 'Pending' ORDER BY created_at DESC")
    cancelled_appointments = db.execute(
        "SELECT * FROM appointments WHERE status = 'Cancelled' ORDER BY created_at DESC")
    confirmed_appointments = db.execute(
        "SELECT * FROM appointments WHERE status = 'Confirmed' ORDER BY preferred_date, preferred_time")

    return render_template("admin_appointments.html",
                           pending_appointments=pending_appointments,
                           cancelled_appointments=cancelled_appointments,
                           confirmed_appointments=confirmed_appointments)


@app.route("/admin/appointments/update/<int:id>", methods=["POST"])
@login_required
def update_appointment(id):
    new_status = request.form["status"]
    db.execute("UPDATE appointments SET status = ? WHERE appointment_id = ?", new_status, id)
    return redirect(url_for("admin_appointments"))


@app.route("/appointment", methods=["POST"])
def book_appointment():
    full_name = request.form.get("full_name")
    phone = request.form.get("phone")
    email = request.form.get("email")
    preferred_date = request.form.get("preferred_date")
    preferred_time = request.form.get("preferred_time")
    message = request.form.get("message")

    existing = db.execute("SELECT * FROM appointments WHERE preferred_date = ? AND preferred_time = ? AND status = 'Confirmed'",
                          preferred_date, preferred_time)

    if existing:
        flash("This appointment time is already booked. Please choose another time.", "danger")
        return redirect(url_for("appointment"))

    db.execute("""
        INSERT INTO appointments (full_name, phone, email, preferred_date, preferred_time, message, status)
        VALUES (?, ?, ?, ?, ?, ?, 'Pending')
    """, full_name, phone, email, preferred_date, preferred_time, message)

    flash("Appointment request submitted successfully!", "success")
    return redirect(url_for("appointment"))


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("adminlog"))



ALLOWED_EXTENSIONS = {'pdf', 'docx', 'doc'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.errorhandler(500)
def internal_server_error(error):
    return render_template("500.html"), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)