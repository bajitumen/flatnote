import os
import sys
import json
import requests

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required
from text2emotion import get_emotion

"""
import spotipy.util as util
import spotipy
from spotipy.oauth2 import SpotifyOAuth
"""

# Configure application
app = Flask(__name__)
db = SQL("sqlite:///journals.db")

"""
# The below client ID was given to us once we signed up on the Spotify for Developers page
os.environ["SPOTIPY_CLIENT_ID"] = "8c4b8f1854874908a7d8caf5b42d6abc"
os.environ["SPOTIPY_CLIENT_SECRET"]= "d4678e9cf01447f9bd2d76cf0e7d0119"
os.environ["SPOTIPY_REDIRECT_URI"]= "https://www.spotify.com/us/"
"""

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

# home page where you can submit your journal entry
@app.route("/")
@login_required
def index():
    return render_template("cover.html")

# login page
@app.route("/login", methods=["GET", "POST"])
def login():

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

# logout button
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

# unique results page generated after journal entry is submitted
@app.route("/results", methods=["GET", "POST"])
@login_required
def results():
    # if just types in /results into the url bar, redirect them to the home page
    if request.method == "GET":
        return redirect("/")
    # generate results by analyzing text entry
    if request.method == "POST":
        journal = request.form.get("entry") # text entry
        emotions = get_emotion(journal) # dictionary with the emotion values of the text entry
        angry = emotions["Angry"]
        fear = emotions["Fear"]
        happy = emotions["Happy"]
        sad = emotions["Sad"]
        surprise = emotions["Surprise"]

        # find the strongest emotion
        max_emotion = 0
        max_emotion_name = "ambivalent" # default emotion in case no emotions are detected
        for emotion in emotions:
            if emotions[emotion] > max_emotion:
                max_emotion = emotions[emotion]
                max_emotion_name = emotion

        # generate message and song genre depending on strongest emotion
        if max_emotion_name == "Happy":
            message = "You should be proud of feeling so upbeat! You are the life of the party and your journal entry reflects that."
            genre = 0
        elif max_emotion_name == "Angry":
            message = "It's okay to feel angry sometimes but don't let it consume your emotions. Just know that whatever you're angry at right now will pass with time"
            genre = 1
        elif max_emotion_name == "Fear":
            message = "We live in scary times and there is plenty to be afraid of but don't let that keep you down!"
            genre = 2
        elif max_emotion_name == "Sad":
            message = "Sadness is a natural part of life so if you are feeling down, don't feel bad. At the very least, the developers of this website hope you feel better."
            genre = 3
        elif max_emotion_name == "Surprise":
            message = "Wow! You seem to have a lively state of mind and many things are surprising to you at this moment. Hopefully good surprises!"
            genre = 4
        elif max_emotion == 0:
            message = "It looks like you're not really feeling anything right now..."

        # lowercase version of emotion name to put into html
        lower_max_emotion_name = max_emotion_name.lower()

        # put journal entry and emotions into the database
        db.execute("INSERT INTO journal (user_id, text, angry, fear, happy, sad, surprise) VALUES(?, ?, ?, ?, ?, ?, ?)", session["user_id"], journal, angry, fear, happy, sad, surprise)

        """
        # we considered creating an algorithm for valence, energy, danceability depending on emotions
        valence_score = (happy + 0.5 * surprise - 0.5 * angry - 0.5 * fear - sad + 1)/2
        energy_score = (happy + surprise + angry - 0.5 * fear - sad + 1)/2
        dance_score = (happy + 0.5 * surprise - angry - 0.5 * fear - sad + 1)/2

        # get the user's username
        username = request.form.get("spotify")
        # scope (catalog of songs being used) is user's library
        scope = 'user-library-read playlist-modify-public'
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
        sptoken = util.prompt_for_user_token(username, scope)

        if sptoken:
            playist_name = "flatNotes Generated Playlist"
            sp.user_playlist_create(username, name=playlist_name)
            list=[]
            endlist=[]
            results = sp.current_user_saved_tracks(limit=50)
            features = {}
            song_ids = []
            for item in results['items']:
                track = item['track']
                features = sp.audio_features(track['id'])
                for song in features:
                    if genre == 0:
                            # Angry
                        if song['energy'] > 0.7 and song['valence'] < 0.4:
                            song_ids.append(song['id'])
                    elif genre == 1:
                            # Sad
                        if song['energy'] < 0.5 and song['valence'] < 0.4:
                            song_ids.append(song['id'])
                    elif genre == 2:
                            # Happy
                        if song['valence'] > 0.4 and song['energy'] > 0.4:
                            song_ids.append(song['id'])
                    elif genre == 3:
                            # Fear
                        if song['valence'] < 0.5 and song['danceability'] < 0.5:
                            song_ids.append(song['id'])
                    elif genre == 4:
                            # Surprise
                        if song['valence'] > 0.6 and song['danceability'] > 0.6:
                            song_ids.append(song['id'])
        else:
            print("Token not working for " + username)

        # Make the playlist
        playlist = sp.user_playlist_create(username, public=True, description = "This playlist was made using flatNotes, a final project for CS50 developed by Baji Tumendemberel and William Zhu (2020)")
        playlistID = playlist['id']

        playlist = sp.user_playlist_add_tracks(username, playlistID, song_ids)
        """

        return render_template("results.html", emotions=emotions, lower_max_emotion_name=lower_max_emotion_name, message=message)

# about page
@app.route("/about")
def about():
    return render_template("about.html")

# past journal entries page
@app.route("/journal", methods=["GET", "POST"])
@login_required
def journal():
    if request.method == "POST":
        delete_id = request.form.get("delete")
        db.execute("DELETE FROM journal WHERE id = ?", delete_id)
        journals = db.execute("SELECT * FROM journal WHERE user_id = ?", session["user_id"])
        return render_template("journal.html", journals=journals)
    else:
        journals = db.execute("SELECT * FROM journal WHERE user_id = ?", session["user_id"])
        return render_template("journal.html", journals=journals)

#registration page
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        elif not request.form.get("confirmation"):
            return apology("must confirm password", 403)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("passwords must match", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username does not exist
        if len(rows) != 0:
            return apology("username taken", 403)

        # Insert new user into users
        user_id = db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", request.form.get(
            "username"), generate_password_hash(request.form.get("password")))

        # Remember which user has logged in
        session["user_id"] = user_id

        # Redirect user to home page
        return redirect("/")

    else:
        return render_template("register.html")

# "vibes" page with chart showing how the user's emotions have changed over time
@app.route("/vibes")
@login_required
def vibes():
    # dictionary with all the user's past emotions
    history = db.execute("SELECT date, angry, fear, happy, sad, surprise FROM journal WHERE user_id = ?", session["user_id"])

    # create lists with past data to insert into html chart
    date = []
    angry = []
    fear = []
    happy = []
    sad = []
    surprise = []
    for entry in history:
        date.append(entry["date"])
        angry.append(entry["angry"])
        fear.append(entry["fear"])
        happy.append(entry["happy"])
        sad.append(entry["sad"])
        surprise.append(entry["surprise"])

    # find the total number of journal entries to find width of chart
    num_entries = db.execute("SELECT COUNT(id) FROM journal WHERE user_id = ?", session["user_id"])
    total = num_entries[0]["COUNT(id)"]

    # if number of entries is less than or equal to 10, set width of chart to 600px
    if total <= 10:
        width = 600
    # if number of entries is greater than 10, make width of chart increase by 60px for each entry
    else:
        width = 60 * total
    # add the "px" for html formatting
    width_str = str(width) + "px"

    return render_template("vibes.html", date=date, angry=angry, fear=fear, happy=happy, sad=sad, surprise=surprise, width_str=width_str)

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)