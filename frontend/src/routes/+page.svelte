<script lang="ts">
	import { apiGet, apiPost, apiPut } from './../utils/apiClient.js';
    import { onMount } from 'svelte';

    import spotifyLogo from '../../src/images/icons/spotify_logo.svg';
    import youtubeLogo from '../../src/images/icons/youtube_logo.svg';
    import { Checkbox } from "$lib/components/ui/checkbox";
    import { Button } from "$lib/components/ui/button";
    import { Toaster } from "$lib/components/ui/sonner";
    import { toast } from "svelte-sonner";

    let tracks: any[] = [];  // State to store tracks
    let playlistOverview: any[] = [];
    let isGridView: boolean = true;  // State to toggle between grid and list view
    let extendedTracks: string[] | any = [];  // State to store the extended track names
    const VITE_SERVER_URL = "http://127.0.0.1:5000"; 

    // const spotifyPlaylistId = "4UvlgqVm4gE5cyOx81JSMj";
    const spotifyPlaylistId = "4QS0wutGTV59WwcXaI4pbn";
  
    // Fetch data from the server
    const fetchSpotifyPlaylist = async () => {
        // tracks = spotifyTestData;
        const url = `${VITE_SERVER_URL}/api/spotify/get-playlist/${spotifyPlaylistId}`;
        try {
            const data = await apiGet(url);  // Default method is 'GET'
            tracks = data.playlist.tracks || [];
            playlistOverview = data.playlist.overview || [];
            console.log(data.playlist.tracks);
        } catch (error) {
            console.error('Error fetching playlist:', error);
        }
    };


   // Function to fetch YouTube links
    const fetchYoutubeLinks = async () => {
        try {
            const pageSize = 3; 
            let offset = 0; 
            const allYoutubeLinks = [];
            const offsetLimit = 15;
            generateExtendedTracks();
            while (offset < extendedTracks.length ) {
                const url = `${VITE_SERVER_URL}/api/youtube/get-links`;
                // Using the apiClient from the reference code
                const data = await apiPost(url, {
                  playlistId: spotifyPlaylistId,
                  offset: offset,
                  pageSize: pageSize
                });
                console.log("D:", data)
                if (data && data.playlist_data.tracks) {
                    console.log("YouTube Links Success:", data.playlist_data.tracks);
                    tracks = data.playlist_data.tracks
                } else {
                    console.error("Error:", data?.message || 'Unknown error');
                }

                // Increment the offset to fetch the next chunk
                offset += 1;

                if (data.apiStatus.value !== true) {
                  if (data.apiStatus.value === "restricted"){
                    toast.error(data.apiStatus.message);
                  } else {
                    toast.warning(data.apiStatus.message);
                  }
                } else {
                  // toast.success("Youtube Links generated!");
                }
            }

            console.log("Updated Data:", tracks);
            toast.success("Tracks data updated!");
            return tracks; // Return all the fetched links if needed
        } catch (error) {
            console.error("Error fetching YouTube links:", error);
        }
    };

  
    onMount(async () => {
      await fetchSpotifyPlaylist();
    });
  
    // Toggle the view between grid and list
    const toggleView = () => {
      isGridView = !isGridView;
    };
  
    const handleVideoSelection = async (track, selectedVideo) => {
      // Set all videos' selected property to false except the selected one
      try {
        track.youtube_links.forEach(video => {
          video.selected = (video === selectedVideo);
        });
        const url = `${VITE_SERVER_URL}/api/youtube/update-selected-link`;
        const data = await apiPut(url, {
            playlistId: spotifyPlaylistId,
            track: track,
            selectedVideo: selectedVideo
        });
        console.log(data);
        if (data && data.status === "success") {
          toast.success(data.message);
        } else {
          toast.error(data.message);
        }
      } catch (error) {
        console.error('Error: ', error);
      }

      //TODO: Create an update on the backend store file for a particular youtube link
    }

    // Generate an array of strings in the format: "${track name} - ${Artists names} - Extended"
    const generateExtendedTracks = () => {
        extendedTracks = tracks.map(track => {
            const artistNames = track.track_artists.join(', ');
            return {
                id: track.id,  // Use the track's ID
                name: `${track.track_name} - ${artistNames} - Extended`  // Create the extended name
            };
        
        });
    };

    const downloadMp3FromYoutube = () => {
      console.log("Downloading mp3s...");
    }
  </script>
  
  <Toaster richColors />
  <h1 class="text-3xl font-bold text-center mb-6">{tracks.length ? "Spotify Playlist" : "Loading..."}</h1>
  {#if tracks.length > 0}
    <div class="max-w-7xl mx-auto px-4">
      <div class="mb-4 flex items-center space-x-4">
        <Button 
          on:click={toggleView} 
          class="p-2 bg-blue-500 text-white hover:bg-blue-600 focus:outline-none">
          {isGridView ? 'Switch to List View' : 'Switch to Grid View'}
        </Button>
        <Button 
          on:click={fetchYoutubeLinks} 
          class="p-2 bg-orange-500 text-white hover:bg-orange-600 focus:outline-none">
          Generate Youtube links from Extended Tracks
        </Button>
        <Button 
          on:click={downloadMp3FromYoutube} 
          class="p-2 bg-pink-500 text-white hover:bg-pink-600 focus:outline-none">
          Download .mp3 files
        </Button>
        <p>Tracks: {tracks.length}</p>
      </div>
      <div class="max-w-7xl mx-auto px-4 flex gap-4 py-5">
        <img src={playlistOverview.images[0].url} alt={playlistOverview.name} class="w-16 h-16 object-cover rounded-md" />
        <div class="">
          <h1><a href={playlistOverview.external_urls.spotify}>{playlistOverview.name}</a></h1>
          <h1><a href={playlistOverview.owner.external_urls.spotify}>{playlistOverview.owner.display_name}</a></h1>
        </div>
      </div>
      <ul class={isGridView ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6' : 'space-y-6'}>
        {#each tracks as track}
        <li class={isGridView ? 'bg-white border border-gray-200 p-4 rounded-lg shadow-md hover:shadow-xl transition-shadow' : 'flex items-center space-x-4 bg-white p-4 rounded-lg shadow-md hover:shadow-xl transition-shadow'}>
          <div class="flex gap-4">
               <!-- Image on the left -->
               <img src={track.track_image} alt={track.track_name} class="w-24 h-24 object-cover rounded-md" />
               
               <!-- Data on the right -->
              <div class="flex-1 flex flex-col justify-between">
                 <img src={spotifyLogo} alt="Spotify Logo" width="26px" height="26px"/>
                   <a href={track.external_url} target="_blank" class="flex gap-2 text-lg font-semibold text-blue-500 hover:underline">
                    {track.track_name} - {track.track_artists.join(', ')}
                    </a>
              </div>
          </div>

          <!-- YouTube videos list -->
          {#if track.youtube_links && track.youtube_links.length > 0}
              <ul class="mt-4 space-y-2">
              {#each track.youtube_links as video}
                  <li class="flex items-center space-x-4">
                  <img src={video.thumbnails.medium.url} alt={video.title} class="w-16 h-16 object-cover rounded-md" />
                  <div>
                      <img src={youtubeLogo} alt="Youtube Logo" width="26px" height="26px"/>
                      <a href={video.url} target="_blank" class="text-sm font-semibold text-blue-500 hover:underline">
                      {video.title}
                      </a>
                      <!-- Checkbox for video selection -->
                      <div class="flex items-center mt-2">
                        <Checkbox
                          bind:checked={video.selected}
                          onCheckedChange={() => handleVideoSelection(track, video)}
                        />
                      </div>
                  </div>
                  </li>
              {/each}
              </ul>
          {/if}
        </li>
        {/each}
      </ul>
    </div>
  {:else}
    <p class="text-center text-gray-500">No tracks found or still loading...</p>
  {/if}