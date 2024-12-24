<script lang="ts">
    import { onMount } from 'svelte';
  
    let tracks: any[] = [];  // State to store tracks
    let isGridView: boolean = true;  // State to toggle between grid and list view
    let extendedTracks: string[] = [];  // State to store the extended track names
    const VITE_SERVER_URL = "http://127.0.0.1:5000"; 
  
    // Fetch data from the server
    const fetchSpotifyPlaylist = async () => {
      const spotifyPlaylistId = "4UvlgqVm4gE5cyOx81JSMj";
      const response = await fetch(VITE_SERVER_URL + '/api/spotify/get-playlist/' + spotifyPlaylistId);
      const data = await response.json();
      tracks = data.tracks || [];  // Store tracks in the state
    };

   // Function to fetch YouTube links
    const fetchYoutubeLinks = async () => {
        try {
        const response = await fetch(VITE_SERVER_URL + '/api/youtube/get-links', {
            method: 'POST',
            headers: {
            'Content-Type': 'application/json',
            },
            body: JSON.stringify({ songNames: extendedTracks }), // Sending the array of songs
        });

        // Parse the response
        const data = await response.json();

        if (response.ok) {
            console.log("YouTube Links Success:", data.tracks);
        } else {
            console.error("Error:", data.message);
        }
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
  
    // Generate an array of strings in the format: "${track name} - ${Artists names} - Extended"
    const generateExtendedTracks = () => {
      extendedTracks = tracks.map(track => {
        const artistNames = track.track_artists.join(', ');
        return `${track.track_name} - ${artistNames} - Extended`;
      });
      console.log(extendedTracks);  // Log the result or use it elsewhere
    };
  </script>
  
  <h1 class="text-3xl font-bold text-center mb-6">{tracks.length ? "Spotify Playlist" : "Loading..."}</h1>
  
  {#if tracks.length > 0}
    <div class="max-w-7xl mx-auto px-4">
      <div class="mb-4 flex items-center space-x-4">
        <button 
          on:click={toggleView} 
          class="p-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 focus:outline-none">
          {isGridView ? 'Switch to List View' : 'Switch to Grid View'}
        </button>
        
        <button 
          on:click={generateExtendedTracks} 
          class="p-2 bg-green-500 text-white rounded-md hover:bg-green-600 focus:outline-none">
          Convert to Extended Tracks
        </button>
        <button 
          on:click={fetchYoutubeLinks} 
          class="p-2 bg-orange-500 text-white rounded-md hover:bg-orange-600 focus:outline-none">
          Generate Youtube links from Extended Tracks
        </button>
      </div>
      
      <ul class={isGridView ? 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6' : 'space-y-6'}>
        {#each tracks as track}
          <li class={isGridView ? 'bg-white p-4 rounded-lg shadow-md hover:shadow-xl transition-shadow' : 'flex items-center space-x-4 bg-white p-4 rounded-lg shadow-md hover:shadow-xl transition-shadow'}>
            <!-- Image on the left -->
            <img src={track.track_image} alt={track.track_name} class="w-24 h-24 object-cover rounded-md" />
            
            <!-- Data on the right -->
            <div class="flex-1">
              <a href={track.external_url} target="_blank" class="text-lg font-semibold text-blue-500 hover:underline">
                {track.track_name} - {track.track_artists.join(', ')}
              </a>
            </div>
          </li>
        {/each}
      </ul>
      
      {#if extendedTracks.length > 0}
        <div class="mt-6">
          <h2 class="text-xl font-semibold mb-4">Extended Tracks:</h2>
          <ul>
            {#each extendedTracks as track}
              <li class="text-gray-700">{track}</li>
            {/each}
          </ul>
        </div>
      {/if}
    </div>
  {:else}
    <p class="text-center text-gray-500">No tracks found or still loading...</p>
  {/if}