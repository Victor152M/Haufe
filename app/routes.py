import datetime, os, gc, uuid
from app import app
from .database_functions import db_operation
from .helper_functions import login_required, allowed_file
from flask import render_template, request, flash, redirect, url_for, jsonify, session
from werkzeug.utils import secure_filename
from passlib.hash import sha256_crypt
from datetime import datetime


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        data = request.json
        feedback = data.get('feedback')

        if session['email'] and feedback:
            email = session['email']
            db_operation(f"INSERT INTO feedback (email, feedback) VALUES (%s, %s);", params=(email, feedback))

        elif feedback:
            db_operation(f"INSERT INTO feedback (feedback) VALUES (%s);", params=(feedback))

    links = []
    dates = []
    months = {
        "01": "ianuarie", "02": "februarie", "03": "martie", \
        "04": "aprilie", "05": "mai", "06": "iunie", "07": "iulie", \
        "08": "august", "09": "septembrie", "10": "octombrie", \
        "11": "noiembrie", "12": "decembrie"}

    events = db_operation("SELECT * FROM events;", fetch=True)

    if events:
        for event in events:
            links.append("/events/event" + str(event[0]))
        for event in events:
            month = months[str(event[4]).split('-')[1]]
            date = str(str(event[4]).split('-')[2]) + "-" + month \
                + "-" + str(str(event[4]).split('-')[0])
            dates.append(date)
        return render_template("index.html", events=events, links=links, dates=dates)
    return render_template("index.html")


@app.route("/post_event", methods=["GET", "POST"])
@login_required
def post_event():
    if request.method == "POST":
        # check if the post request has the file part
        if "image" not in request.files:
            #do flashes actually work?
            #do they do anything?
            flash("No file part")
            return redirect(request.url)
        title = request.form["title"]
        description = request.form["description"]
        image = request.files["image"]
        date = request.form["date"]

        #gettting location data
        country = request.form.get("country")
        city = request.form.get("city")
        venue = request.form.get("venue")

        location = country + ", " + city + ", " + venue 

        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if image.filename == '':
            flash("No selected file")
            return redirect(request.url)

        #making new lines actually work (for description)
        description = description.replace('\n', '<br>')

        #preprocessing the date for uploading to the database
        date = [int(x) for x in date.split("-")]
        date = f"{date[1]}-{date[2]}-{date[0]}"

        #responsabilities
        responsibilities = request.form.getlist('responsibilities[]')
        responsibility_details = request.form.getlist('responsibility_details[]')
        responsibilities_budgets = request.form.getlist('responsibility_budget[]')

        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            filename = str(uuid.uuid4()) + filename
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
            user_email = session['email']
            sql = "SELECT id FROM users WHERE email = %s;"
            parameters = [user_email]
            user_id = db_operation(sql=sql, params=parameters, fetch=True)
            user_id_str = str(user_id[0][0])

            sql = f"""
            INSERT INTO events (title, description, image_filepath, date, location, user_id)
            VALUES (%s, %s, %s, %s, %s, %s);
            """

            parameters = (title, description, image_path, date, location, user_id_str)

            db_operation(sql=sql, params=parameters)

            sql = """
            SELECT id FROM events 
            WHERE title = %s AND description = %s AND image_filepath = %s 
            AND date = %s AND location = %s AND user_id = %s
            ORDER BY id DESC LIMIT 1;
            """

            parameters = (title, description, image_path, date, location, user_id_str)
            event_id = db_operation(sql=sql, params=parameters, fetch=True)[0][0]

            for resp, details, budget in zip(responsibilities, responsibility_details, responsibilities_budgets):
                if resp.strip():
                    sql = """
                    INSERT INTO responsibilities (event_id, task_name, task_details, budget)
                    VALUES (%s, %s, %s, %s);
                    """
                    parameters = (event_id, resp.strip(), details.strip(), budget.strip())
                    db_operation(sql=sql, params=parameters)

            print("Event added successfuly")
            flash("The event was added successfully")
            return redirect(url_for("index"))
        else:
            flash('Invalid file type. Please upload an image.')
    return render_template("post_event.html")


@app.route("/events/event<int:event_id>", methods=["GET"])
def get_event(event_id):
    sql = "SELECT * FROM events WHERE id = %s;"
    parameters = [str(event_id)]
    event = db_operation(sql=sql, params=parameters, fetch=True)

    sql = """
    SELECT id, task_name, task_details, user_id, budget
    FROM responsibilities 
    WHERE event_id = %s 
    ORDER BY id;
    """
    parameters = [str(event_id)]
    responsibilities = db_operation(sql=sql, params=parameters, fetch=True)

    if responsibilities:
        names = []
        for responsibility in responsibilities:
            if responsibility[3]:
                sql = """ SELECT first_name FROM users WHERE id = %s;"""
                user_id = str(responsibility[3])
                first_name = db_operation(sql=sql, params=user_id, fetch=True)
                names.append(first_name[0][0])
            else:
                names.append(0)
    
    print(responsibilities)
    print(names)
    
    if responsibilities:
        return render_template("events/event.html", event=event, responsibilities=responsibilities, event_id=event_id, names=names)

    return render_template("events/event.html", event=event)


@app.route("/logout")
@login_required
def logout():
    session.clear()
    flash("You have been logged out")
    gc.collect()
    return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not db_operation("SELECT * FROM users WHERE email = %s;", params=[email], fetch=True):
            return jsonify({"success": False, "message": "Wrong password or user does not exist!"})

        password_hash_as_list = db_operation("SELECT password_hash FROM users WHERE email = %s;", params=[email], fetch=True)
        password_hash = password_hash_as_list[0][0]

        if sha256_crypt.verify(password, password_hash):
            session['logged_in'] = True
            first_name = db_operation("SELECT first_name FROM users WHERE email = %s;", params=[email], fetch=True)
            session['username'] = first_name
            session['email'] = email

            return jsonify({"success": True, "message": "Login successful", "redirect": url_for("account")})
        
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        first_name = request.form.get("first_name")
        last_name = request.form.get("last_name")
        email = request.form.get("email")
        password_hash = sha256_crypt.encrypt(request.form.get("password"))

        sql = f"SELECT * FROM users WHERE email = %s"
        parameters = (email)

        if db_operation(sql=sql, params=parameters, fetch=True):
            return jsonify({"success": False, "message": "Email already exists"})

        sql = f"""
            INSERT INTO users (first_name, last_name, email, password_hash)
            VALUES ('{first_name}', '{last_name}', '{email}', '{password_hash}');
            """

        parameters = (first_name, last_name, email, password_hash)
        print(parameters)

        db_operation(sql=sql, params=parameters)

        return jsonify({"success": True, "message": "Registration successful", "redirect": url_for("login")})

    return render_template("register.html")


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "POST":
        event_id = request.json.get('id')
        db_operation("DELETE FROM events WHERE id=%s;", params=[event_id], fetch=False)
        return jsonify({"status": True, "message": "Event deleted!"})
    username = session['username']
    email = session['email'] 
    user_id = db_operation("SELECT id FROM users WHERE email = %s;", params=[email], fetch=True)[0][0]
    events = db_operation("SELECT * FROM events WHERE user_id = %s;", params=[user_id], fetch=True)
    links = []

    if events:
        for event in events:
            links.append("/events/event" + str(event[0]))
        return render_template("account.html", username=username[0][0], email=email, events = events, links=links)

    return render_template("account.html", username=username[0][0], email=email)


@app.errorhandler(404)
def page_not_found(e):
    return render_template("404.html")


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {"png", "jpg", "jpeg", "webp"}


@app.route("/claim_responsibility", methods=["POST"])
def claim_responsibility():
    """Allows a logged-in user to claim a responsibility for a given event."""
    email = session.get("email")
    if not email:
        return jsonify({"error": "User not logged in"}), 401

    # Get the responsibility ID from the request JSON data
    responsibility_id = request.json.get("responsibility_id")

    sql = "SELECT id FROM users where email = %s;"

    user_id = db_operation(sql=sql, params=[email], fetch=True)
    
    # Update the responsibility in the database only if it's unclaimed (user_id is NULL)
    sql = "UPDATE responsibilities SET user_id = %s WHERE id = %s AND user_id IS NULL;"
    #user_id = str(user_id)
    parameters = (str(user_id[0][0]), str(responsibility_id))

    db_operation(sql=sql, params=parameters)

    return jsonify({"message": "Responsibility claimed successfully"}), 200
