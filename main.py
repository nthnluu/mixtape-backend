import requests
from urllib.parse import quote
from fastapi import FastAPI, Query
from typing import List

auth_header = {
    'Authorization': f'Bearer TOKEN'}


def get_playlists(current_user_id, offset=0):
    """Lists the current user's playlists"""
    endpoint = f'https://api.spotify.com/v1/me/playlists?offset={offset}'
    playlists_res = requests.get(endpoint, headers=auth_header)
    playlist_data = playlists_res.json()

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


def get_tracks(seed_artists, seed_genres, seed_tracks):
    """Gets track recommendation based on provided seeds"""
    endpoint = f'https://api.spotify.com/v1/recommendations?seed_artists={",".join(seed_artists)}&seed_genres={",".join(seed_genres)}&seed_tracks={",".join(seed_tracks)}'
    recommendations_res = requests.get(endpoint, headers=auth_header)
    recommendations = recommendations_res.json()
    tracks = generate_track_dict(recommendations['tracks'])
    return tracks


def add_to_playlist(track_uri, playlist_id):
    """Add a specified track to a specified playlist"""
    endpoint = f'https://api.spotify.com/v1/playlists/{playlist_id}/tracks?uris={quote(track_uri)}'
    requests.post(endpoint, headers=auth_header)


def get_genre_seeds():
    """Gets a list of available seeds"""
    endpoint = 'https://api.spotify.com/v1/recommendations/available-genre-seeds'
    genres_red = requests.get(endpoint, headers=auth_header)
    genres = genres_red.json()
    return genres['genres']


def search(query: str, search_type: str):
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


@app.get("/search/{search_type}/{query}")
async def search_item(query: str, search_type: str):
    return search(query, search_type)


@app.get("/genres")
async def get_genres():
    return get_genre_seeds()


@app.get("/recommend")
def get_track_recommendations(artists: list = Query(['3MZsBdqDrRTJihTHQrO6Dq']), genres: list = Query(['rap']),
                              tracks: list = Query(['1jcNHi5D96aaD0T5f1OjFY'])):
    return get_tracks(artists, genres, tracks)


@app.get("/playlists/{user_id}")
def get_user_playlists(user_id: str):
    return get_playlists(user_id)

# print(get_playlists('21uomo3aooifwq2fpx273m4wa', 20))
# print(get_tracks(['3MZsBdqDrRTJihTHQrO6Dq'], ['rap'], ['1jcNHi5D96aaD0T5f1OjFY']))
# print(search('joji', 'artist'))
