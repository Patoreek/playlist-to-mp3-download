<script lang="ts">
	import { apiGet, apiPost, apiPut } from './../utils/apiClient.js';
    import { onMount, onDestroy } from 'svelte';

    import spotifyLogo from '../../src/images/icons/spotify_logo.svg';
    import youtubeLogo from '../../src/images/icons/youtube_logo.svg';
    import { Checkbox } from "$lib/components/ui/checkbox";
    import { Progress } from "$lib/components/ui/progress";
    import { Button } from "$lib/components/ui/button";
    import { Toaster } from "$lib/components/ui/sonner";
    import { toast } from "svelte-sonner";

    let tracks: any[] = [];  // State to store tracks
    let playlistOverview: any[] = [];
    let quotaLimits: any = {};
    let zipFileUrl = null;  // Variable to store the file URL
    let isGridView: boolean = true;  // State to toggle between grid and list view
    let extendedTracks: string[] | any = [];  // State to store the extended track names
    const VITE_SERVER_URL = "http://127.0.0.1:5000"; 

    // const spotifyPlaylistId = "4QS0wutGTV59WwcXaI4pbn"; // Augh Playlist
    // const spotifyPlaylistId = "4UvlgqVm4gE5cyOx81JSMj"; // House Classics
    // const spotifyPlaylistId = "4zndP2wvkpiai68dQQuGUu"; // Techno
    // const spotifyPlaylistId = "5H2r42I3k1ME2n8rCM1b40"; // Deep Beats
    const spotifyPlaylistId = "4Pgk83d5LW0xbR1ivSbsC8"; // EDM
  
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
            let apiStatus = null;
            while (offset < extendedTracks.length ) {
                const url = `${VITE_SERVER_URL}/api/youtube/get-links`;
                // Using the apiClient from the reference code
                const data = await apiPost(url, {
                  playlistId: spotifyPlaylistId,
                  offset: offset,
                  pageSize: pageSize
                });
                console.log("D:", data)
                
                if (data.apiStatus === "quotaExceeded"){
                  apiStatus = data.apiStatus;
                  break;
                } else if (data.apiStatus != "success") {
                  toast.warning(data.apiStatus.message);
                }

                if (data && data.playlist_data.tracks) {
                    console.log("YouTube Links Success:", data.playlist_data.tracks);
                    tracks = data.playlist_data.tracks
                } else {
                    console.error("Error:", data?.message || 'Unknown error');
                }
                await fetchQuotaLimitsData();

                // Increment the offset to fetch the next chunk
                offset += 1;

            }

            console.log("Updated Data:", tracks);
            if (apiStatus === "quotaExceeded"){
              toast.error("Youtube API Quota exceeded for the day!");
            } else {
              toast.success("Tracks data updated!");
            }
            return tracks; // Return all the fetched links if needed
        } catch (error) {
            console.error("Error fetching YouTube links:", error);
        }
    };

  
    onMount(async () => {
      await fetchSpotifyPlaylist();
      await fetchQuotaLimitsData();
    });

    onDestroy(() => {
      if (zipFileUrl) {
        URL.revokeObjectURL(zipFileUrl); // Release memory
      }
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

    const fetchQuotaLimitsData = async () => {
      // Set all videos' selected property to false except the selected one
      try {
        const url = `${VITE_SERVER_URL}/api/youtube/get-current-quota-limit`;
        const data = await apiGet(url);
        console.log(data);
        quotaLimits = data.data;
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

    const downloadMp3FromYoutube = async () => {
      console.log("Downloading mp3s...");
      try {
        const url = `${VITE_SERVER_URL}/api/mp3/download-mp3-files/${spotifyPlaylistId}`;
        const response = await fetch(url);
        
        if (!response.ok) {
          throw new Error('Failed to fetch the zip file');
        }

        const blob = await response.blob();
        zipFileUrl = URL.createObjectURL(blob);  // Store the file URL in the variable

        console.log("Zip file is ready for download!");
        toast.success(".zip file is ready for download!");
      } catch (error) {
        console.error('Error: ', error);
      }
    }

    const handleDownload = () => {
      if (zipFileUrl) {
        console.log("Downloading file:", zipFileUrl);
        const link = document.createElement("a");
        link.href = zipFileUrl;
        link.download = `${playlistOverview.name}_playlist.zip`;
        document.body.appendChild(link); // Append link to body
        link.click(); // Trigger download
        document.body.removeChild(link); // Clean up
        URL.revokeObjectURL(zipFileUrl); // Release memory
        zipFileUrl = null; // Reset blob URL
      } else {
        console.log('No zip file ready for download');
      }
    };

    function getResetTime() {
      const refreshedDate = new Date(quotaLimits.refreshed_on);
      refreshedDate.setHours(refreshedDate.getHours() + 24); // Adds 24 hours
      return refreshedDate.toLocaleString(); // Formats the date to a readable string
    }

    $: quotaPercentage = quotaLimits.daily_quota_limit && quotaLimits.quota_used
    ? (quotaLimits.quota_used / quotaLimits.daily_quota_limit) * 100
    : 0;
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
        {#if zipFileUrl != null}
        <Button 
          on:click={handleDownload} 
          class="p-2 bg-pink-500 text-white hover:bg-pink-600 focus:outline-none">
          Download {playlistOverview.name}_playlist.zip
        </Button>
        {/if}
        <p>Tracks: {tracks.length}</p>
        <div class="max-w-lg mx-auto bg-white shadow-lg rounded-lg p-6">
          <Progress value={quotaPercentage} class="w-full mb-4 h-4 rounded-full bg-gray-200" />
        
          <div class="">
            <p class="text-lg font-semibold text-gray-700">
              <span class="text-gray-600">Used:</span> {quotaLimits.quota_used} / {quotaLimits.daily_quota_limit}
            </p>
            <p class="text-sm text-gray-500">
              <span class="text-gray-600">Resets on:</span> {quotaLimits.refreshed_on ? getResetTime() : 'N/A'}
            </p>
          </div>
       
        </div>
       
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