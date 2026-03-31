const socket = io('http://127.0.0.1:5000');

let driverLat = null;
let driverLon = null;

// ─── Get driver GPS location ───────────────────────────────
function getDriverLocation() {
    if (!navigator.geolocation) {
        showStatus(" Geolocation not supported by your browser", "error");
        return;
    }
    navigator.geolocation.getCurrentPosition(
        (pos) => {
            driverLat = pos.coords.latitude;
            driverLon = pos.coords.longitude;
            showStatus(` Driver location detected\nLat: ${driverLat.toFixed(4)}, Lon: ${driverLon.toFixed(4)}`, "success");
        },
        () => {
            showStatus(" Location permission denied — using nearest ambulance instead", "error");
        }
    );
}

// ─── Incoming emergency from backend ──────────────────────
socket.on('new_emergency', async (data) => {
    // Flash the alert box
    const alertBox = document.getElementById('alertBox');
    alertBox.style.borderColor = '#e94560';
    alertBox.innerHTML = `
        <span style="color:#e94560; font-size:1.1rem; font-weight:bold;"> EMERGENCY ALERT!</span><br><br>
        <b>Patient:</b> ${data.name}<br>
        <b>Location:</b> ${data.lat.toFixed(4)}, ${data.lon.toFixed(4)}<br><br>
        <span style="color:#aaa; font-size:0.85rem;">Processing optimal route...</span>
    `;

    showStatus(" Running A* algorithm on Chennai roads...", "");
    await processRoute(data.name, data.lat, data.lon);
});

// ─── Route ready confirmation ──────────────────────────────
socket.on('route_ready', (data) => {
    showStatus(
        ` Route Ready!\n\n` +
        ` Patient: ${data.patient}\n` +
        ` Road Distance: ${data.distance_km} km\n` +
        ` Path Nodes (A*): ${data.nodes}`,
        "success"
    );
});

// ─── Process route to patient ──────────────────────────────
async function processRoute(name, lat, lon) {
    try {
        const body = {
            name: name,
            lat: lat,
            lon: lon
        };

        const response = await fetch('/process', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });

        const data = await response.json();

        if (data.success) {
            // Reload map with cache-busting
            const mapFrame = document.getElementById('routeMap');
            mapFrame.src = 'route_map.html?t=' + Date.now();
            document.getElementById('mapMsg').style.display = 'none';
            loadAmbulances();
        } else {
            showStatus(` ${data.error}`, "error");
        }

    } catch (err) {
        showStatus(" Could not connect to server!", "error");
    }
}

// ─── Load ambulance fleet ──────────────────────────────────
async function loadAmbulances() {
    try {
        const res = await fetch('/ambulances');
        const data = await res.json();

        const list = document.getElementById('ambulanceList');
        list.innerHTML = '';

        for (const [id, amb] of Object.entries(data)) {
            const div = document.createElement('div');
            div.className = 'ambulance-item';
            div.innerHTML = `
                <span> ${id}</span>
                <span class="${amb.status}">${amb.status.toUpperCase()}</span>
            `;
            list.appendChild(div);
        }
    } catch (err) {
        document.getElementById('ambulanceList').innerText = " Could not load ambulances";
    }
}

// ─── Reset all ambulances ──────────────────────────────────
async function resetAmbulances() {
    await fetch('/reset', { method: 'POST' });
    loadAmbulances();
    showStatus(" All ambulances reset to available!", "success");
    document.getElementById('alertBox').innerHTML = "Waiting for emergency...";
    document.getElementById('alertBox').style.borderColor = '';
    document.getElementById('routeMap').src = '';
    document.getElementById('mapMsg').style.display = 'block';
}

// ─── Show status message ───────────────────────────────────
function showStatus(message, type) {
    const box = document.getElementById('status');
    box.innerText = message;
    box.className = `status-box ${type}`;
}

// ─── On page load ──────────────────────────────────────────
window.onload = () => {
    getDriverLocation();
    loadAmbulances();
};