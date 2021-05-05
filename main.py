# CS1520
# Group 3 Project

from flask import Flask, render_template, request, redirect, session, make_response, jsonify
import spotipy
import os
import json 

from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
from dotenv import load_dotenv
from google.cloud import datastore
import random
from logins import get_salt, get_hashed_password, create_new_user, is_unique_username, check_password, is_unique_email, get_signed_url

app = Flask(__name__)
app.secret_key = '2\xe4\xf35\xda\xabv^ \xeaKt'

load_dotenv()
datastore_client = datastore.Client()
auth = False

# Spotify Authentication
client_credentials_manager = SpotifyClientCredentials()
spAuth = SpotifyOAuth(cache_path=".spotifycache", scope="playlist-modify-public")
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)

# Quiz questions
questions = {
    "What is your favorite genre of music?": ['rock', 'pop', 'country', 'hip-hop', 'r-n-b', 'indie', 'techno', 'jazz', 'afrobeat', 'soul', 'gospel'],
    "How many songs should be in the finished playlist?": [10, 20, 30, 40],
    "Which of these artists would you be most likely to listen to?": ['The Beatles', 'Taylor Swift', 'The Chicks', 'Eminem', 'Beyonce', 'Coldplay', 'Daft Punk', 'Kamasi Washington', 'Wizkid', 'Janelle Monae', 'Kirk Franklin'],
    "Based on artist selected would you like for the playlist to have related artists included?": ['Yes', 'No'], 
}

@app.route("/")
def home():
    user = get_user()
    if user is None:
        return render_template("index.html", auth=False)
    else:
        return render_template("index.html", auth=True, user=user)

@app.route("/questionnaire")
def questionnaire():
    user = get_user()
    if user is None:
        return redirect("/login")
    else:
        return render_template("questionnaire.html", questions=questions, auth=True, user=user)

@app.route("/quizoutput", methods=['POST'])
def quizoutput():
    answerlist = []
    for i in questions.keys():
        answered = request.form[i]
        # print(answered)
        answerlist.append(answered)
    return playlist(quiz_answers=answerlist)

@app.route("/playlist")
def playlist(*args, **kwargs):
    quiz_answers = kwargs.get('quiz_answers', [])
    try:
        num_songs = int(quiz_answers[1])
    except:
        num_songs = 10

    try:
        genres = [quiz_answers[0]]
        # print ("genres = " + str(genres))
    except:
        genres = ['hip-hop']

    try:
        artist = quiz_answers[2]
        artist_top_track = find_artist_top_tracks(artist, country="US")
    except:
        artist_top_track = None

    related_artist_tracks = find_related_artist_tracks(artist, quiz_answers[3])

    # Set up recommended playlist & find ideal song proportion
    recommended_playlist = []
    proportion = int(num_songs*.2)
    num_songs = num_songs - proportion

    # Add related artist tracks
    if related_artist_tracks:
        add_songs_from_json(related_artist_tracks, proportion, recommended_playlist)
        num_songs = num_songs - proportion

    # Add artist top tracks
    add_songs_from_json(artist_top_track, proportion, recommended_playlist)

    # Add recommended tracks
    recommended_songs = sp.recommendations(None, genres, None, num_songs)
    add_songs_from_json(recommended_songs, num_songs, recommended_playlist)
    random.shuffle(recommended_playlist)
    return render_template("playlist.html", playlist=recommended_playlist, json_playlist=json.dumps(recommended_playlist), auth=True, user=get_user())

# Get artist id from string of artist's name
def find_artist_id(artist):
    switch = {
        'The Beatles': '3WrFJ7ztbogyGnTHbHJFl2',
        'Taylor Swift': '06HL4z0CvFAxyc27GXpf02',
        'The Chicks': '25IG9fa7cbdmCIy3OnuH57',
        'Eminem': '7dGJo4pcD2V6oG8kP0tJRR',
        'Beyonce': '6vWDO969PvNqNYHIOW5v0m',
        'Coldplay': '4gzpq5DPGxSnKTe4SA8HAU',      
        'Daft Punk': '4tZwfgrHOc3mvqYlEYSvVi',
        'Kamasi Washington': '6HQYnRM4OzToCYPpVBInuU',
        'Wizkid': '3tVQdUvClmAT7URs9V3rsp',
        'Janelle Monae': '6ueGR6SWhUJfvEhqkvMsVs',
        'Kirk Franklin': '4akybxRTGHJZ1DXjLhJ1qu',
    }
    return switch.get(artist, None)

# Get top tracks from related artists if user wants them included
def find_related_artist_tracks(artist, related_yn):
    # Check if user's answer is yes for if they want tracks from related artists 
    if related_yn=='Yes':
        # Get id for the artist
        artist_id = find_artist_id(artist)
        # Spotipy function for get related artists
        related_artists = sp.artist_related_artists(artist_id)
        # Get ids of all the artists
        related_artist_ids = []    
        for artist in related_artists["artists"]:
            related_artist_ids.append(artist["id"])
        id = random.choice(related_artist_ids) 
        # Get top tracks for a random one of those artists
        result = sp.artist_top_tracks(id, 'US')  
    else:
        result = None  
    return result

# JSON Parsing function for Spotify API Output
# Adds songs to destination data structure
def add_songs_from_json(json, num_songs, destination):
    tracks = json['tracks'][0:num_songs]    
    for track in tracks:
        track_id = track['id']
        album_name = track['album']['name']
        artist_names = []
        for artist in track['artists']:
            artist_names.append(artist['name'])
        track_name = track['name']  
        track_link = track['external_urls']['spotify']
        image = track['album']['images'][0]['url']
        
        destination.append({
            "id": track_id,
            "album": album_name,
            "artists": artist_names,
            "track": track_name,
            "link": track_link,
            "img": image
        })    
    return destination

# Gets top tracks for artists based on name
def find_artist_top_tracks(artist_name, country="US"):
    if artist_name == 'The Beatles':
        result = sp.artist_top_tracks('3WrFJ7ztbogyGnTHbHJFl2', 'US')   
    elif artist_name == 'Taylor Swift':
        result = sp.artist_top_tracks('06HL4z0CvFAxyc27GXpf02', 'US')       
    elif artist_name == 'The Chicks':
        result = sp.artist_top_tracks('25IG9fa7cbdmCIy3OnuH57', 'US')       
    elif artist_name == 'Eminem':
        result = sp.artist_top_tracks('7dGJo4pcD2V6oG8kP0tJRR', 'US')     
    elif artist_name == 'Beyonce':
        result = sp.artist_top_tracks('6vWDO969PvNqNYHIOW5v0m', 'US')       
    elif artist_name == 'Coldplay':
        result = sp.artist_top_tracks('4gzpq5DPGxSnKTe4SA8HAU', 'US')       
    elif artist_name == 'Daft Punk':
        result = sp.artist_top_tracks('4tZwfgrHOc3mvqYlEYSvVi', 'US')      
    elif artist_name == 'Kamasi Washington':
        result = sp.artist_top_tracks('6HQYnRM4OzToCYPpVBInuU', 'US')       
    elif artist_name == 'Wizkid':
        result = sp.artist_top_tracks('3tVQdUvClmAT7URs9V3rsp', 'US')      
    elif artist_name == 'Janelle Monae':
        result = sp.artist_top_tracks('6ueGR6SWhUJfvEhqkvMsVs', 'US')       
    elif artist_name == 'Kirk Franklin':
        result = sp.artist_top_tracks('4akybxRTGHJZ1DXjLhJ1qu', 'US')
    else:
        pass
    return result

@app.route("/saveplaylist", methods=['POST'])
def save_playlist():
    # Get playlist info from form
    json_playlist = request.form['save']
    playlist = json.loads(json_playlist)
    playlist_name = request.form['playlist-name']

    # Add playlist to Datastore for user
    username = get_user()
    datastore_playlist = datastore.Entity(datastore_client.key("UserPlaylists"))
    datastore_playlist.update(
        {
            "username": username,
            "playlist": playlist,
            "name": playlist_name
        }
    )
    datastore_client.put(datastore_playlist)  
    return redirect("/profile")

@app.route("/profile")
def profile():
    user = get_user()
    if user is None:
        return redirect("/login")
    else:
        # Get user data and playlists from Datastore
        userQuery = datastore_client.query(kind="UserProfile")
        userQuery.add_filter("username", "=", user)
        userInfo = list(userQuery.fetch())
        userData = userInfo[0]
        playlistQuery = datastore_client.query(kind="UserPlaylists")
        playlistQuery.add_filter("username", "=", user)
        playlists = list(playlistQuery.fetch())

    # Spotify Auth
    spUrl = spAuth.get_authorize_url()
    login_spotify()
    access_spotify = is_logged_in()

    return render_template("profile.html", playlists=playlists, userInfo=userData, auth=True, user=user, spAuthURL=spUrl, spotifyStatus=access_spotify)

@app.route("/viewplaylist/<playlist_id>")
def view_playlist(playlist_id):
    # Get playlist from Datastore with id to display
    playlist_key = datastore_client.key("UserPlaylists", int(playlist_id))
    playlist = datastore_client.get(playlist_key)
    return render_template("view_playlist.html", playlist=playlist, auth=True, user=get_user())

@app.route("/addtospotify/<playlist_id>")
def add_playlist_to_spotify(playlist_id):
    # Get access to Spotify
    access_token = login_spotify()
    spToken = spotipy.Spotify(access_token)
    if spToken:
        # Get playlist from database
        playlist_key = datastore_client.key("UserPlaylists", int(playlist_id))
        playlist = datastore_client.get(playlist_key)
        # Create playlist for logged in user using playlist name
        user_id = spToken.me()['id']
        new_spotify_playlist = spToken.user_playlist_create(user_id, playlist["name"])
        # Get playlist id on Spotify
        new_playlist_id = new_spotify_playlist["id"]
        # Get track ids from all tracks in playlist
        tracks_list = list(playlist["playlist"])
        track_ids = []
        for track in tracks_list:
            track_ids.append(track["id"])
        # Add tracks to playlist
        spToken.playlist_add_items(new_playlist_id, track_ids)
    return redirect("/profile")

@app.route("/deleteplaylist/<playlist_id>")
def delete_playlist(playlist_id):
    playlist_key = datastore_client.key("UserPlaylists", int(playlist_id))
    datastore_client.delete(playlist_key)
    return redirect("/profile")

@app.route("/logoutspotify")
def logoutspotify():
    logout_spotify()
    return redirect("/profile")

def login_spotify():
    access_token = ""
    # Check if there is token in session
    token_info = session.get("token_info", None)

    # If in session, check if token is expired and refresh it
    if token_info:
        if spAuth.is_token_expired(token_info):
            token_info = spAuth.refresh_access_token(token_info['refresh_token'])
        access_token = token_info['access_token']
    else:
        # If not in session, get code from redirected url
        code = request.args.get("code")
        if code:
            # Get access token from code
            try:
                token_info = spAuth.get_access_token(code)
                access_token = token_info['access_token']
                session['token_info'] = token_info
            except:
                access_token = ""

    # Return access token or None if empty - user didn't get auth yet
    if access_token:
        return access_token
    else:
        return None

def logout_spotify():
    session["token_info"] = None
    return redirect("/profile")

# Return status of Spotify login - True if token is valid,
# False if no token or expired token
def is_logged_in():
    token_info = session.get("token_info", None)

    if token_info:
        if spAuth.is_token_expired(token_info):
            return False
        return True
    else:
        return False

""" Profile Login """
@app.route("/login", methods=["GET"])
def login_profile():
    return render_template("login.html")

@app.route("/login", methods=["POST"])
def user_logon():
    username = request.form.get("username")    
    password = request.form.get("password")

    if(not check_password(username, password)):
        return render_template("login.html", error="Incorrect username or password", auth=False)
    else:
        session["user"] = username
        return render_template("index.html", auth=True, user=username)

""" Profile Signup """
@app.route("/signup", methods=["GET"])
def signup_service():
    return render_template("signup.html")

@app.route("/signup", methods=["POST", "PUT"])
def handle_signup():
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")

    if(is_unique_username(username) == False or is_unique_email(email) == False):
        return render_template("signup.html", error="Sorry the username or email is already in use")
    
    salt = get_salt()
    hashed_password = get_hashed_password(password, salt)
    create_new_user(username, email, hashed_password, salt)
    set_user(username)
    
    return render_template("index.html", auth=True, user=get_user())

# Route that is no longer utilized.
@app.route("/get_signed_url", methods=["PUT"])
def get_signedurl():
    print("Entering get_signedurl")
    filename = request.json["filename"]
    data_type = request.json["contentType"]
    if not (filename and type):
        # One of the fields was missing in the JSON request
        os.abort()

    profile_url = get_signed_url(filename, data_type)
    return jsonify({"signedUrl": profile_url})

@app.route("/logout")
def handle_logout():
    session.clear()
    return redirect("/")

def get_user():
    return session.get("user", None)

def set_user(username):
    session["user"] = username

def get_profile_pic_name():
    return session.get("profile_pic_name", None)

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8081, debug=True)