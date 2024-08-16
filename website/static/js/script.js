$(document).ready(function(){
    $('#routeForm').on('submit', function(event){
        event.preventDefault();
        $.ajax({
            url: '/route',
            method: 'POST',
            data: $(this).serialize(),
            success: function(response){
                $('#map').html(response.map_html);
                animateCarMovement(response.route_coords, response.speed_limits);
            }
        });
    });

    function animateCarMovement(route_coords, speed_limits) {
        // Initialize the map
        let map = L.map('map').setView(route_coords[0], 14);

        // Add tile layer
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 19,
            attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);

        // Add the route to the map
        L.polyline(route_coords, {color: 'blue'}).addTo(map);

        // Create a marker for the car
        let marker = L.marker(route_coords[0]).addTo(map);

        // Function to move the marker along the route
        let index = 0;
        function moveMarker() {
            if (index < route_coords.length) {
                marker.setLatLng(route_coords[index]);
                $('#speedValue').text(speed_limits[index].toFixed(2));
                index++;
                setTimeout(moveMarker, 500); // Adjust the speed of animation here
            }
        }

        moveMarker();
    }
});
