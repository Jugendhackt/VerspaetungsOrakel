<script lang="ts">
	const BACKEND_SERVER_URL: string = '127.0.0.1:5000';

	interface Response {
		average_delay: number;
		arrival: string;
		departure: string;
		last_delays: Delay[];
	}

	interface Delay {
		delay: number;
		date: string;
	}

	let stop_data_promise: Promise<any>;
	let station_name: string = '';
	let train_number: number = 0;

	let prev_station_names_start: string[] = [];
	let stations: Set<string> = new Set();

	async function get_stations() {
		if (station_name.length < 2) return;
		const station_name_start = station_name.slice(0, 2);
		if (prev_station_names_start.includes(station_name_start)) return;
		prev_station_names_start.push(station_name_start);

		const response = await fetch(`http://${BACKEND_SERVER_URL}/api/stations?name=${station_name}`);
		const data = await response.json();
		for (let item of data) {
			stations.add(item);
		}
		stations = stations;
	}

	async function get_stop_data(): Promise<Response> {
		const response = await fetch(
			`http://${BACKEND_SERVER_URL}/api/submit?train=${train_number}&station=${station_name}`
		);
		const data: Response = await response.json();
		return data;
	}
</script>

<svelte:head>
	<title>VerspätungsOrakel</title>
</svelte:head>

<main class="container">
	<article>
		<h1>VerspätungsOrakel</h1>

		<form>
			<div class="grid">
				<label for="station">
					Bahnhof
					<input
						bind:value={station_name}
						type="text"
						id="staion"
						placeholder="Bahnhof"
						list="station-names"
						on:input={get_stations}
						required
					/>
					<datalist id="station-names">
						{#each stations as station}
							<option>{station}</option>
						{/each}
					</datalist>
				</label>
				<label for="train-number">
					Zugnummer
					<input
						bind:value={train_number}
						type="number"
						id="train-number"
						placeholder="Zugnummer"
						required
					/>
				</label>
			</div>
			<button on:click={() => (stop_data_promise = get_stop_data())}>Analysieren</button>
		</form>

		{#if stop_data_promise}
			{#await stop_data_promise}
				<h6 aria-busy="true">Werte Daten aus ...</h6>
			{:then data}
				<p>
					<strong>Ankunft:</strong>
					{data.arrival}
				</p>
				<p>
					<strong>Abfahrt:</strong>
					{data.departure}
				</p>
				<p>
					<strong>Durchschnittliche Verspätung:</strong>
					{data.average_delay} min.
				</p>
			{:catch error}
				<h6>{error}</h6>
			{/await}
		{/if}
	</article>
</main>

<footer>
	<a
		class="hover:opacity-75 github-icon"
		href="https://github.com/Jugendhackt/verspaetungsorakel"
		target="_blank"
	>
		<img src="./github_logo.svg" alt="GitHub" loading="lazy" />
	</a>
</footer>

<style>
	.github-icon {
		position: fixed;
		bottom: 1rem;
		right: 1rem;
		height: 2.5rem;
		width: 2.5rem;
	}
	.github-icon:hover {
		opacity: 0.75;
	}
</style>
