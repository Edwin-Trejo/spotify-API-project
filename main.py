import spotipy
import time
from spotipy.oauth2 import SpotifyOAuth
from flask import Flask, request, url_for, session, redirect

app = Flask(__name__)

app.config['SESSION_COOKIE_NAME'] = 'Spotify Cookie'

app.secret_key = 'fd21hd18u92gr37&#H!&@^$)6'

TOKEN_INFO = 'token_info'

@app.route('/')
def login():
    auth_url = create_spotify_oauth().get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirect_page():
    session.clear()
    code = request.args.get('code')
    token_info = create_spotify_oauth().get_access_token(code)
    session[TOKEN_INFO] = token_info
    return redirect(url_for('saved_songs', _external= True))

@app.route('/saveDiscoverWeekly')
def save_discover_weekly():

    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect('/')
    
    # create a Spotipy instance with the access token
    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.current_user()['id']

    # get the user's playlists
    current_playlists =  sp.current_user_playlists()['items']
    discover_weekly_playlist_id = None
    saved_weekly_playlist_id = None

    # find the Discover Weekly and Saved Weekly playlists
    for playlist in current_playlists:
        if(playlist['name'] == 'Modo prra'):
            discover_weekly_playlist_id = playlist['id']
        if(playlist['name'] == 'Saved Weekly'):
            saved_weekly_playlist_id = playlist['id']
    
    # if the Discover Weekly playlist is not found, return an error message
    if not discover_weekly_playlist_id:
        return 'Playlist not found.'
    
    if not saved_weekly_playlist_id:
        new_playlist=sp.user_playlist_create(user_id, 'Saved Weekly', True)
        saved_weekly_playlist_id = new_playlist['id']
    
    # get the tracks from the Discover Weekly playlist
    discover_weekly_playlist = sp.playlist_items(discover_weekly_playlist_id)
    song_uris = []
    for song in discover_weekly_playlist['items']:
        song_uri= song['track']['uri']
        song_uris.append(song_uri)
    
    # add the tracks to the Saved Weekly playlist
    sp.user_playlist_add_tracks(user_id, saved_weekly_playlist_id, song_uris, None)

    # return a success message
    return ('Playlist created successfully')


@app.route('/playlistFromLiked')
def saved_songs():

    try:
        token_info = get_token()
    except:
        print("User not logged in")
        return redirect('/')

    sp = spotipy.Spotify(auth=token_info['access_token'])
    user_id = sp.current_user()['id']

    current_playlists =  sp.current_user_playlists()['items']
    saved_songs_playlist_id = None
    

    for playlist in current_playlists:
        if(playlist['name'] == 'Saved Songs'):
            saved_songs_playlist_id = playlist['id']
        

    if not saved_songs_playlist_id:
        new_playlist = sp.user_playlist_create(user_id, 'Saved Songs', True)
        saved_songs_playlist_id = new_playlist['id']

    #get songs from liked songs playlist
    liked_songs = sp.current_user_saved_tracks()
    song_uris = []
    for song in liked_songs['items']:
        song_uri = song['track']['uri']
        song_uris.append(song_uri)

    #Check songs from target playlist
    target_playlist_tracks = sp.playlist_items(saved_songs_playlist_id)
    target_song_uris = []
    for song in target_playlist_tracks['items']:
        song_uri = song['track']['uri']
        target_song_uris.append(song_uri)

    #Check if songs from liked_songs are already in target playlist
    tracks_to_add = []
    for song in song_uris:
        if song not in target_song_uris:
            tracks_to_add.append(song)


    try:
        sp.user_playlist_add_tracks(user_id, saved_songs_playlist_id, tracks_to_add, None)
        return ("Liked songs added to playlist")
    except Exception as e:
        return (f"No new songs to add. Error:{str(e)}")
    
    
    


    



def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for('login', _external=False))

    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60 #checks if the difference between actual time is less than 60s
    if(is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])

    return token_info


def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = "675717e385344c2cbdac404d0b07953e",
        client_secret="bb6926a6cbcc4a5db9ca1c8fbc854cc4",
        redirect_uri = url_for('redirect_page', _external= True),
        scope= 'user-library-read playlist-modify-public playlist-modify-private user-library-modify'
        )

app.run(debug=True)