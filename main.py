import requests
from urllib.parse import quote
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware


def get_user_profile(auth_header):
    endpoint = 'https://api.spotify.com/v1/me'
    profile_res = requests.get(endpoint, headers=auth_header)
    profile_data = profile_res.json()

    return profile_data


def get_playlists(auth_header, offset=0):
    """Lists the current user's playlists"""
    endpoint = f'https://api.spotify.com/v1/me/playlists?offset={offset}'
    playlists_res = requests.get(endpoint, headers=auth_header)
    playlist_data = playlists_res.json()

    current_user_id = get_user_profile(auth_header)['id']

    playlists = []
    for playlist in playlist_data['items']:
        if playlist['owner']['id'] == current_user_id:
            playlists.append({
                'id': playlist['id'],
                'name': playlist['name']
            })

    return playlists


def generate_track_dict(track_list):
    tracks = []
    for track in track_list:
        if track['preview_url'] is not None:
            tracks.append({
                'id': track['id'],
                'uri': track['uri'],
                'name': track['name'],
                'preview_url': track['preview_url'],
                'image': track['album']['images'][0],
                'artists': list(map(lambda x: x['name'], track['artists']))
            })

    return tracks


def get_tracks(auth_header, seed_artists, seed_genres, seed_tracks):
    """Gets track recommendation based on provided seeds"""
    endpoint = f'https://api.spotify.com/v1/recommendations?seed_artists={",".join(seed_artists)}&seed_genres={",".join(seed_genres)}&seed_tracks={",".join(seed_tracks)}'
    recommendations_res = requests.get(endpoint, headers=auth_header)
    recommendations = recommendations_res.json()
    tracks = generate_track_dict(recommendations['tracks'])
    return tracks


def add_to_playlist(auth_header, track_uri, playlist_id):
    """Add a specified track to a specified playlist"""
    endpoint = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?uris={quote(track_uri)}'
    requests.post(endpoint, headers=auth_header)


def get_genre_seeds(auth_header):
    """Gets a list of available seeds"""
    endpoint = 'https://api.spotify.com/v1/recommendations/available-genre-seeds'
    genres_red = requests.get(endpoint, headers=auth_header)
    genres = genres_red.json()
    return genres['genres']


def search(auth_header, query: str, search_type: str):
    """Search for tracks/artists with a given query"""
    endpoint = f'https://api.spotify.com/v1/search?q={quote(query)}&type={search_type}'
    search_res = requests.get(endpoint, headers=auth_header)
    results = search_res.json()

    if search_type == 'track':
        return generate_track_dict(results['tracks']['items'])
    else:
        return list(
            map(lambda x: {'id': x['id'], 'name': x['name'], 'images': x['images'], 'genres': x['genres']},
                results['artists']['items']))


app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/search/{search_type}/{query}")
async def search_item(token: str, query: str, search_type: str):
    auth_header = {'Authorization': f'Bearer {token}'}
    return search(auth_header, query, search_type)


@app.get("/genres")
async def get_genres(token: str):
    auth_header = {'Authorization': f'Bearer {token}'}
    return get_genre_seeds(auth_header)


@app.get("/recommend")
def get_track_recommendations(token: str, artists: list = Query(['3MZsBdqDrRTJihTHQrO6Dq']),
                              genres: list = Query(['rap']),
                              tracks: list = Query(['1jcNHi5D96aaD0T5f1OjFY'])):
    auth_header = {'Authorization': f'Bearer {token}'}
    return get_tracks(auth_header, artists, genres, tracks)


@app.get("/playlists")
def get_user_playlists(token: str):
    auth_header = {'Authorization': f'Bearer {token}'}
    return get_playlists(auth_header)


@app.get("/add_playlist/{playlist_id}/{track_uri}")
def add_track_playlist(token: str, playlist_id: str, track_uri: str):
    auth_header = {'Authorization': f'Bearer {token}'}
    return add_to_playlist(auth_header, track_uri, playlist_id)
