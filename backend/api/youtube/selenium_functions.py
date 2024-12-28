from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
import time
import json
import os
from datetime import datetime, timedelta

def get_youtube_results_selenium(playlistId, offset, pageSize):
    max_results = 3
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

    # Initialize WebDriver with headless mode
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")  # Use for Chrome 109+, use "--headless" for older versions
    chrome_options.add_argument("--disable-gpu")  # Optional, might not be needed with newer Chrome
    chrome_options.add_argument("--window-size=1920x1080")  # Helps with rendering consistency
    chrome_options.add_argument("--no-sandbox")  # Optional, if running on Linux without graphical interface
    chrome_options.add_argument("--disable-dev-shm-usage")  # Optional, for memory efficiency

    driver = webdriver.Chrome(options=chrome_options)  # Use the configured options
    driver.get("https://www.youtube.com")

    for track in tracks:
        # Skip tracks that already have YouTube links
        if len(track["youtube_links"]) >= max_results:
            print(f"Skipping track: {track['track_name']} (YouTube links already present)")
            continue
        else:
            print(f"Getting Youtube links for {track['track_name']}")

        # Query YouTube API
        query = f"{track['track_name']} {' '.join(track['track_artists'])} - Extended"

        # Find the search box, clear it, and perform the search
        search_box = driver.find_element(By.NAME, "search_query")
        search_box.clear()  # Clear any existing query
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)

        # Wait for the results to load, ensure the first video appears
        # WebDriverWait(driver, 10).until(
        #     EC.presence_of_element_located((By.CSS_SELECTOR, "ytd-video-renderer"))
        # )

        # Sleep for an additional timeout to allow YouTube to fully load the search results
        time.sleep(2)  # Adjust this time as needed (e.g., 2-5 seconds)

        # Retrieve video details
        video_elements = driver.find_elements(By.CSS_SELECTOR, "ytd-video-renderer")[:max_results]
        top_videos = []
        for index, video in enumerate(video_elements):
            print(f"Video No.{index}")
            title_element = video.find_element(By.CSS_SELECTOR, "a#video-title")
            title = title_element.get_attribute("title")
            url = title_element.get_attribute("href")

            try:
                # Attempt to find the primary thumbnail
                thumbnail_element = video.find_element(By.CSS_SELECTOR, "ytd-thumbnail img")
                thumbnail_url = thumbnail_element.get_attribute("src")
                print("Primary thumbnail URL:", thumbnail_url)
            except Exception as e:
                print("Failed to find primary thumbnail:", e)
                thumbnail_url = "N/A"

            top_videos.append({
                "title": title,
                "url": url,
                "thumbnails": {
                    "default": {
                        "url": thumbnail_url,
                        "width": 120,
                        "height": 120
                    },
                    "medium": "N/A",
                    "high": "N/A"
                },
                "updated_at": datetime.now().isoformat(),
                "selected": index == 0
            })

        # Append YouTube links to the track (after gathering all results)
        track["youtube_links"] = top_videos

        # Sleep between track queries to allow time for YouTube to fully load the next results
        time.sleep(2)  # You can adjust this based on your testing

        # Save updated playlist JSON after all tracks are processed
        with open(filepath, "w") as file:
            json.dump(playlist_data, file, indent=4)
            print(f"{track['track_name']} YouTube links updated in JSON.")

    print("YouTube links updated in playlist JSON.")

    # Close the browser
    driver.quit()
    return {"apiStatus": "Test", "playlist_data": playlist_data}


if __name__ == "__main__":
    playlistId = "your_playlist_id"
    offset = 0
    pageSize = 3
    results = get_youtube_results_selenium(playlistId, offset, pageSize)

    # Display the results
    for track in results["playlist_data"]["tracks"]:
        print(f"Track: {track['track_name']}")
        for youtube_link in track['youtube_links']:
            print(f"   Title: {youtube_link['title']}")
            print(f"   URL: {youtube_link['url']}")
            print(f"   Thumbnail: {youtube_link['thumbnails']['default']['url']}")
            print(f"   Duration: {youtube_link.get('duration', 'N/A')}")