<script lang="ts">
	import { onMount } from 'svelte';
    let data: any = {};

    const VITE_SERVER_URL = "http://127.0.0.1:5000"; 
    const fetchData = async () => {
        const response = await fetch(VITE_SERVER_URL + '/api/data');
        data = await response.json();
    };

    onMount(async() => {

        await fetchData();
    })
</script>

<h1>{data.message}</h1>
<p>Status: {data.status}</p>