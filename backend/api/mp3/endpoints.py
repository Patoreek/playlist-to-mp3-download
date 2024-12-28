from flask import Blueprint, jsonify, send_file
import zipfile
import json
import os
import re
from pytubefix import YouTube
from pytubefix.cli import on_progress
from pytube.innertube import _default_clients

_default_clients["ANDROID_MUSIC"] = _default_clients["ANDROID_CREATOR"]

mp3_blueprint = Blueprint('mp3', __name__)

def download_mp3(youtube_video, output_file):
    print("Downloading mp3...")
    url = youtube_video["youtube_url"]
    trackName = youtube_video["track_name"] + " - " + youtube_video["track_artists"] + " - YT.m4a"
    trackName = re.sub(r'[<>:"/\\|?*]', '', trackName)  # Remove invalid characters
    trackName = trackName.strip()  # Remove leading/trailing whitespace

    yt = YouTube(url, on_progress_callback=on_progress, use_oauth=True)
    print(yt.title)

    ys = yt.streams.get_audio_only()
    ys.download(output_path=output_file, filename=trackName)
        
    print(f"MP3 downloaded and saved as {output_file}")

def generate_mp3_files(playlist_id):
    print("Generating MP3 Files from playlist...")
    cache_dir = "backend/cached_playlists"
    os.makedirs(cache_dir, exist_ok=True)  # Ensure the cache directory exists
    filename = f"Playlist - {playlist_id}.json".replace(" ", "_")
    filepath = os.path.join(cache_dir, filename)

    # Check if cached file exists
    if os.path.exists(filepath):
        with open(filepath, "r") as file:
            cached_data = json.load(file)

    # Initialize the new array to store selected youtube links
    selected_youtube_links = []
    playlist_overview = cached_data.get('overview', [])
    playlist_name = playlist_overview["name"]
    # Loop through tracks and their youtube_links to find selected ones
    for track in cached_data.get('tracks', []):
        for youtube_link in track.get('youtube_links', []):
            if youtube_link.get('selected') == True:
                selected_youtube_links.append({
                    'track_name': track['track_name'],
                    'track_artists': ', '.join(track.get('track_artists', [])),
                    'youtube_url': youtube_link['url']
                })

    # print("Selected YouTube Links:")
    # print(selected_youtube_links)

    for youtube_video in selected_youtube_links:
        download_mp3(youtube_video, "backend/m4a_files/" + playlist_name + "-" + playlist_id)

    
    # Get the base directory of your backend folder
    BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../"))

    # Zip file with all the .m4a files in the folder
    zip_filename = f"{playlist_name}_{playlist_id}.zip"

    # Correct the path to point to backend/zipped_playlists
    zip_filepath = os.path.join(BASE_DIR, "zipped_playlists", zip_filename)

    # Ensure the zip output directory exists
    os.makedirs(os.path.join(BASE_DIR, "zipped_playlists"), exist_ok=True)

    # Define the folder for the current playlist (playlist_folder should be in backend/m4a_files)
    playlist_folder = os.path.join(BASE_DIR, "m4a_files", f"{playlist_name}-{playlist_id}")

    # Create the zip file for the current playlist
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the playlist folder to add .m4a files to the zip
        for root, dirs, files in os.walk(playlist_folder):
            for file in files:
                if file.endswith(".m4a"):
                    # Add file to zip, maintaining folder structure relative to playlist folder
                    zipf.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), playlist_folder))

    print(f"Zipped {len(selected_youtube_links)} mp3 files into {zip_filepath}")

    return zip_filepath

# Example of the /get-playlist endpoint
@mp3_blueprint.route('/download-mp3-files/<playlist_id>')
def download_mp3_files(playlist_id):
    zip_filepath = generate_mp3_files(playlist_id)
    print(f"Generated zip file path: {zip_filepath}")

    # Check if the file exists before sending it
    if os.path.exists(zip_filepath):
        return send_file(zip_filepath, as_attachment=True)
    else:
        print(f"Error: Zip file not found at {zip_filepath}")
        return jsonify({"error": "File not found"}), 404
