import requests
import time
from flask import Blueprint, jsonify, request
import os

YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')
# Authorization blueprint
youtube_blueprint = Blueprint('youtube', __name__)
    
# YouTube API URL
YOUTUBE_API_URL = "https://www.googleapis.com/youtube/v3/search"

def get_youtube_links_from_songs(songs):
    results = []
    maxResults = 3
    for song in songs:
        print(song)
        # Make a request to the YouTube API for each song
        params = {
            'part': 'snippet',
            'q': song['name'],
            'key': YOUTUBE_API_KEY,
            'type': 'video',
            'maxResults': maxResults
        }
        response = requests.get(YOUTUBE_API_URL, params=params)
        if response.status_code == 200:
            # Parse the response JSON
            data = response.json()
            top_videos = []
            for item in data.get('items', []):
                video_id = item['id']['videoId']
                video_title = item['snippet']['title']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                thumbnails = item['snippet']['thumbnails']  # Includes all thumbnail sizes
                top_videos.append({
                    'title': video_title,
                    'url': video_url,
                    'thumbnails': {
                        'default': thumbnails.get('default', {}),
                        'medium': thumbnails.get('medium', {}),
                        'high': thumbnails.get('high', {})
                    }
                })
            results.append({'query': song, 'videos': top_videos})
        else:
            # Handle API errors
            results.append({'query': song, 'error': response.json().get('error', {}).get('message', 'Unknown error')})

    return results

# def get_youtube_links_from_songs(song_names):
#     # Process only the first song in the list for testing
#     if not song_names:
#         return {'error': 'No songs provided'}
    
#     song = song_names[0]  # Use only the first song
#     params = {
#         'part': 'snippet',
#         'q': song,
#         'key': YOUTUBE_API_KEY,
#         'type': 'video',
#         'maxResults': 3  # Fetch only one result
#     }
#     response = requests.get(YOUTUBE_API_URL, params=params)

#     if response.status_code == 200:
#         # Parse the response JSON
#         data = response.json()
#         if data.get('items'):  # Check if there are any results
#             item = data['items'][0]  # Get the first (and only) result
#             video_id = item['id']['videoId']
#             video_title = item['snippet']['title']
#             video_url = f"https://www.youtube.com/watch?v={video_id}"
#             return {
#                 'query': song, 
#                 'video': {'title': video_title, 'url': video_url}
#             }
#         else:
#             return {'query': song, 'error': 'No results found'}
#     else:
#         # Handle API errors
#         return {'query': song, 'error': response.json().get('error', {}).get('message', 'Unknown error')}


@youtube_blueprint.route('/get-links', methods=['POST'])
def get_youtube_links():
    # Get the JSON data from the request
    data = request.get_json()
    # Ensure the data contains the 'songNames' field (an array of strings)
    if not data or 'songNames' not in data:
        return jsonify({'message': 'Invalid request, no songNames found'}), 400

    song_names = data['songNames']
    
    # Process the song names to add ' - Extended' to each one
    youtube_links = get_youtube_links_from_songs(song_names)

    # Return the YouTube links in the response
    return jsonify({
        'message': 'Youtube Links created!',
        'tracks': youtube_links,
    })