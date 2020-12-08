import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
from text2emotion import get_emotion

# Configure application
app = Flask(__name__)
db = SQL("sqlite:///journals.db")

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

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
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

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

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        return render_template("cover.html")
    if request.method == "POST":
        journal = request.form.get("entry")
        user_id = db.execute("INSERT INTO journal (user_id, journal) VALUES(?, ?)", session["user_id"], journal)
        return redirect("/")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/journal", methods=["GET", "POST"])
@login_required
def journal():
    return render_template("journal.html")
    journal = request.form.get("entry")
    db.execute("INSERT INTO journal (journal) VALUES(?)", journal)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    if request.method == "POST":
        # Ensure username is filled out
        if not request.form.get("username"):
            return apology("Must register a username", 403)

        # Ensure password is filled out
        elif not request.form.get("password"):
            return apology("Must register a password", 403)

        elif not request.form.get("confirmation"):
            return apology("Must confirm password", 403)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("Passwords do not match", 403)
            
        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username does not exist
        if len(rows) != 0:
            return apology("username taken", 403)

        elif request.form.get("password") in db.execute("SELECT hash FROM users"):
            return apology("Password has already been taken", 403)

        else:
            username = request.form.get("username")
            password = request.form.get("password")
            hashedpassword = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            user_id = db.execute("INSERT INTO users (username, hash) VALUES(?,?)", username, hashedpassword)
            if not user_id:
                return apology("Username taken", 403)
            return redirect("/")
            session["user_id"] = user_id




