function drawMap(restaurants, segments) {
	// Mid-Quebec City
	let bikeMap = L.map('bikeMap').setView([46.82329245241579, -71.28679887430665], 12);

	// Credits to http://leaflet-extras.github.io/leaflet-providers/preview/index.html
	let layer = L.tileLayer('https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png', {
		maxZoom: 19,
		attribution: '&copy; <a href="http://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors, &copy; <a href="http://cartodb.com/attributions">CartoDB</a>, &copy; <a href="https://www.donneesquebec.ca">Gouvernement du Québec</a>'
	});

	bikeMap.addLayer(layer);

	for (const restaurant of restaurants) {
		let coordinates = restaurant['geometry']['coordinates'];
		let marker = L.marker([coordinates[1], coordinates[0]]).addTo(bikeMap);
		marker.bindPopup(restaurant['name']);
	}

	for (const road of segments) {
		let startPoint = road["bp1"];
		let endPoint = road["bp2"];

		let roadCoordinates = [
			[startPoint["latitude"], startPoint["longitude"]],
			[endPoint["latitude"], endPoint["longitude"]]
		];

		let line = L.polyline(roadCoordinates, { color: 'red' }).addTo(bikeMap);
		line.bindPopup(roadCoordinates[0].map(String).join(',') + "à" + roadCoordinates[1].map(String).join(','));
	}
}