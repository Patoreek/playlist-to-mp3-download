import requests
import time
from flask import Blueprint, jsonify
import os

SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')


# Global variables to store the token and its expiration time
spotify_token = None
token_expiry_time = 0

# Authorization blueprint
spotify_blueprint = Blueprint('spotify', __name__)

# Function to fetch the Spotify access token
def get_spotify_token():
    global spotify_token, token_expiry_time

    # Check if the token is still valid
    if spotify_token and time.time() < token_expiry_time:
        # If valid, return the cached token
        return spotify_token

    # If no valid token, fetch a new one
    url = "https://accounts.spotify.com/api/token"
    payload = {
        'grant_type': 'client_credentials',
        'client_id': SPOTIFY_CLIENT_ID,  
        'client_secret': SPOTIFY_CLIENT_SECRET
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
    }

    # Make the request to get the access token
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        # Extract the token and set the expiration time (1 hour)
        response_data = response.json()
        spotify_token = response_data.get('access_token')
        token_expiry_time = time.time() + response_data.get('expires_in', 3600)  # Default to 3600 seconds (1 hour)
        return spotify_token
    else:
        print(f"Error fetching token: {response.status_code}, {response.text}")
        return None

# Function to fetch data from the Spotify Web API
def fetch_web_api(endpoint, method, body=None):
    token = get_spotify_token()  # Fetch the access token (cached or new)

    if not token:
        return {'error': 'Unable to fetch access token'}

    headers = {
        'Authorization': f'Bearer {token}',
    }
    url = f'https://api.spotify.com/{endpoint}'
    response = requests.request(method, url, headers=headers, json=body)
    
    if response.status_code != 200:
        return {'error': 'Request failed', 'status_code': response.status_code, 'details': response.text}
    
    return response.json()


def fetch_spotify_playlist(playlist_id):
    print('fetching spotify playlist')
    endpoint = f'v1/playlists/{playlist_id}/tracks'
    response_data = fetch_web_api(endpoint, 'GET')
    playlistData = response_data.get('items', [])

    if playlistData:
        tracks_info = []
        
        # Loop through all tracks and extract required details
        for index, item in enumerate(playlistData, start=1):  # Start enumeration from 1
            track = item['track']
            
            track_name = track['name']
            artists = [artist['name'] for artist in track['artists']]
            external_url = track['external_urls']['spotify']
            track_image = track['album']['images'][0]['url'] if track['album']['images'] else None

            tracks_info.append({
                'id': index,  # Add unique ID
                'track_name': track_name,
                'track_artists': artists,
                'external_url': external_url,
                'track_image': track_image,
            })

        return tracks_info
    
# Example of the /get-playlist endpoint
@spotify_blueprint.route('/get-playlist/<playlist_id>')
def get_spotify_playlist(playlist_id):
    tracks_info = fetch_spotify_playlist(playlist_id)
        
    return jsonify({
        'message': 'Spotify Playlist received', 
        'playlist_id': playlist_id,
        'tracks': tracks_info,
    })
