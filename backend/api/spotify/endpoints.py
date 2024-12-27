import requests
import time
from datetime import datetime, timedelta
from flask import Blueprint, jsonify
import json
import os
from dotenv import load_dotenv

load_dotenv()

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
    print(SPOTIFY_CLIENT_ID)
    print(SPOTIFY_CLIENT_SECRET)
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


def fetch_spotify_playlist(playlist_id, force_update=False):
    print("Fetching Spotify playlist...")
    cache_dir = "backend/cached_playlists"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the cache directory exists
    filename = f"Playlist - {playlist_id}.json".replace(" ", "_")
    filepath = os.path.join(cache_dir, filename)

    # Check if cached file exists
    if not force_update and os.path.exists(filepath):
        with open(filepath, "r") as file:
            cached_data = json.load(file)

        # Check if cache is less than 24 hours old
        updated_at = datetime.fromisoformat(cached_data["updated_at"])
        if datetime.now() - updated_at < timedelta(hours=24):
            print("Returning cached playlist data.")
            return cached_data
    
    # First, get the playlist overview data
    endpoint = f"v1/playlists/{playlist_id}"
    playlist_overview_data = fetch_web_api(endpoint, "GET")
    playlist_overview_data = {
        "name": playlist_overview_data.get("name"),
        "external_urls": playlist_overview_data.get("external_urls"),
        "images": playlist_overview_data.get("images"),
        "owner": playlist_overview_data.get("owner"),
    }

    # Load existing data to preserve youtube_links
    existing_tracks = []  
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            existing_data = json.load(file)
            existing_tracks = existing_data.get("tracks", [])
    tracks_info = []
    offsetSpotify = 0
    limitSpotify = 100   
    totalSpotify = 9999999  # Arbitrary high value for total, this will get updated

    while offsetSpotify < totalSpotify:
        # Construct the correct API endpoint with the current offset and limit
        next_url = f"v1/playlists/{playlist_id}/tracks?offset={offsetSpotify}&limit={limitSpotify}"
        print("Grabbing page of results...", next_url)

        response_data = fetch_web_api(next_url, "GET")
        tracks_data = response_data.get("items", [])
        
        # Extract relevant track data
        for index, item in enumerate(tracks_data, start=offsetSpotify + 1):
            track = item["track"]
            track_name = track["name"]
            artists = [artist["name"] for artist in track["artists"]]
            external_url = track["external_urls"]["spotify"]
            track_image = track["album"]["images"][0]["url"] if track["album"]["images"] else None
            added_at = item["added_at"]  # Timestamp of when track was added
            
            # Check if the track exists in the existing data
            if existing_tracks:
                existing_track = next((t for t in existing_tracks if t["track_name"] == track_name), None)
                
                # If the track exists, preserve the existing youtube_links
                if existing_track:
                    youtube_links = existing_track.get("youtube_links", [])
                else:
                    youtube_links = []
            else:
                youtube_links = []
            tracks_info.append({
                "id": index,
                "track_name": track_name,
                "track_artists": artists,
                "external_url": external_url,
                "track_image": track_image,
                "added_at": added_at,
                "youtube_links": youtube_links  # Preserve existing youtube_links
            })

        # Update the offset for the next page
        offsetSpotify += limitSpotify
        
        # Get the total number of tracks and check if there are more pages
        totalSpotify = response_data.get("total", 0)
        print("Offset:", offsetSpotify)
        print("Limit:", limitSpotify)
        print("Total tracks:", totalSpotify)
        
        # Check if there's another page of results
        if offsetSpotify >= totalSpotify:
            break

        # Delay to avoid overwhelming the API
        time.sleep(2.5)
        print("-----------")
        
    # Sort the tracks by the 'added_at' field (most recent first)
    tracks_info.sort(key=lambda x: datetime.fromisoformat(x["added_at"].replace("Z", "+00:00")), reverse=True)

    # Build final structure and save to cache
    data = {
        "playlist_id": playlist_id,
        "overview": playlist_overview_data,
        "tracks": tracks_info,
        "updated_at": datetime.now().isoformat(),
    }

    # Save to JSON file
    with open(filepath, "w") as file:
        json.dump(data, file, indent=4)

    print("Returning fresh playlist data.")
    return data

# Example of the /get-playlist endpoint
@spotify_blueprint.route('/get-playlist/<playlist_id>')
def get_spotify_playlist(playlist_id):
    tracks_info = fetch_spotify_playlist(playlist_id)
    return jsonify({
        'message': 'Spotify Playlist received', 
        'playlist': tracks_info,
    })
