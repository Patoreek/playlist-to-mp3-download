<script lang="ts">
	import { apiGet, apiPost } from './../utils/apiClient.js';
    import { onMount } from 'svelte';
    import spotifyTestData from '../utils/spotifyTestData.json';
    import youtubeTestData from '../utils/youtubeTestData.json';
    import spotifyLogo from '../../src/images/icons/spotify_logo.svg';
    import youtubeLogo from '../../src/images/icons/youtube_logo.svg';
    let tracks: any[] = [];  // State to store tracks
    let isGridView: boolean = true;  // State to toggle between grid and list view
    let extendedTracks: string[] | any = [];  // State to store the extended track names
    const VITE_SERVER_URL = "http://127.0.0.1:5000"; 

  
    // Fetch data from the server
    const fetchSpotifyPlaylist = async () => {
        tracks = spotifyTestData;
        // const spotifyPlaylistId = "4UvlgqVm4gE5cyOx81JSMj";

        // const url = `${VITE_SERVER_URL}/api/spotify/get-playlist/${spotifyPlaylistId}`;
        // try {
        //     const data = await apiGet(url);  // Default method is 'GET'
        //     tracks = data.tracks || [];
        //     console.log(data.tracks);
        // } catch (error) {
        //     console.error('Error fetching playlist:', error);
        // }
    };


   // Function to fetch YouTube links
    const fetchYoutubeLinks = async () => {
        // tracks = combineYoutubeAndSpotifyData(null, null);
        // console.log(tracks);
        try {
            const pageSize = 3; 
            let offset = 0; 
            const allYoutubeLinks = [];

            // while (offset < extendedTracks.length) {
            while (offset == 0) {
                // Slice the array to get the current chunk
                const chunk = extendedTracks.slice(offset, offset + pageSize);
                console.log("C", chunk);

                const url = `${VITE_SERVER_URL}/api/youtube/get-links`;

                // Using the apiClient from the reference code
                const data = await apiPost(url, {songNames: chunk});

                if (data && data.tracks) {
                    console.log("YouTube Links Success:", data.tracks);

                    // Collect the results
                    allYoutubeLinks.push(...data.tracks);
                } else {
                    console.error("Error:", data?.message || 'Unknown error');
                }

                // Increment the offset to fetch the next chunk
                offset += pageSize;
            }

            console.log("All YouTube Links:", allYoutubeLinks);
            tracks = combineYoutubeAndSpotifyData(allYoutubeLinks, tracks);
            console.log("Updated Data:", tracks);
            return allYoutubeLinks; // Return all the fetched links if needed
        } catch (error) {
            console.error("Error fetching YouTube links:", error);
        }
    };

    const combineYoutubeAndSpotifyData = (youtubeData: any, spotifyData: any) => {
        youtubeData = youtubeTestData;
        spotifyData = spotifyTestData;

        const combinedData = spotifyData.map((spotifyTrack: any) => {
            const matchingYoutubeTrack = youtubeData.find((youtubeTrack: any) => {
                return youtubeTrack.query.id === spotifyTrack.id
            });

            return {
                ...spotifyTrack,
                youtubeVideos: matchingYoutubeTrack ? matchingYoutubeTrack.videos : [], // Add YouTube videos or empty array
            };
        });
        return combinedData;
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
            return {
                id: track.id,  // Use the track's ID
                name: `${track.track_name} - ${artistNames} - Extended`  // Create the extended name
            };
        
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
            {#if track.youtubeVideos && track.youtubeVideos.length > 0}
                <ul class="mt-4 space-y-2">
                {#each track.youtubeVideos as video}
                    <li class="flex items-center space-x-4">
                    <img src={video.thumbnails.medium.url} alt={video.title} class="w-16 h-16 object-cover rounded-md" />
                    <div>
                        <img src={youtubeLogo} alt="Youtube Logo" width="26px" height="26px"/>
                        <a href={video.url} target="_blank" class="text-sm font-semibold text-blue-500 hover:underline">
                        {video.title}
                        </a>
                    </div>
                    </li>
                {/each}
                </ul>
            {/if}
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