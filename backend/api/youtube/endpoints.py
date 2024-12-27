import requests
import time
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import json
from backend.api.youtube.youtube_quota_manager import can_make_api_call, increment_quota_usage

load_dotenv()

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
youtube_blueprint = Blueprint('youtube', __name__)
    
# YouTube API URL
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"


# Initialize the quota tracker
DAILY_QUOTA_LIMIT = 10000  # Replace this with your actual daily quota limit
quota_used = 0  # Initialize at the start of the day

### Get Youtube Links from Songs string array
def get_youtube_links_from_songs(playlistId, offset = 0, pageSize = 50):
    quota_status = can_make_api_call()  # Get the quota status

      # If the API call is restricted due to quota limits, return None
    if quota_status["value"] == "restricted":
        print(f"API call restricted due to quota limits: {quota_status['message']}")
        return {"status": "restricted", "message": quota_status["message"]}

    # Optionally, print the status message for warnings
    elif quota_status["value"] in ["warning_75", "warning_50", "warning_25"]:
        print(f"Warning: Current YouTube quota status - {quota_status['message']}")
      
    results = []
    maxResults = 3

    cache_dir = "backend/cached_playlists"
    filename = f"Playlist - {playlistId}.json".replace(" ", "_")
    filepath = os.path.join(cache_dir, filename)

    # Load the playlist JSON
    with open(filepath, "r") as file:
        playlist_data = json.load(file)

    # Get the current page of tracks

    start_index = offset * pageSize
    end_index = start_index + pageSize
    tracks = playlist_data["tracks"][start_index:end_index]
    hasApiBeenCalled = False

    for track in tracks:
        # Skip tracks that already have YouTube links
        if len(track["youtube_links"]) >= maxResults:
            print(f"Skipping track: {track['track_name']} (YouTube links already present)")
            continue
        else:   
                print(f"Getting Youtube links for {track['track_name']}")

        # Query YouTube API
        query = f"{track['track_name']} {' '.join(track['track_artists'])} - Extended"
        params = {
            'part': 'snippet',
            'q': query,
            'key': YOUTUBE_API_KEY,
            'type': 'video',
            'maxResults': maxResults
        }
        response = requests.get(YOUTUBE_API_URL, params=params)
        hasApiBeenCalled = True
        print(f"Current track: {track['track_name']}")
        

        if response.status_code == 200:
            data = response.json()
            increment_quota_usage(100)
            top_videos = []
            for index, item in enumerate(data.get("items", [])):
                video_id = item["id"]["videoId"]
                video_title = item["snippet"]["title"]
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                thumbnails = item["snippet"]["thumbnails"]

                top_videos.append({
                    "title": video_title,
                    "url": video_url,
                    "thumbnails": {
                        "default": thumbnails.get("default", {}),
                        "medium": thumbnails.get("medium", {}),
                        "high": thumbnails.get("high", {})
                    },
                    "updated_at": datetime.now().isoformat(),
                    "selected": index == 0
                })
            # Append YouTube links to the track
            track["youtube_links"] = top_videos
        else:
            print(response.json())
            error_message = response.json().get('error', {}).get('message', 'Unknown error')
            error_reason = response.json().get('error', {}).get('errors', [{}])[0].get('reason', 'Unknown reason')
            print(f"Error fetching YouTube links for {track['track_name']}: {error_message}")
            print(f"Error reason: {error_reason}")
            return {"apiStatus": error_reason, "playlist_data": playlist_data}

        # Save updated playlist JSON
        with open(filepath, "w") as file:
            json.dump(playlist_data, file, indent=4)

    print("YouTube links updated in playlist JSON.")
    if (hasApiBeenCalled == False):
        quota_status['value'] = True
    return {"apiStatus": quota_status, "playlist_data": playlist_data}

@youtube_blueprint.route('/get-links', methods=['POST'])
def get_youtube_links():
    # Get the JSON data from the request
    data = request.get_json()
    # Ensure the data contains the 'songNames' field (an array of strings)
    if not data or 'playlistId' not in data:
        return jsonify({'message': 'Invalid request, no playlistId found'}), 400

    playlistId = data['playlistId']
    offset = data['offset']
    pageSize = data['pageSize']
    
    # Process the song names to add ' - Extended' to each one
    results = get_youtube_links_from_songs(playlistId, offset, pageSize)

    # Return the YouTube links in the response
    return jsonify(results)

### Update Selected Link
def update_select_link_in_json(playlistId, track, selectedVideo):
    try:
        cache_dir = "backend/cached_playlists"
        filename = f"Playlist - {playlistId}.json".replace(" ", "_")
        filepath = os.path.join(cache_dir, filename)

        # Check if the file exists
        if not os.path.exists(filepath):
            return {"status": "error", "message": f"File not found: {filepath}"}

        # Load the playlist JSON
        with open(filepath, "r") as file:
            playlist_data = json.load(file)

        tracks = playlist_data.get("tracks", [])
        if not tracks:
            return {"status": "error", "message": "No tracks found in the playlist."}

        # Find the track by id
        track_found = False
        for existing_track in tracks:
            if existing_track["id"] == track["id"]:
                track_found = True
                # Loop through youtube_links to update the selected field
                video_found = False
                for youtube_link in existing_track.get("youtube_links", []):
                    if youtube_link["url"] == selectedVideo["url"]:
                        video_found = True
                    youtube_link["selected"] = (youtube_link["url"] == selectedVideo["url"])

                if not video_found:
                    return {"status": "error", "message": "Selected video URL not found in youtube_links."}
                break

        if not track_found:
            return {"status": "error", "message": f"Track with ID {track['id']} not found."}

        # Save the updated playlist JSON back to the file
        with open(filepath, "w") as file:
            json.dump(playlist_data, file, indent=4)

        return {"status": "success", "message": f"Updated {track['track_name']} successfully."}

    except json.JSONDecodeError:
        return {"status": "error", "message": "Failed to parse the JSON file. Ensure it is properly formatted."}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}

@youtube_blueprint.route('/update-selected-link', methods=['PUT'])
def update_selected_link():
    print('Updating selected link...')
    # Get the JSON data from the request
    data = request.get_json()
    # Ensure the data contains the 'songNames' field (an array of strings)
    if not data or 'playlistId' not in data:
        return jsonify({'message': 'Invalid request, no playlistId found'}), 400

    playlistId = data['playlistId']
    track = data['track']
    selectedVideo = data['selectedVideo']
    
    # Process the song names to add ' - Extended' to each one
    results = update_select_link_in_json(playlistId, track, selectedVideo)

    # Return the YouTube links in the response
    return jsonify(results)


### Current Quota Limits
def get_current_quota_limit_data():
    cache_dir = "backend/data"
    filename = "youtube_quota_data.json"
    filepath = os.path.join(cache_dir, filename)

    # Check if the file exists
    if not os.path.exists(filepath):
        return {"status": "error", "message": f"File not found: {filepath}"}

    try:
        # Load the quota data JSON
        with open(filepath, "r") as file:
            quota_data = json.load(file)

        # Return the data along with a success status
        return {
            "status": "success",
            "data": {
                "quota_used": quota_data.get("quota_used"),
                "daily_quota_limit": quota_data.get("daily_quota_limit"),
                "updated_at": quota_data.get("updated_at"),
                "refreshed_on": quota_data.get("refreshed_on")
            }
        }

    except json.JSONDecodeError:
        return {"status": "error", "message": "Failed to parse the JSON file. Ensure it is properly formatted."}
    except Exception as e:
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}

  

@youtube_blueprint.route('/get-current-quota-limit', methods=['GET'])
def get_current_quota_limit():
    # Process the song names to add ' - Extended' to each one
    results = get_current_quota_limit_data()

    # Return the YouTube links in the response
    return jsonify(results)


