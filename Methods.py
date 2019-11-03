import spotipy
import sys
import random
import json
from threading import Thread
import concurrent.futures
import spotipy.util as util


def authenticate_spotify(token):
    print("Connecting to Spotify....")
    print()
    sp = spotipy.Spotify(auth=token)
    return sp

def _get_top_artists(sp, term):
    top_artists = set()
    top_artists_data = sp.current_user_top_artists(limit=50, time_range=term)["items"]
    for artist_data in top_artists_data:
        top_artists.add(artist_data["id"])
    return top_artists

def _get_followed_artists(sp):
    followed_artists = set()
    followed_artists_data = sp.current_user_followed_artists(limit=50)["artists"]
    for artist_data in followed_artists_data["items"]:
        followed_artists.add(artist_data["id"])
    return followed_artists

def aggregate_top_artists(sp):
    followed_artists = set()
    top_artists = set()
    print("Getting your top artists....")
    print()
    print("Getting your followed artists....")
    print()
    terms = ["short_term", "medium_term"]
    with concurrent.futures.ThreadPoolExecutor() as executor:
        f1 = [executor.submit(_get_top_artists, sp, term) for term in terms]
        f2 = executor.submit(_get_followed_artists, sp)
        for fs in concurrent.futures.as_completed(f1):
            top_artists = top_artists.union(fs.result())
        followed_artists = followed_artists.union(f2.result())
    return followed_artists.union(top_artists)

def _get_top_related_artists(sp, artist, top_related_artists):
    related_artists = sp.artist_related_artists(artist)["artists"]  
    for artist in related_artists:
        top_related_artists.add(artist["id"])

"""returns a set of related artists to your top artists """
def aggregate_top_related_artists(sp, top_artists):
    print("Getting related artists....")
    print()

    # Set() ensures uniqueness of each element in case duplicates
    top_related_artists = set()
    threads = list()
    for artist in top_artists:
        t = Thread(target=_get_top_related_artists, args=(sp, artist, top_related_artists))
        t.start()
        threads.append(t)

    for thread in threads:
        thread.join()
    
    return top_related_artists
    
def aggregate_top_tracks(sp, all_artists):
    print("Getting top tracks....")
    print()
    top_tracks = list()
    for artist in all_artists:
        top_tracks_data = sp.artist_top_tracks(artist)["tracks"]
        for track in top_tracks_data:
            top_tracks.append(track["id"])
    return top_tracks

def cluster(top_tracks, n=50):
    # Returns top tracks in a cluster of 100
    cluster = []
    for i in range(0, len(top_tracks), n):
        cluster.append(top_tracks[i:i+n])
    return cluster 


def select_tracks(sp, top_tracks, mood):
    print("Selecting tracks....")
    print()
    selected_tracks = []

    # shuffle top tracks 
    track_group = cluster(top_tracks)
    for tracks in track_group:
        track_data_all = sp.audio_features(tracks)
        for track_data in track_data_all:
            try:
                    if mood <= 0.10:
                        if (0 <= track_data["valence"] <= (mood + 0.05) 
                            and track_data["danceability"] <= (mood + 0.2) 
                            and track_data["energy"] <= (mood+ 0.1)):
                                selected_tracks.append(track_data["uri"])
                    elif mood <= 0.25:
                        if ((mood - 0.05) <= track_data["valence"] <= (mood + 0.05)
                            and track_data["danceability"] <= (mood + 0.2)
                            and track_data["energy"] <= (mood + 0.1)):
                                selected_tracks.append(track_data["uri"])
                    elif mood <= 0.50:
                        if ((mood - 0.05) <= track_data["valence"] <= (mood + 0.05)
                            and track_data["danceability"] <= (mood)
                            and track_data["energy"] <= (mood + 0.1)):
                                selected_tracks.append(track_data["uri"])
                    elif mood <= 0.75:
                        if ((mood - 0.05) <= track_data["valence"] <= (mood + 0.05)
                            and track_data["danceability"] >= (mood)
                            and track_data["energy"] >= (mood - 0.1)):
                                selected_tracks.append(track_data["uri"])
                    elif mood <= 0.90:
                        if ((mood - 0.05) <= track_data["valence"] <= (mood + 0.05)
                            and track_data["danceability"] >= (mood - 0.3)
                            and track_data["energy"] >= (mood - 0.2)):
                                selected_tracks.append(track_data["uri"])
                    else:
                        if ((mood - 0.1) <= track_data["valence"] <= 1
                            and track_data["danceability"] >= (mood - 0.4)
                            and track_data["energy"] >= (mood - 0.3)):
                                selected_tracks.append(track_data["uri"])
            except:
                continue
    random.shuffle(selected_tracks)
    return selected_tracks[0:32]

def create_playlist(sp, mood):
    top_artists = aggregate_top_artists(sp)
    top_related_artists = aggregate_top_related_artists(sp, top_artists)
    all_artists = list(top_artists.union(top_related_artists))
    top_tracks = aggregate_top_tracks(sp, all_artists)
    selected_tracks = select_tracks(sp, top_tracks, float(mood))
    
    print("Creating playlist....")
    print()

    user_id = sp.current_user()["id"]
    playlist_id = sp.user_playlist_create(user_id, "Moodify "+str(mood))["id"]
    random.shuffle(selected_tracks)
    sp.user_playlist_add_tracks(user_id, playlist_id, selected_tracks[0:30])

def Moodify(token):
    # create spotify object and authenticate
    spotify_object = authenticate_spotify(token)
    mood = input("Enter mood (from 0.0 to 1.0): ")
    print()
    create_playlist(spotify_object, mood)
