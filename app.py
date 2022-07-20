import os

from cs50 import SQL
from flask import Flask, redirect, render_template, request, session
from flask_session import Session
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///users.db")

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    # Get users type to see whether or not to display songs library button
    if request.method == "GET":
        submitted = db.execute("SELECT type FROM users WHERE id = ?", session["user_id"])
        return render_template("index.html", submitted=submitted)

    # Allow user to go to quiz or library using buttons
    if request.method == "POST":
        if request.form.get("submit_quiz"):
            return redirect("/quiz")
        if request.form.get("submit_library"):
            return redirect("/library")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # return register template
    if request.method == "GET":
        return render_template("register.html")

    # register new user
    if request.method == "POST":
        # gather user input and look for usernames that match with user given username
        rows = db.execute("SELECT * FROM users WHERE username = ?",
                          request.form.get("username"))
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # check for errors
        if not request.form.get("username"):
            return apology("must provide username", 400)
        elif not request.form.get("password"):
            return apology("must provide password", 400)
        elif not request.form.get("confirmation"):
            return apology("must provide confirmation password", 400)
        elif not confirmation == password:
            return apology("passwords don't match", 400)
        elif len(rows) != 0:
            return apology("Username already taken", 400)

        # insert new user and password into users database and remember user is longed in
        else:
            logged_in = db.execute("INSERT INTO users (username, hash) VALUES (?,?)", username, generate_password_hash(request.form.get("password")))
            session["user_id"] = logged_in
        return  render_template("index.html")

@app.route("/quiz", methods=["GET", "POST"])
@login_required
def quiz():

    # Retrieve questions from questions database and display on quiz page
    row = db.execute("SELECT * FROM questions")
    if request.method == 'GET':
        return render_template('quiz.html', row=row)

    # Send user to results page when they submit the quiz
    if request.method == 'POST':
        return redirect('/results')

@app.route("/library", methods=["GET"])
@login_required
def library():

    # Retrieve songs corresponding to user's music artist type and display on library page
    songs = db.execute("SELECT * FROM songs WHERE type = (SELECT type FROM users WHERE id = ?)", session["user_id"])
    if request.method == 'GET':
        return render_template("library.html", songs=songs)

@app.route("/results", methods=["GET", "POST"])
@login_required
def results():

    # Create dict to allow for points to be associated with music artists based on user's responses
    types = {"Corey Taylor": 0, "Erykah Badu": 0, "NBA Youngboy": 0, "Playboi Carti": 0, "Olivia Rodrigo": 0, "Jacob Collier": 0}

    # Get length of questions of database
    length = db.execute("SELECT id FROM questions ORDER BY ID DESC")
    lenn = len(length) + 1

    # loop through all the quiz questions and increase music artists points based on user's responses submitted thorugh the form
    if request.method == 'POST':
        for i in range(lenn):
            k = str(i)
            if request.form.get(k) == "olivia":
                types["Olivia Rodrigo"] += 1
            if request.form.get(k) == "erykah":
                types["Erykah Badu"] += 1
            if request.form.get(k) == "corey":
                types["Corey Taylor"] += 1
            if request.form.get(k) == "youngboy":
                types["NBA Youngboy"] += 1
            if request.form.get(k) == "jacob":
                types["Jacob Collier"] += 1
            if request.form.get(k) == "playboi":
                types["Playboi Carti"] += 1

        # find music artist with the most points and set to variable
        max_key = max(types, key=types.get)

        # Update users database with type for current user
        db.execute("UPDATE users SET type = ? WHERE id = ?", max_key, session["user_id"])

        # Return results template with the user's quiz results
        result = db.execute("SELECT * FROM songs WHERE type = ?", max_key)
        return render_template("results.html", result=result, max_key=max_key)

    # Return results template if method is GET
    else:
        return render_template('results.html')

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

